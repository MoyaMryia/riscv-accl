#!/usr/bin/env python3
"""Recheck a completed release's immutable artifacts without running inference."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import tarfile

HERE = Path(__file__).resolve().parent


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(root, preservation):
    run = load(root/'run.json')
    receipt = load(root/'collection-receipt.json')
    collected = load(root/'collection-verification.json')
    summary = load(root/'summary.json')
    manifest = load(root/'manifest.json')
    provenance = load(root/'provenance.json')
    expected = load(root/'expected-provenance.json')
    require(run['board'] == 'musepipro', 'direct board transport differs')
    for name in ('exit-status', 'collector-exit-status'):
        require((root/name).read_text().strip() == '0', name+' is not zero')
    require(collected['board_exit_status'] == '0' and collected['staged_code_verified']
            and collected['collector_code_verified'], 'collection was not verified')
    require(collected['remote_staged_code_sha256'] == run['code_sha256'], 'remote staged code differs')
    for table in (receipt['files_sha256'], run['code_sha256'], run['collector_code_sha256']):
        for name, checksum in table.items():
            require(Path(name).name == name and digest(root/name) == checksum, 'artifact differs: '+name)
    archive = root/'profile-artifacts.tar.gz'
    require(digest(archive) == receipt['archive_sha256'] and archive.stat().st_size == receipt['archive_bytes'],
            'archive identity differs')
    with tarfile.open(archive, 'r:gz') as bundle:
        members = bundle.getmembers()
        names = [m.name for m in members]
        require(len(names) == len(set(names)) and set(names) == set(receipt['files_sha256']),
                'archive file list differs')
        for member in members:
            require(member.isfile() and Path(member.name).name == member.name, 'unsafe archive entry')
            h = hashlib.sha256()
            with bundle.extractfile(member) as stream:
                for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
                    h.update(chunk)
            require(h.hexdigest() == receipt['files_sha256'][member.name], 'archive entry differs')
    require(summary['status'] == 'release verified' and summary['requests_completed'] == summary['requests_planned'] == 4,
            'release incomplete')
    require(provenance['source_revision'] == manifest['source_commit']
            == 'a990751d55a4c54acf2bb77d44282c2093652359', 'wrong clean revision')
    require(provenance['source_sha256'] == manifest['patched_source_sha256'], 'patched source differs')
    require(digest(root/manifest['patch']) == manifest['patch_sha256'], 'release patch differs')
    require(provenance['models'] == expected['models'], 'model provenance differs')
    for model, info in provenance['models'].items():
        require(info['sha256'] == manifest['models'][model]['sha256']
                and Path(info['path']).name == manifest['models'][model]['filename'], 'model pin differs')
    spec = importlib.util.spec_from_file_location('release_frozen_checks', root/'k1-release-check.py')
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    native = summary['stages']['native']
    require(native['cases_per_arm'] == 104 and native['bitwise_equal'], 'native graph gate incomplete')
    for mode in (0, 3):
        log = (root/f'native-{mode}.log').read_text()
        require('PASS: 104 production graph cases;' in log, 'native cases incomplete')
        runner.route.check_activation(log, mode, ('prefill', 'single'))
        require(digest(root/f'native-{mode}.data') == native['sha256'][str(mode)]
                == 'e31997719879fb9a858f9e970af7e11ceb68124657d41c53bd3b3f82c4dbd4dc',
                'native dump differs from measured baseline')
    pairs = load(root/'complete-answer-pairs.json')
    results = {}
    for model in ('2B', '4B'):
        prior = load(root/(model+'-frozen-pairs.json'))['unicode_runs']['control']
        pair = pairs[model]
        result = {}
        answers = []
        for mode, arm in ((0, 'baseline'), (3, 'optimized')):
            label = f'{model}-route{mode}'
            answer = load(root/(label+'.answer.json'))
            payload = answer['request']
            require(answer == pair[arm] and payload == prior['request'], 'frozen complete request differs')
            require(payload['seed'] == 42 and payload['temperature'] == 0 and payload['max_tokens'] == 2048
                    and payload['cache_prompt'] is False and payload['chat_template_kwargs']['enable_thinking'] is False,
                    'matched request settings differ')
            require(answer['prompt_tokens'] == prior['prompt_tokens'] == 162, 'full prompt differs')
            require(answer['audit'] == runner.audit(answer, payload, 162) and all(answer['audit'].values()),
                    'complete/cold request audit fails')
            require(answer['answer_sha256'] == hashlib.sha256(answer['answer'].encode()).hexdigest()
                    and (root/(label+'.answer.md')).read_text() == answer['answer']+'\n', 'saved answer differs')
            code = runner.checks.check_code('unicode_runs', answer['answer'])
            require(code == answer['code_test'] and code['pass'] and code['checks'] == 106, 'held-out code tests fail')
            command = answer['server_command']
            for flag, value in {'-t':'4','-c':'6144','--parallel':'1','-b':'32','-ub':'32',
                                '-fa':'on','-ctk':'f16','-ctv':'f16','-ngl':'0','--port':'18092'}.items():
                require(command[command.index(flag)+1] == value, 'server setting differs: '+flag)
            require('--no-context-shift' in command and '-md' not in command, 'server mode differs')
            log = (root/(label+'.server.log')).read_text()
            runner.route.check_activation(log, mode, ('prefill', 'single'))
            require('SPINE_FA_WIDE_TILE: RVV tiled attention enabled' in log, 'RVV activation absent')
            for key in ('ttft_s', 'wall_s'):
                require(math.isfinite(answer[key]) and answer[key] > 0, 'invalid client timing')
            timings = answer['timings']
            for key in ('prompt_ms', 'prompt_per_second', 'predicted_ms', 'predicted_per_second'):
                require(math.isfinite(timings[key]) and timings[key] > 0, 'invalid server timing')
            require(timings.get('cache_n', 0) == 0, 'server cache count nonzero')
            answers.append(answer['answer'])
            result[arm] = dict(output_tokens=answer['usage']['completion_tokens'], ttft_s=answer['ttft_s'],
                               answer_latency_s=answer['wall_s'], prefill_tok_s=timings['prompt_per_second'],
                               decode_tok_s=timings['predicted_per_second'], held_out_checks=106)
        require(answers[0] == answers[1] and pair['bitwise_text_equal'], 'paired text differs')
        require(pair['same_as_prior_control'] == (answers[0] == prior['answer']), 'prior identity record differs')
        results[model] = dict(arms=result, exact_text_equal=True, same_as_prior_control=pair['same_as_prior_control'])
    remote = load(preservation)
    target = run['remote_root']
    wanted = {target+'/source/'+n: h for n, h in manifest['patched_source_sha256'].items()}
    wanted.update({target+'/build/bin/llama-server':provenance['server_sha256'],
                   target+'/build/bin/libggml-cpu.so.0.16.0':provenance['library_sha256'],
                   target+'/build/CMakeCache.txt':provenance['cmake_cache_sha256'],
                   target+'/build/compile_commands.json':provenance['compile_commands_sha256']})
    wanted.update({target+'/'+n: h for n, h in run['code_sha256'].items()})
    require(remote['files_sha256'] == wanted and remote['board_exit_status'] == 0
            and remote['source_commit'] == manifest['source_commit'], 'post-run board preservation differs')
    require(set(remote['modified_source_files']) == set(manifest['patched_source_sha256']),
            'unexpected source changes')
    require(remote['baseline_source_commit'] == manifest['source_commit']
            and set(remote['baseline_modified_source_files']) == set(manifest['measured_baseline_source_sha256'])
            and remote['baseline_source_sha256'] == manifest['measured_baseline_source_sha256'],
            'measured baseline has additional source changes')
    runtime = {n: h for n, h in expected['artifacts_sha256'].items()
               if n.endswith(('libspine_tcm.so.3.0.1', 'libspert.so.0.6.2'))}
    require(len(runtime) == 2 and remote['runtime_files_sha256'] == runtime,
            'vendor runtime differs from measured configuration')
    require(remote['compiler_version'] == expected['compiler'], 'vendor compiler differs')
    for option, value in {'CMAKE_BUILD_TYPE':'Release','GGML_CPU_RISCV64_SPACEMIT':'ON',
                           'GGML_OPENMP':'OFF','GGML_RV_ZBA':'ON','GGML_NATIVE':'OFF',
                           'GGML_CPU_REPACK':'OFF','LLAMA_BUILD_TESTS':'OFF','LLAMA_OPENSSL':'OFF',
                           'LLAMA_CURL':'OFF','LLAMA_BUILD_UI':'OFF','LLAMA_USE_PREBUILT_UI':'OFF'}.items():
        require(remote['cmake_settings'][option] == value, 'fresh build option differs: '+option)
    return dict(status='independently verified release', board_exit_status=0, collector_exit_status=0,
                source_commit=manifest['source_commit'], artifacts_verified=len(receipt['files_sha256']),
                archive_sha256=receipt['archive_sha256'], staged_code_files=len(run['code_sha256']),
                collector_code_files=len(run['collector_code_sha256']), preservation_files=len(wanted),
                native_cases_per_arm=104, native_exact_identity=True, natural_answers=4,
                held_out_checks_per_answer=106, complete_answer_results=results, elapsed_s=summary['elapsed_s'],
                limitation='One complete code task per model and profile; descriptive timings only. Existing absolute quality limits remain.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_dir', type=Path)
    parser.add_argument('--preservation', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    output = json.dumps(verify(args.run_dir.resolve(), args.preservation.resolve()), indent=2)+'\n'
    if args.output:
        args.output.write_text(output)
    print(output, end='')
