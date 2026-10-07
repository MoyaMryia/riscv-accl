import importlib.util,json,os,sys,traceback
from pathlib import Path
p=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location("audit",p/"k1-decode-audit.py"); a=importlib.util.module_from_spec(s); s.loader.exec_module(a)
run=a.Run(p); run.server=next(Path(x) for x in run.expected["artifacts_sha256"] if x.endswith("/llama-server"))
old=Path("/home/moyamryia/Projects/riscv-accl-bench-2026-09-27/k1-decode-audit-20261007-070430")
routing=json.loads((old/"routing-provenance.json").read_text()); provenance=json.loads((old/"provenance.json").read_text())
lib=old/"lib/libggml-cpu.so.0.16.0"
assert a.fast.digest(lib)==provenance["candidate_library_sha256"]
run.base_env=dict(os.environ,**routing["runtime"],SPINE_K1_GEMM_ROUTE="3",SPINE_GEMM_AUDIT="0")
run.env=dict(os.environ,LD_LIBRARY_PATH=str(lib.parent)+":"+run.expected["runtime"]["LD_LIBRARY_PATH"],SPINE_FA_WIDE_TILE="1",SPINE_FA_K1_LAYOUT="0",SPINE_K1_GEMM_ROUTE="3")
try:
 control,cpu=run.request("2B",32,False)
 candidate,counters=run.request("2B",32,True)
 assert all(control[k]==candidate[k] for k in ("prompt_ids","token_ids","text"))
 (p/"probe-summary.json").write_text(json.dumps(dict(status="passed",exact_identity=True,samples=cpu["samples"],clock=cpu["perf_clockid"],window=cpu["sample_window_verification"],prefill_records=counters["prefill"]["records"],decode_records=counters["decode"]["records"],pairs=counters["ffn_pairs"]),indent=2)+"\n")
except BaseException as e:
 (p/"probe-summary.json").write_text(json.dumps(dict(status="failed",reason=str(e)))+"\n"); raise
