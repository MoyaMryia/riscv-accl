#!/usr/bin/env python3
"""Query runtime geometry and board configuration without changing settings."""
import argparse
import ctypes as C
import json
import os
from pathlib import Path
import platform
import stat


class Layout(C.Structure):
    _fields_ = [('blk_size', C.c_size_t), ('blk_num', C.c_size_t), ('is_fake_tcm', C.c_int)]


def audit(library):
    result = {'kernel': platform.uname()._asdict(), 'uid': os.getuid(),
              'runtime_library': str(library.resolve()), 'devices': {}, 'cpu': {}, 'thermal': {}}
    for name in ('/dev/tcm', '/dev/tcm_sync_mem', '/dev/hugetlb_1g'):
        p = Path(name)
        result['devices'][name] = {'exists': p.exists(), 'readable': os.access(p, os.R_OK),
                                  'writable': os.access(p, os.W_OK)}
        if p.exists(): result['devices'][name]['mode'] = oct(stat.S_IMODE(p.stat().st_mode))
    for p in Path('/sys/devices/system/cpu').glob('cpu[0-9]*/cpufreq/scaling_*'):
        if p.name in ('scaling_governor', 'scaling_cur_freq', 'scaling_max_freq'):
            try: result['cpu'][str(p)] = p.read_text().strip()
            except OSError: pass
    for p in Path('/sys/class/thermal').glob('thermal_zone*/temp'):
        try: result['thermal'][str(p)] = p.read_text().strip()
        except OSError: pass
    lib = C.CDLL(str(library), mode=C.RTLD_GLOBAL)
    lib.spine_tcm_runtime_version.restype = C.c_char_p
    lib.spine_tcm_runtime_is_available.restype = C.c_int
    lib.spine_tcm_runtime_layout_info.argtypes = [C.POINTER(Layout)]
    lib.spine_tcm_runtime_layout_info.restype = C.c_int
    info = Layout()
    result['tcm'] = {'version': lib.spine_tcm_runtime_version().decode(),
                     'available': lib.spine_tcm_runtime_is_available(),
                     'layout_status': lib.spine_tcm_runtime_layout_info(C.byref(info)),
                     'block_size': info.blk_size, 'block_count': info.blk_num,
                     'fake': bool(info.is_fake_tcm)}
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('library', type=Path)
    args = p.parse_args(); print(json.dumps(audit(args.library), indent=2))
