# MTP divergence target-logit diagnostic

> Dated campaign snapshot. Measurements apply to the stated workload and date.
> Queued/running statements below are historical; use the
> [current guide](../DOCS.md) and the [experiments index](README.md) for later results and current status.

The fixed C++ prompt produced repeatable direct/MTP token-ID differences at generated index 179 for 2B and 303 for 4B. The [diagnostic patch](2026-09-27-spec-logits-trace.patch) adds `SPINE_TRACE_LOGITS_BEGIN` and `SPINE_TRACE_LOGITS_END` to print the target model's raw top-two logits at selected generated-token indices in direct sampling and speculative verification. It does not sample or alter logits. This permits inspection of the argmax margin where output first changes.

The [serialized board script](../reports/raw/2026-09-25-lifecycle/run-spec-logits-trace.sh)
completed the four traced requests after restart. Each reproduced its saved
uninstrumented token sequence. The traced source was removed and the original
server rebuilt. Logs are archived in persistent `reports/raw/2026-09-25-lifecycle/`
storage; the old temporary-board queue is no longer active.

The [completed analysis](../reports/2026-09-27-resumed-measures.md#target-logit-trace)
found the same top-two candidates in opposite order at the first mismatch.
This supports numerical sensitivity but does not isolate the responsible
kernel or fix MTP long-code identity.
