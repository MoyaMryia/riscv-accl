"""核验本地搜索收据，并重算冻结的阶段选择。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
from selection import choose


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text())


def receipts(root):
    pins = read(root / 'receipts.json')
    for name, value in pins.items():
        if sha(root / name) != value:
            raise ValueError('evidence differs: ' + str(root / name))
    return len(pins)


def verify(board, policy):
    if not os.environ.get('TMUX'):
        raise ValueError('run the check in tmux')
    root = board / 'search-r2'
    counts = dict(search=receipts(root), native=receipts(board / 'native-check'))
    summary = read(root / 'summary.json')
    selected = read(root / 'selected-default.json')
    assert summary['status'] == 'pass' and summary['search_converged']
    assert selected['search_converged'] and summary['selected'] == selected['config']
    assert sha(policy) == sha(root / 'selected-default.json')
    identity = read(root / 'identity.json')['inputs']
    tools = board / 'tools-r2'
    actual = {p.name: sha(p) for p in tools.iterdir() if p.is_file()}
    assert actual == identity['code']
    rows = {p.parent.name: read(p) for p in sorted(root.glob('*/result.json'))}
    assert len(rows) == 104 and all(row['status'] == 'pass' for row in rows.values())
    assert set(rows) == set(summary['completed'])
    masks = [row for name, row in rows.items() if name.startswith('masks-c0-')]
    assert len(masks) == 64
    configs = [dict(mask=m, threads=4, ubatch=32) for m in range(8)]
    decision = choose(masks, configs, configs[0])
    assert decision == read(root / 'masks-cycle-0.json')
    params = [row for name, row in rows.items() if name.startswith('params-c0-')]
    assert len(params) == 32
    configs = [dict(mask=decision['selected']['mask'], threads=t, ubatch=u)
        for t in (4, 2) for u in (32, 16, 64, 128)]
    decision = choose(params, configs, configs[0])
    assert decision == read(root / 'parameters-cycle-0.json')
    assert decision['selected'] == selected['config']
    for model in ('2B', '4B'):
        evidence = [row for name, row in rows.items() if name.startswith('selected-answer-' + model)]
        assert len(evidence) == 2
        assert all(row['quality']['pass'] and row['quality']['checks'] == 106 for row in evidence)
        assert all(row['answer_sha256'] == selected['quality'][model]['selected'] for row in evidence)
        for name, row in rows.items():
            if name.startswith('selected-answer-' + model):
                answer = read(root / name / 'answer.json')
                assert hashlib.sha256(answer['answer'].encode()).hexdigest() == row['answer_sha256']
    return dict(status='pass', receipts=counts, requests=len(rows), selected=selected['config'],
        policy_sha256=sha(policy), code_files=len(actual), source_of_selection='recomputed frozen stages')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board', type=Path, required=True)
    p.add_argument('--policy', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = verify(a.board, a.policy)
    if a.output.exists():
        raise ValueError('output exists')
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
