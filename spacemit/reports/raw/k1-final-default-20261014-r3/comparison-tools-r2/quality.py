#!/usr/bin/env python3
"""Deterministic task checks and restricted execution of generated Python functions."""
import ast
import builtins
import json
from pathlib import Path
import random
import re
import resource
import signal
import subprocess
import sys


ADAPTIVE_CODE_SPECS = {
    'unicode_offsets': 'Return only Python source, with no imports, classes, tests or explanatory text. '
        'Implement run_spans(text) and expand_spans(spans). run_spans returns a list of (character,start,end) '
        'tuples for maximal consecutive runs of Unicode code points, using zero-based half-open offsets. '
        'Empty text returns []. expand_spans reconstructs the text. It raises ValueError for malformed input: '
        'every item must be a three-element list or tuple, character a one-character string, '
        'start/end integers excluding bool, start >= 0, end > start, first start 0, '
        'and each later start exactly the preceding end (no gaps or overlaps). '
        'Empty spans returns an empty string. Adjacent valid spans with the same character are allowed. '
        'Do not mutate inputs. Use Python builtins only; include useful docstrings and handle edge cases.'}

CODE_SPECS = {
    'free_windows': 'Return only Python source, without imports, classes, tests, or explanatory text. '
        'Implement merge_intervals(busy) and free_windows(busy, start, end). '
        'busy is a list of numeric (a,b) pairs representing half-open intervals [a,b). '
        'merge_intervals returns sorted tuples, merges overlapping or touching intervals, ignores zero-length '
        'intervals, and raises ValueError for reversed intervals. free_windows validates end >= start, '
        'clips busy intervals to [start,end), and returns sorted maximal free intervals as tuples. '
        'An empty query window returns []. Neither function may mutate its inputs. '
        'Use Python builtins only. Include useful docstrings and clear handling of edge cases.',
    'unicode_runs': 'Return only Python source, without imports, classes, tests, or explanatory text. '
        'Implement encode_runs(text) and decode_runs(runs). encode_runs returns a list of (character,count) '
        'tuples for consecutive runs of Unicode characters; empty text returns []. decode_runs returns the '
        'original string and rejects malformed items with ValueError: every item must be a two-element '
        'list or tuple, character must be a one-character string, and count must be a positive int, excluding '
        'bool. Empty runs returns an empty string. Do not mutate inputs. Use Python builtins only. '
        'Include useful docstrings and clear handling of edge cases.'}


def extract_code(answer):
    blocks = re.findall(r'```(?:python|py)?\s*\n(.*?)```', answer, re.S)
    if len(blocks) > 1: raise ValueError('multiple code blocks')
    source = blocks[0] if blocks else answer.strip()
    if len(source) > 50000: raise ValueError('source too large')
    return source


SAFE_BUILTINS = ('range', 'len', 'sorted', 'enumerate', 'zip', 'reversed', 'min', 'max', 'sum',
                 'all', 'any', 'abs', 'int', 'float', 'bool', 'str', 'list', 'tuple', 'dict', 'set',
                 'isinstance', 'type', 'ValueError', 'TypeError')
SAFE_ATTRIBUTES = {'append', 'extend', 'sort', 'copy', 'items', 'keys', 'values', 'get', 'join', 'pop', 'count'}


def checked_tree(source):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.Global, ast.Nonlocal,
                             ast.With, ast.AsyncWith, ast.AsyncFunctionDef, ast.Await)):
            raise ValueError('unsupported generated construct: ' + type(node).__name__)
        if isinstance(node, ast.Name) and node.id.startswith('_') and node.id != '_':
            raise ValueError('private/runtime names prohibited')
        if isinstance(node, (ast.FunctionDef, ast.arg)):
            name = node.name if isinstance(node, ast.FunctionDef) else node.arg
            if name.startswith('_') and name != '_': raise ValueError('private/runtime names prohibited')
        if isinstance(node, ast.FunctionDef) and node.decorator_list: raise ValueError('decorators prohibited')
        if isinstance(node, ast.Attribute) and node.attr not in SAFE_ATTRIBUTES:
            raise ValueError('unsupported attribute: ' + node.attr)
    if not all(isinstance(n, ast.FunctionDef) or isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant)
               and isinstance(n.value.value, str) for n in tree.body):
        raise ValueError('only functions and docstrings permitted at module level')
    return tree


def code_worker(case_id, source):
    # The source has no import/file/network/runtime-introspection capabilities.
    # Resource limits also bound accidental loops and allocations.
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
    signal.alarm(3)
    namespace = {'__builtins__': {n: getattr(builtins, n) for n in SAFE_BUILTINS}}
    exec(compile(checked_tree(source), '<generated-functions>', 'exec'), namespace)
    checks = 0
    def equal(actual, expected):
        nonlocal checks
        checks += 1
        if actual != expected: raise AssertionError('functional output mismatch at check ' + str(checks))
    def rejects(function, value):
        nonlocal checks
        checks += 1
        try: function(value)
        except ValueError: return
        raise AssertionError('invalid input not rejected at check ' + str(checks))
    rng = random.Random(20261003)
    if case_id == 'free_windows':
        merge, free = namespace['merge_intervals'], namespace['free_windows']
        equal(merge([]), []); equal(merge([(2, 4), (0, 2), (8, 8)]), [(0, 4)])
        equal(free([], 0, 10), [(0, 10)]); equal(free([(0, 20)], 5, 5), [])
        equal(free([(-3, 2), (4, 8), (8, 12)], 0, 10), [(2, 4)])
        rejects(merge, [(5, 2)]); rejects(lambda v: free([], *v), (3, 1))
        for _ in range(32):
            busy = [tuple(sorted((rng.randrange(-4, 17), rng.randrange(-4, 17)))) for i in range(rng.randrange(10))]
            original = list(busy)
            occupied = [any(a <= i < b for a, b in busy) for i in range(12)]
            expected = []; start = None
            for i, blocked in enumerate(occupied + [True]):
                if not blocked and start is None: start = i
                if blocked and start is not None: expected.append((start, i)); start = None
            equal(free(busy, 0, 12), expected); equal(busy, original)
    elif case_id == 'unicode_runs':
        encode, decode = namespace['encode_runs'], namespace['decode_runs']
        equal(encode(''), []); equal(decode([]), '')
        equal(encode('aa中中🙂b'), [('a', 2), ('中', 2), ('🙂', 1), ('b', 1)])
        for bad in [[('a', 0)], [('a', -1)], [('ab', 1)], [('a', True)], [('a', 1.2)], [('a',)], [3]]:
            rejects(decode, bad)
        for _ in range(32):
            text = ''.join(rng.choice('aaβ中🙂') for i in range(rng.randrange(80)))
            expected = []
            for ch in text:
                if expected and expected[-1][0] == ch: expected[-1] = (ch, expected[-1][1] + 1)
                else: expected.append((ch, 1))
            runs = encode(text); equal(runs, expected)
            original = list(runs); equal(decode(runs), text); equal(runs, original)
    elif case_id == 'unicode_offsets':
        spans, expand = namespace['run_spans'], namespace['expand_spans']
        equal(spans(''), []); equal(expand([]), '')
        equal(spans('aa中中🙂b'), [('a',0,2),('中',2,4),('🙂',4,5),('b',5,6)])
        equal(expand([('a',0,1),('a',1,3)]),'aaa')
        for bad in [[('a',1,2)],[('a',0,0)],[('a',-1,1)],[('ab',0,1)],
                    [('a',False,1)],[('a',0,True)],[('a',0,1.5)],[('a',0)], [3],
                    [('a',0,2),('b',1,3)],[('a',0,2),('b',3,4)]]:
            rejects(expand,bad)
        for _ in range(32):
            text=''.join(rng.choice('aaβ中🙂') for i in range(rng.randrange(80)))
            expected=[]
            for i,ch in enumerate(text):
                if expected and expected[-1][0]==ch:expected[-1]=(ch,expected[-1][1],i+1)
                else:expected.append((ch,i,i+1))
            result=spans(text);equal(result,expected)
            original=list(result);equal(expand(result),text);equal(result,original)
    else: raise ValueError('unknown code task')
    return {'pass': True, 'checks': checks, 'restriction': 'builtin-only functions, AST checks and resource limits'}


def check_code(case_id, answer):
    try:
        source = extract_code(answer); checked_tree(source)
        completed = subprocess.run([sys.executable, '-I', str(Path(__file__).resolve()), '--worker', case_id],
            input=json.dumps({'source': source}), text=True, capture_output=True, timeout=5)
        if completed.returncode:
            try: detail=json.loads(completed.stdout).get('reason','worker failed or exceeded budget')
            except (ValueError,AttributeError):detail='worker failed or exceeded budget'
            return {'pass':False,'reason':str(detail)[:200],'exit':completed.returncode}
        return json.loads(completed.stdout)
    except (Exception,) as error:
        return {'pass': False, 'reason': type(error).__name__ + ': ' + str(error)[:160]}


def fact_check(case, answer):
    plain = re.sub(r'[`*_]', '', answer)
    return {'facts': [bool(re.search(pattern, plain, re.I | re.S)) for pattern in case.get('fact_patterns', [])],
            'citations': [f'[{c}]' in answer for c in case.get('citations', [])]}


if __name__ == '__main__':
    try:
        print(json.dumps(code_worker(sys.argv[2], json.load(sys.stdin)['source'])))
    except BaseException as error:
        print(json.dumps({'pass': False, 'reason': type(error).__name__ + ': ' + str(error)[:160]}))
        sys.exit(1)
