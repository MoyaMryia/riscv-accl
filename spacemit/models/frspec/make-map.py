from ast import literal_eval
from collections import Counter
from hashlib import sha256
from pathlib import Path
from struct import pack

here = Path(__file__).resolve().parent
ids = literal_eval((here / 'corpus-token-ids.txt').read_text())
counts = Counter(ids)
ranked = [token for token, _ in counts.most_common()]
ranked.extend(token for token in range(248000, 248320) if token not in counts)
seen = set(ranked)
ranked.extend(token for token in range(248320) if token not in seen)
ranked = ranked[:32768]
assert len(ranked) == len(set(ranked)) == 32768
payload = pack('<32768q', *ranked)
(here / 'd2t-map32k.bin').write_bytes(payload)
print(sha256(payload).hexdigest())
