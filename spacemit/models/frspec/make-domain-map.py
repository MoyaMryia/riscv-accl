#!/usr/bin/env python3
"""Build a 32k d2t map with reserved capacity for domain corpora."""

import argparse
from ast import literal_eval
from collections import Counter
from hashlib import sha256
from pathlib import Path
from struct import pack

N_VOCAB = 248320
N_DRAFT = 32768
SPECIAL_START = 248000
HERE = Path(__file__).resolve().parent


def read_ids(path):
    ids = literal_eval(path.read_text())
    if not isinstance(ids, list) or not all(isinstance(v, int) and 0 <= v < N_VOCAB for v in ids):
        raise ValueError(f"expected a list of Qwen3.5 token IDs in {path}")
    return ids


def ranked(ids):
    counts = Counter(ids)
    return sorted(counts, key=lambda token: (-counts[token], token))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ids", type=Path, default=HERE / "corpus-token-ids.txt")
    parser.add_argument("--domain-ids", type=Path, action="append", default=[],
                        help="repeat for each domain corpus; must use the same Qwen3.5 tokenizer")
    parser.add_argument("--domain-quota", type=int, default=4096,
                        help="maximum distinct IDs reserved per domain before base ranking")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not args.domain_ids:
        parser.error("at least one --domain-ids corpus is required")
    if not 0 < args.domain_quota * len(args.domain_ids) <= N_DRAFT - (N_VOCAB - SPECIAL_START):
        parser.error("domain quotas leave no room for special tokens or base ranking")

    output = list(range(SPECIAL_START, N_VOCAB))
    seen = set(output)
    for corpus in args.domain_ids:
        added = 0
        for token in ranked(read_ids(corpus)):
            if token not in seen:
                output.append(token)
                seen.add(token)
                added += 1
            if added == args.domain_quota:
                break
        print(f"{corpus}: reserved {added} unique tokens")
    for token in ranked(read_ids(args.base_ids)):
        if token not in seen:
            output.append(token)
            seen.add(token)
        if len(output) == N_DRAFT:
            break
    if len(output) < N_DRAFT:
        output.extend(token for token in range(N_VOCAB) if token not in seen)
    output = output[:N_DRAFT]
    assert len(output) == len(set(output)) == N_DRAFT
    payload = pack(f"<{N_DRAFT}q", *output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    print(f"{args.output}: sha256={sha256(payload).hexdigest()}")


if __name__ == "__main__":
    main()
