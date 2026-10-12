"""固定组合开关，并核验实际路径。"""
import os
import re

import prepare

FAST = prepare.module('combined_fast', prepare.HERE.parent/'k1-fast-test.py')
QUALITY = prepare.module('combined_quality', prepare.HERE.parent/'k1-ssm-quality.py')
ARMS = {'C0': 0, 'B': 1, 'H': 2, 'G': 4, 'P': 6, 'F': 7, 'L': 8}


class NumericalStop(RuntimeError):
    pass


def flags(arm):
    code = ARMS[arm]
    return {'SPINE_K1_FA_GQA': str(int(bool(code & 1))),
            'SPINE_K1_SSM_CONV': '3' if code & 2 or arm == 'L' else '0',
            'SPINE_GDN_PREFILL': str(int(bool(code & 4) or arm == 'L')),
            'SPINE_K1_GDN_REVISION': str(int(bool(code & 4)))}


def arm_env(arm, library):
    env = {k: v for k, v in os.environ.items() if not k.startswith(('SPINE_', 'SPACEMIT_'))}
    env.update(SPINE_FA_WIDE_TILE='1', SPINE_FA_K1_LAYOUT='0', SPINE_K1_GEMM_ROUTE='3',
               SPINE_K1_TRACE='1', SPINE_K1_FA_DECODE='0', SPINE_K1_CONV_SILU='0')
    env.update(flags(arm))
    env['LD_LIBRARY_PATH'] = str(library)+':'+env.get('LD_LIBRARY_PATH', '')
    return env


def activation(text, arm, require_both=False, require_shared=False, fixed_route=True, rs3=False):
    selected = flags(arm)
    QUALITY.check_activation(text, int(selected['SPINE_K1_SSM_CONV']), require_both=require_both)
    recurrent = selected['SPINE_GDN_PREFILL'] == '1' and not rs3
    revised = selected['SPINE_K1_GDN_REVISION'] == '1' and not rs3
    if ('SPINE_GDN_PREFILL: scalar-gate K1 RVV fusion enabled' in text) != recurrent:
        raise ValueError('GDN activation differs: '+arm)
    if ('SPINE_GDN_PREFILL_R2: retained two state segments' in text) != revised:
        raise ValueError('GDN revision activation differs: '+arm)
    if revised:
        workers = set(re.findall(r'K1_GDN_R2 worker=(\d+) workers=4 state=128', text))
        if workers != {'0', '1', '2', '3'}:
            raise ValueError('GDN worker coverage differs: '+arm)
    rows = re.findall(r'K1_FA path=([\w-]+) heads=(\d+) kv_heads=(\d+) history=(\d+) chunk=\d+:\d+ worker=(\d+) workers=(\d+)', text)
    shared = [row for row in rows if row[0] == 'B1']
    if selected['SPINE_K1_FA_GQA'] == '0' and shared:
        raise ValueError('inactive attention path is present')
    if require_shared and {row[-2] for row in shared if int(row[3]) >= 512} != {'0', '1', '2', '3'}:
        raise ValueError('shared attention workers are absent')
    if any(row[-1] != '4' or (row[0] == 'B1' and int(row[2]) < 4 and int(row[3]) < 512) for row in rows):
        raise ValueError('attention fallback or thread count differs')
    if fixed_route and ('K1_GEMM_ROUTE mode=3' not in text or
            'SPINE_FA_WIDE_TILE: RVV tiled attention enabled for 256-dim heads' not in text):
        raise ValueError('fixed route or attention evidence is absent')
