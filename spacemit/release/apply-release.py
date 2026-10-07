#!/usr/bin/env python3
"""Apply the measured infrastructure package to its exact clean source."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_source(root, manifest, snapshot=None):
    if snapshot:
        if sha(snapshot)!=manifest['clean_snapshot_manifest_sha256']:
            raise ValueError('unrecognized clean source snapshot receipt')
        receipt=json.loads(snapshot.read_text())
        if receipt['commit']!=manifest['source_commit']:
            raise ValueError('wrong snapshot revision')
        for name,expected in receipt['files_sha256'].items():
            if sha(root/name)!=expected: raise ValueError('snapshot source changed: '+name)
    else:
        head=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()
        if head!=manifest['source_commit']: raise ValueError('requires exact source commit '+manifest['source_commit'])
        if subprocess.check_output(['git','-C',str(root),'status','--porcelain'],text=True).strip():
            raise ValueError('source checkout must be clean')
    for name,expected in manifest['original_source_sha256'].items():
        if sha(root/name)!=expected: raise ValueError('original source hash differs: '+name)


def apply(root, check_only=False, snapshot=None):
    manifest=json.loads((HERE/'manifest.json').read_text()); patch=HERE/manifest['patch']
    if sha(patch)!=manifest['patch_sha256']: raise ValueError('release patch checksum mismatch')
    verify_source(root,manifest,snapshot)
    # Git applies one combined patch atomically. Outside a Git checkout it can
    # also patch a verified archive; the exact snapshot receipt supplies identity.
    subprocess.run(['git','apply','--check',str(patch)],cwd=root,check=True)
    if check_only:
        print('PASS: pinned clean source and release patch preflight'); return
    subprocess.run(['git','apply',str(patch)],cwd=root,check=True)
    hashes={name:sha(root/name) for name in manifest['patched_source_sha256']}
    if hashes!=manifest['patched_source_sha256']: raise ValueError('patched files differ from measured source')
    result=dict(source_commit=manifest['source_commit'],patch_sha256=manifest['patch_sha256'],source_sha256=hashes)
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout',type=Path); parser.add_argument('--check-only',action='store_true')
    parser.add_argument('--snapshot-manifest',type=Path,help='Pinned archived-source receipt for offline verification')
    args=parser.parse_args()
    try: apply(args.checkout.resolve(),args.check_only,args.snapshot_manifest)
    except (ValueError,OSError,subprocess.SubprocessError) as error: parser.exit(1,str(error)+'\n')
