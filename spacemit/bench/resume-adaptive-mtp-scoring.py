#!/usr/bin/env python3
"""Resume frozen adaptive scoring with a larger, recorded judge output budget."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod


def resume(root,key_file):
    scorer=load('frozen_scorer',root/'score-adaptive-mtp.py')
    judge=load('frozen_judge',root/'judge-shared-document-cache.py')
    transport=judge.chat_completion;parse=judge.parse_judgment
    def logged_parse(content):
        try:return parse(content)
        except ValueError as error:
            # Record only public judge text and validation failures, never credentials.
            with (root/'judge-invalid-responses.jsonl').open('a') as f:
                f.write(json.dumps({'reason':str(error),'content':content},ensure_ascii=False)+'\n')
            raise
    judge.parse_judgment=logged_parse
    judge.chat_completion=lambda url,model,key,messages,timeout,retries,max_tokens: transport(
        url,model,key,messages,timeout,retries,max(max_tokens,8192))
    original_loader=scorer.load
    scorer.load=lambda name,folder:judge if name=='judge-shared-document-cache' else original_loader(name,folder)
    status_file=root/'collector-exit-status'
    record=root/'adaptive-scoring-recovery.json'
    evidence={'status':'running','judge_response_token_budget':8192,
        'change':'Larger judge response budget only; frozen prompts, validators, generation and scoring gates retained.',
        'prior_collector_exit':status_file.read_text().strip() if status_file.exists() else None,
        'original_scorer_sha256':hashlib.sha256((root/'score-adaptive-mtp.py').read_bytes()).hexdigest(),
        'original_judge_sha256':hashlib.sha256((root/'judge-shared-document-cache.py').read_bytes()).hexdigest(),
        'recovery_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    record.write_text(json.dumps(evidence,indent=2)+'\n')
    status_file.unlink(missing_ok=True)
    try:
        result=scorer.score(root,key_file)
        status=0 if result['candidate_qualified'] else 2
        evidence.update(status='completed',exit=status)
        status_file.write_text(str(status)+'\n')
    except BaseException as error:
        evidence.update(status='failed',error=type(error).__name__+': '+str(error)[:300])
        status_file.write_text('1\n')
        (root/'scoring-phase').write_text('recovery failed: '+type(error).__name__+'\n')
        raise
    finally:
        record.write_text(json.dumps(evidence,indent=2)+'\n')
        with (root/'adaptive-scoring-recovery-history.jsonl').open('a') as f:
            f.write(json.dumps(evidence)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    p.add_argument('--key-file',type=Path,default=Path.home()/'.secret_ai_key')
    args=p.parse_args();resume(args.root.resolve(),args.key_file.resolve())
