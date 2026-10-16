"""保留实测策略，并为单槽默认修复建立新交付版本。"""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
original = root / 'selection/selected-default.json'
output = root / 'selection/selected-default-r3.json'
assert not output.exists()
data = json.loads(original.read_text())
assert data['search_converged']
assert data['config'] == dict(mask=3, threads=4, ubatch=32)
data['supersedes'] = 'k1-final-20261013-r2'
data['version'] = 'k1-final-20261013-r3'
data['selection_policy_sha256'] = hashlib.sha256(original.read_bytes()).hexdigest()
output.write_text(json.dumps(data, indent=2) + '\n')
