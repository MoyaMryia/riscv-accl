#!/usr/bin/env python3
"""收集原基线与合格组合的六项完整回答。"""
import hashlib
import json
import re
import signal
import socket
import subprocess

import combined_common as prefill


def collect(root, source, server, expected, library, candidate):
    root.mkdir()
    quality = prefill.prepare.module('answer_quality', prefill.prepare.HERE.parent/'k1-ssm-quality.py')
    pilot, chat, checks = quality.pilot, quality.chat, quality.checks
    summary = {'status': 'running', 'candidate': candidate, 'models': {}, 'requests_completed': 0,
               'planned_requests': 24, 'quality': 'review-pending',
               'limitations': 'One pair per task and model. Report absolute errors and candidate regressions separately.'}

    def save(phase):
        (root/'phase').write_text(phase+'\n')
        (root/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')

    def write(path, value):
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

    url = 'http://127.0.0.1:18085'
    readme = (source/'tools/server/README.md').read_text()
    summary['readme_sha256'] = hashlib.sha256(readme.encode()).hexdigest()
    summary['protocol'] = {'tasks': ['routes', 'trace', 'aggregation', 'free_windows', 'unicode_runs', 'chinese_policy'],
        'threads': 4, 'batch': 32, 'ubatch': 32, 'context': 6144, 'document_budget': 2048,
        'facts_output_guard': 512, 'code_prose_output_guard': 2048, 'natural_stop': True,
        'request_budget_s': 1800, 'mtp': False, 'route': 3, 'kv': 'f16',
        'temperature': 0, 'seed': 42, 'order': {'2B': ['C0', candidate], '4B': [candidate, 'C0']}}
    blocks, base_cases = pilot.doc_blocks(readme)
    try:
        for model in ('2B', '4B'):
            document = None
            pairs, configs, counts = {}, {}, {}
            for arm in summary['protocol']['order'][model]:
                save(model+' '+arm+' server startup')
                with socket.socket() as probe:
                    if probe.connect_ex(('127.0.0.1', 18085)) == 0:
                        raise ValueError('benchmark port is busy')
                argv = [str(server), '-m', expected['models'][model]['path'], '--alias', 'local',
                        '-t', '4', '-c', '6144', '--parallel', '1', '-b', '32', '-ub', '32',
                        '-fa', 'on', '-ctk', 'f16', '-ctv', 'f16', '-ngl', '0',
                        '--no-context-shift', '--host', '127.0.0.1', '--port', '18085']
                env = prefill.arm_env(arm, library)
                configs[arm] = {'command': argv, 'runtime': {k: v for k, v in env.items()
                    if k.startswith('SPINE_') or k == 'LD_LIBRARY_PATH'}}
                write(root/(model+'-configs.json'), configs)
                logpath = root/(model+'-'+arm+'.server.log')
                with logpath.open('w') as log:
                    proc = subprocess.Popen(argv, stdout=log, stderr=subprocess.STDOUT, env=env)
                    try:
                        pilot.bench.wait_healthy(proc, url, 120)
                        if document is None:
                            document, count = pilot.quality.make_document(url, chat, blocks, readme, 2048, 120)
                            (root/(model+'-document.txt')).write_text(document)
                            cases = pilot.task_cases(document, base_cases)
                            if {case['case_id'] for case in cases} != set(summary['protocol']['tasks']):
                                raise ValueError('complete-answer task set differs')
                            for case in cases:
                                if case['kind'] == 'code' or case['case_id'] == 'chinese_policy':
                                    case['max_tokens'] = 2048
                            write(root/(model+'-cases.json'), {'cases': cases, 'blocks': blocks, 'document_tokens': count})
                        for case in (cases if arm == 'C0' else list(reversed(cases))):
                            save(model+' '+arm+' '+case['case_id'])
                            payload = chat.request_body([{'role': 'system', 'content': case['system']},
                                {'role': 'user', 'content': case['user']}], 'local', 0, case['max_tokens'])
                            payload.update(cache_prompt=False, stream_options={'include_usage': True}, verbose=True)
                            count = chat.count_prompt_tokens(url, payload, 120)
                            if count+case['max_tokens'] > 6144:
                                raise ValueError('complete input and output exceed context')
                            if case['case_id'] in counts and counts[case['case_id']] != count:
                                raise ValueError('paired input counts differ')
                            counts[case['case_id']] = count
                            record = {'case_id': case['case_id'], 'arm': arm, 'model': model,
                                'request': payload, 'prompt_tokens': count,
                                'request_sha256': hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()}
                            try:
                                signal.alarm(1800)
                                answer = chat.complete(url, payload, 1800, display=False)
                                record.update(answer, audit=quality.audit_result(answer, payload, count),
                                              facts=checks.fact_check(case, answer['answer']))
                                if case['kind'] == 'code':
                                    record['code_test'] = checks.check_code(case['case_id'], answer['answer'])
                            except Exception as exc:
                                record['error'] = type(exc).__name__+': '+str(exc)
                                raise
                            finally:
                                signal.alarm(0)
                                pairs.setdefault(case['case_id'], {})[arm] = record
                                write(root/(model+'-pairs.json'), pairs)
                                summary['requests_completed'] += 1
                                save(model+' '+arm+' '+case['case_id'])
                            invalid = [key for key, value in record['audit'].items() if not value and key != 'complete']
                            if invalid:
                                raise ValueError('invalid complete-answer record: '+', '.join(invalid))
                            (root/(model+'-'+arm+'-'+case['case_id']+'-answer.md')).write_text(record['answer']+'\n')
                    finally:
                        proc.terminate()
                        try:
                            proc.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                            proc.wait()
                prefill.activation(logpath.read_text(), arm)
                text = logpath.read_text()
                quality.check_activation(text, int(prefill.flags(arm)['SPINE_K1_SSM_CONV']))
                routing = re.findall(r'K1_GEMM_ROUTE mode=(\d) phase=(prefill|single)', text)
                if {phase for _, phase in routing} != {'prefill', 'single'} or any(mode != '3' for mode, _ in routing):
                    raise ValueError('route-3 activation differs')
            if len(pairs) != 6 or not all(set(pair) == {'C0', candidate} for pair in pairs.values()):
                raise ValueError('complete-answer paired coverage is incomplete')
            summary['models'][model] = {'requests_completed': 12, 'status': 'generation completed'}
        summary['status'] = 'generation completed; review pending'
        save(summary['status'])
        return summary
    except BaseException as exc:
        summary.update(status='failed', error=str(exc))
        save('complete-answer campaign failed')
        raise
