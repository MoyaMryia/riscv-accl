from pathlib import Path
import json,subprocess
base=Path("/home/moyamryia/Projects/riscv-accl-bench-2026-09-27")
print(subprocess.run(["tmux","list-sessions"],capture_output=True,text=True).stdout)
for name in ("k1-local-candidates-C-repair2-20261008-190930","k1-local-candidates-C1-repeat-20261008-202900"):
 r=base/name;print(name,(r/"phase").read_text().strip())
 s=json.loads((r/"summary.json").read_text());print("status",s["status"])
 for arm,v in s.get("arms",{}).items():print(arm,v["status"],v.get("error"))
 if (r/"exit-status").exists():print("exit",(r/"exit-status").read_text())
 for p in r.glob("*/result.json"):
  if p.parent.name=="C1-vs-C0":continue
  s=json.loads(p.read_text());print(p.parent.name,s["status"])
  for row in s["comparisons"]:
   if row["tokens"]==2048 or s["status"]!="running":print(row["model"],row["tokens"],row["outputs"],row["passed"],{k:{x:v[x] for x in ("reduction_pct","control_range_pct","advance","clear_regression")} for k,v in row["metrics"].items()})
 for p in r.glob("*failure.txt"):print(p.name,p.read_text()[-1500:])
 logs=sorted(r.glob("**/*.server.log"),key=lambda p:p.stat().st_mtime)
 if logs:
  p=logs[-1];print("latest",p.relative_to(r));print("\n".join(p.read_text().splitlines()[-3:]))
