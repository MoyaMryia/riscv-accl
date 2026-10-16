"""整理完整归档证据与 Git 文本入口。"""
from pathlib import Path
import shutil,json
root=Path(__file__).resolve().parent
stage=root/'release-evidence';assert not stage.exists()
shutil.copytree(root/'board',stage,ignore=shutil.ignore_patterns('bin','__pycache__','*.pyc'))
for name in ('search-attempt1','report-snapshot-20261012'):
 shutil.copytree(root/name,stage/name)
local=stage/'local-checks';local.mkdir()
for p in root.iterdir():
 if p.is_file() and (p.suffix in ('.py','.sh','.json','.log','.md','.cpp') or p.name.endswith('exit-status')):
  if p.name!='CONTINUATION.md':shutil.copy2(p,local/p.name)
for p in root.glob('*verification.json'):shutil.copy2(p,stage/p.name)
shutil.copy2(root/'final-package-receipt.json',stage/'final-package-receipt.json')
shutil.copytree(Path('spacemit/bench/final-default'),stage/'verification-tools',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for name in ('delivery','delivery-r2'):
 shutil.copytree(root/name/'package',stage/'failed-packages'/name,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
shutil.copytree(root/'selection',stage/'selection')
raw=Path('spacemit/reports/raw/k1-final-default-20261014-r3');assert not raw.exists()
raw.mkdir(parents=True)
for p in stage.rglob('*'):
 if not p.is_file() or p.is_symlink() or p.suffix=='.data' or p.name=='threads.json' or 'report-snapshot-20261012' in p.parts:continue
 if p.suffix=='.pdf':continue
 dest=raw/p.relative_to(stage);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
(raw/'ARCHIVE.md').write_text('''# 最终默认构建的文本证据入口

已验证：完整证据已在本地通过原始收据核验。
本目录保存原始文本记录和收据，不包含大型 `.data` 转储、`threads.json` 采样及生产二进制。
收据中的路径仍表示完整证据文件，不能仅凭此文本视图完成严格全工件复核。
完整证据在 `lab/final-default-20261013/release/k1-final-20261013-r3.tar.gz` 的 `evidence/` 中。
归档还包含全部源码、同次生产构建、依赖说明与固定默认启动器。
归档外部 SHA-256 与复核结果在交付报告中记录。
旧原始记录没有改写。
''')
print(json.dumps(dict(status='staged',evidence=str(stage),text_evidence=str(raw))))
