#!/usr/bin/env python3
"""在控制器持锁期间采集一次请求，然后退出。"""
import argparse
import http.client
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import urllib.error
import urllib.request

import diagnostic as base
import repetition_guard
import trace_cases


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args(argv)
    job = json.loads(args.config.read_text())
    folder = Path(job['folder'])
    parameters = SimpleNamespace(max_tokens=job['max_tokens'], quality=Path(job['quality']),
                                 trace_plan={'prefix_rows': job['prefix_rows']})
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    chat = base.load_module('attempt_chat', Path(job['chat']))
    assessor = base.load_module('attempt_assessor', Path(job['assessment']))
    quality = base.load_module('attempt_quality', Path(job['quality']))
    options = job.get('repeat_guard')
    guard = repetition_guard.RepeatGuard(**options) if options else None
    try:
        record = trace_cases.sample(parameters, job['case'], job['arm'], chat, assessor, quality,
            job['pid'], job['url'], job['url'], folder, Path(job['log_path']),
            round_no=job['round'], legacy=job['legacy'], stream_path=folder / 'stream.sse',
            guard=guard)
    except repetition_guard.DegenerateOutput as error:
        base.save(folder / 'outcome.json', {'status': 'incomplete', 'reason': 'degenerate_repetition'})
        print(str(error), file=sys.stderr)
        return 3
    except trace_cases.OutputTruncated as error:
        base.save(folder / 'outcome.json', {'status': 'incomplete', 'reason': 'output_limit'})
        print(str(error), file=sys.stderr)
        return 3
    except TimeoutError as error:
        base.save(folder / 'outcome.json', {'status': 'incomplete', 'reason': 'request_timeout'})
        print(str(error), file=sys.stderr)
        return 3
    except (urllib.error.URLError, http.client.HTTPException) as error:
        if isinstance(error, urllib.error.HTTPError):
            error.close()
        base.save(folder / 'outcome.json', {'status': 'incomplete', 'reason': 'request_transport'})
        print(type(error).__name__ + ': ' + str(error), file=sys.stderr)
        return 3
    quality_pass = record['quality']['passed']
    if quality_pass is None:
        outcome = {'status': 'passed', 'reason': 'quality_review_pending'}
        status = 0
    else:
        outcome = {'status': 'passed' if quality_pass else 'failed',
                   'reason': 'complete' if quality_pass else 'quality'}
        status = 0 if quality_pass else 2
    base.save(folder / 'outcome.json', outcome)
    return status


if __name__ == '__main__':
    sys.exit(main())
