#!/usr/bin/env python3
"""核对统一源码、独立候选共用文件和原发布基础设施。"""
import hashlib,json,os
from pathlib import Path
r=Path(__file__).resolve().parents[4]
assert os.environ.get('TMUX')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
source=r/'lab/integrated-20261013/source'
pkg=r/'spacemit/release-candidate'
release=json.loads((r/'spacemit/release/manifest.json').read_text())
combined=json.loads((r/'spacemit/experiments/local-candidate-patches/combined-r1.manifest.json').read_text())
checks={}
checks['infrastructure']={n:sha(source/n) for n in release['patched_source_sha256']}
assert checks['infrastructure']==release['patched_source_sha256']
checks['combined']={n:sha(source/n) for n in combined['files_sha256']}
assert checks['combined']==combined['files_sha256']
checks['patch_sha256']=sha(pkg/'unified.patch')
assert checks['patch_sha256']==combined['patch_sha256']
checks['C1']={}
c1=json.loads((r/'spacemit/experiments/local-candidate-patches/C.manifest.json').read_text())
for n in ('src/models/qwen35.cpp','src/models/delta-net-base.cpp','src/models/spine-k1-ssm-conv.h','ggml/src/ggml-cpu/spine-k1-ssm-kernel.h'):
 checks['C1'][n]=sha(source/n);assert checks['C1'][n]==c1['files_sha256'][n]
for candidate,name in [('C2-r2','ggml/src/ggml-cpu/spine-k1-gdn-prefill-r2.h'),('B1-r2','ggml/src/ggml-cpu/spine-k1-local-attention.h')]:
 manifest=json.loads((r/f'spacemit/experiments/local-candidate-patches/{candidate}.manifest.json').read_text())
 checks[candidate]={name:sha(source/name)};assert checks[candidate][name]==manifest['files_sha256'][name]
checks['fixture_revision']='combined-fixture-r5-linked-cpu'
checks['fixtures']={}
for new,old in [('test-state.cpp','test-combined-state.cpp'),('test-gdn.cpp','test-gdn-r2.cpp')]:
 a=sha(pkg/'tests'/new);b=sha(r/'lab/k1-combined-fixture-r5-20261011-122000-work/payload/C'/old)
 if new=='test-state.cpp':
  original=(r/'lab/k1-combined-fixture-r5-20261011-122000-work/payload/C'/old).read_text()
  revised=original.replace('    ggml_backend_load_all(); llama_backend_init();','    // Use the linked CPU backend. Do not load another backend from the executable directory.\n    llama_backend_init();')
  assert (pkg/'tests'/new).read_text()==revised
 else: assert a==b
 checks['fixtures'][new]={'current':a,'frozen_r5':b}
checks['status']='pass'
(Path(__file__).parent/'source-audit.json').write_text(json.dumps(checks,indent=2)+'\n')
print('PASS: unified source, infrastructure, shared candidate files, and revised fixtures')
