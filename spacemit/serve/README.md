# Reuse a document prefix for follow-up questions

`llama-server` can retain a prompt prefix in a live slot. The client here sends the same system instruction and document for every question, appends the changing question last, and requests `cache_prompt: true` on `/v1/chat/completions`. It pins requests to slot 0 of a single-slot server. The first question still prefills the document; later questions can reuse the common prefix. No model weights or document contents are stored in this repository.

## Start the board server

On MUSE-Pi-Pro, use the integrated build with optional RVV patch 0009. From this repository on the workstation, copy the three scripts to the board:

```bash
ssh musepipro-wg 'mkdir -p ~/Projects/riscv-accl-bench-2026-09-27/serve'
scp spacemit/serve/cached-document-chat.py spacemit/serve/*.sh \
  musepipro-wg:Projects/riscv-accl-bench-2026-09-27/serve/
```

The launch script defaults to the tested 2B `-dv64k` GGUF and 8,192 context tokens. It sets the SpaceMiT runtime paths and `SPINE_FA_WIDE_TILE=1`, uses direct decoding, and binds to loopback. On the board, run:

```bash
cd ~/Projects/riscv-accl-bench-2026-09-27/serve
CTX_SIZE=8192 ./run-cached-server-board.sh
```

Or, to keep it running after disconnecting:

```bash
tmux new-session -d -s cached-document 'cd ~/Projects/riscv-accl-bench-2026-09-27/serve && CTX_SIZE=8192 ./run-cached-server-board.sh > ~/cached-document-server.log 2>&1'
```

Set `MODEL_PATH` to the 4B GGUF and a matching `CTX_SIZE` to change models or document length. Keep this server dedicated to one document conversation: other requests to the same slot can evict or alter its cached prefix. Restarting the server also clears it.

## Ask questions

Run the client on the board with a board-local document, or use an SSH tunnel (`ssh -N -L 18085:127.0.0.1:18085 musepipro-wg`) and run the client on your machine. The document is read once at startup, so repeated questions see the same bytes. Keep the client and server running for follow-ups.

```bash
python3 spacemit/serve/cached-document-chat.py \
  --document /absolute/path/to/document.md --ctx-size 8192 --max-tokens 512
```

Enter questions interactively. For a scripted run, repeat `--question`; add `--output /path/to/new-log.jsonl` to save answers and latencies. The client uses the server's chat token-count endpoint and refuses a request if prompt plus maximum output exceeds `--ctx-size`. Pass the same context size used to launch the server. The optional log contains document hashes and full questions and answers, so choose its location accordingly.

The answer streams to stdout. Prompt length, time to first answer text, and total time go to stderr. The client sets temperature 0 and disables the Qwen3.5 thinking template. Token-by-token identity is not guaranteed when a warm cache changes batching: in the prior 2B/16k changed-question test, the first difference appeared at answer token 5, although one blinded MiMo judge rated the warm answer higher. Review important answers against the document.

## Reproduce a short smoke test

On the board, `smoke-cached-document-board.sh` builds a public 8,000-character excerpt of the server README, asks two different questions, and checks that the second first-token latency is under one-quarter of the cold one. It writes `result.jsonl`, `client.log`, and `server.log` under `~/Projects/riscv-accl-bench-2026-09-27/cached-document-smoke`; set `RUN_DIR` to a fresh path for another run. Run it in `tmux` if you want to disconnect.

In the 2B board smoke on 2026-09-30, the public excerpt produced 2,605/2,606 input tokens. The first answer started after 120.00 s; the changed-question answer started after 2.54 s (47.2× shorter). The server log reported 33 prompt tokens evaluated for the second request, and both answers completed with `stop`. This measures latency and cache reuse for one document, not answer quality across tasks.

The longer 2B/4B changed-question measurements and their quality limits are in the [shared-document cache report](../reports/2026-09-29-shared-document-cache.md).
