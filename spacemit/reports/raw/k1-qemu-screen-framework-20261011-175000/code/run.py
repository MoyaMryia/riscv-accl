#!/usr/bin/env python3
"""验证 QEMU 功能和热点计数，不估算 K1 耗时。"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
CPU = 'rv64,v=true,vlen=256,elen=64'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(args):
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    commands = []
    summary = {'schema': 1, 'K1_timing': 'unverified', 'checks': {}, 'artifacts': {}}
    compiler = REPO/'lab/toolchain/toolchain/riscv/bin/riscv64-unknown-linux-gnu-gcc'
    nm = compiler.with_name('riscv64-unknown-linux-gnu-nm')

    def run(argv, label, timeout=60, expected=0):
        argv = list(map(str, argv))
        start = time.monotonic()
        record = {'argv': argv, 'label': label}
        commands.append(record)
        (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        with (out/(label+'.log')).open('w') as stream:
            result = subprocess.run(argv, stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
        record.update(returncode=result.returncode, host_seconds=time.monotonic()-start)
        (out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        if expected is not None and result.returncode != expected:
            raise RuntimeError(f'{label}: exit {result.returncode}')
        return (out/(label+'.log')).read_text(errors='replace'), result.returncode

    try:
        for path in (HERE/'probe.c', HERE/'metrics.c', Path('/usr/local/include/qemu-plugin.h'), compiler,
                     Path(shutil.which('qemu-riscv64'))):
            summary['artifacts'][str(path)] = sha(path)
        run(['qemu-riscv64', '--version'], 'upstream-version')
        run(['qemu-system-riscv64', '-machine', 'help'], 'upstream-machines')
        binary = out/'probe'
        run([compiler, '-O2', '-g', '-static', '-fno-pie', '-no-pie', '-march=rv64gcv', HERE/'probe.c', '-o', binary], 'build-probe')
        symbols, _ = run([nm, '-S', '--defined-only', binary], 'symbols')
        ranges = {}
        for line in symbols.splitlines():
            fields = line.split()
            if len(fields) == 4 and fields[-1].startswith('roi_'):
                ranges[fields[-1]] = (int(fields[0], 16), int(fields[0], 16)+int(fields[1], 16))
        cflags = shlex.split(subprocess.check_output(['pkg-config', '--cflags', '--libs', 'glib-2.0'], text=True))
        plugin = out/'metrics-upstream.so'
        run(['cc', '-std=c11', '-O2', '-shared', '-fPIC', '-fvisibility=hidden', '-Wall', '-Wextra', '-Werror',
             '-I/usr/local/include', HERE/'metrics.c', '-o', plugin, *cflags], 'build-plugin-upstream')

        def profile(qemu, cpu, plugin_path, symbol, mode, label):
            first, limit = ranges[symbol]
            metrics = out/(label+'.json')
            option = f'{plugin_path},start={first:#x},end={limit:#x},out={metrics}'
            text, _ = run([qemu, '-cpu', cpu, '-plugin', option, binary, mode], label)
            if 'PASS' not in text: raise ValueError('numeric success marker absent')
            result = json.loads(metrics.read_text())
            if result['overflow'] or not result['cpus']: raise ValueError('metrics invalid')
            return {key: sum(c[key] for c in result['cpus']) for key in result['cpus'][0] if key != 'cpu'}

        measures = {}
        for symbol in ('roi_copy', 'roi_direct'):
            measures[symbol] = profile('qemu-riscv64', CPU, plugin, symbol, 'rvv', symbol)
        for symbol, factor in (('roi_copy', 2), ('roi_direct', 1)):
            expected = factor*1024*4*64
            if measures[symbol]['vector_load_bytes'] != expected or measures[symbol]['vector_store_bytes'] != expected:
                raise ValueError('RVV memory callback byte count differs')
        summary['checks']['rvv'] = {'status': 'passed', 'metrics': measures,
            'scope': 'exact function address ranges; callees excluded; fixed work; one guest thread'}
        _, code = run(['qemu-riscv64', '-cpu', CPU, binary, 'ime'], 'upstream-ime-capability', expected=None)
        summary['checks']['upstream_ime'] = {'returncode': code, 'supported': code == 0}
        if args.vendor_root:
            vendor = args.vendor_root.resolve()
            qemu = vendor/'bin/qemu-riscv64'
            header = vendor/'include/qemu-plugin.h'
            for path in (qemu, header): summary['artifacts'][str(path)] = sha(path)
            run([qemu, '--version'], 'vendor-version')
            vendor_plugin = out/'metrics-vendor.so'
            run(['cc', '-std=c11', '-O2', '-shared', '-fPIC', '-fvisibility=hidden', '-Wall', '-Wextra', '-Werror',
                 '-I'+str(header.parent), HERE/'metrics.c', '-o', vendor_plugin, *cflags], 'build-plugin-vendor')
            result = profile(qemu, 'max,vlen=256', vendor_plugin, 'roi_ime', 'ime', 'vendor-ime')
            if result['ime'] != 32: raise ValueError('IME count differs')
            if result['load_bytes'] != 16*64 or result['store_bytes'] != 16*64:
                raise ValueError('IME memory callback byte count differs')
            summary['checks']['vendor_ime'] = {'status': 'passed', 'metrics': result,
                'scope': 'K1 signed vmadot only; max CPU is not a strict K1 feature profile'}
        if args.os:
            root = out/'root'
            shutil.copytree(REPO/'env/qemu/initrd-root', root, symlinks=True)
            shutil.copy2(binary, root/'probe')
            ime_command = '/probe ime\necho QEMU_SCREEN_IME_EXIT=$?\n' if args.os_vendor else ''
            (root/'init').write_text('#!/bin/sh\n'
                '/bin/mount -t devtmpfs devtmpfs /dev\n'
                '/bin/mount -t proc proc /proc\n'
                '/bin/mount -t sysfs sysfs /sys\n'
                'echo QEMU_SCREEN_OS_BEGIN\n'
                '/bin/uname -m\n/bin/uname -r\n'
                '/probe rvv\necho QEMU_SCREEN_RVV_EXIT=$?\n'+ime_command+
                'echo QEMU_SCREEN_OS_END\n/sbin/poweroff -f\n')
            (root/'init').chmod(0o755)
            entries = ['.']+[str(p.relative_to(root)) for p in sorted(root.rglob('*'))]
            packed = subprocess.run(['cpio', '-o', '-H', 'newc', '--null'], cwd=root,
                input=('\0'.join(entries)+'\0').encode(), stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, check=True)
            (out/'cpio.log').write_bytes(packed.stderr)
            initrd = out/'initramfs.cpio.gz'
            initrd.write_bytes(gzip.compress(packed.stdout, mtime=0))
            kernel = REPO/'env/qemu/vmlinux-rv64'
            bios = Path('/usr/local/share/qemu/opensbi-riscv64-generic-fw_dynamic.bin')
            for path in (kernel, bios, REPO/'env/qemu/initramfs.cpio.gz'):
                summary['artifacts'][str(path)] = sha(path)
            system_qemu = vendor/'bin/qemu-system-riscv64' if args.os_vendor else Path(shutil.which('qemu-system-riscv64'))
            summary['artifacts'][str(system_qemu)] = sha(system_qemu)
            text, _ = run([system_qemu, '-M', 'virt', '-cpu', 'max,vlen=256' if args.os_vendor else CPU, '-m', '512M', '-smp', '2',
                '-bios', bios, '-kernel', kernel, '-initrd', initrd, '-append', 'console=ttyS0 rdinit=/init',
                '-nographic', '-monitor', 'none', '-no-reboot', '-nic', 'none'], 'os-boot', timeout=90)
            if 'QEMU_SCREEN_RVV_EXIT=0' not in text or 'QEMU_SCREEN_OS_END' not in text or 'Kernel panic' in text:
                raise ValueError('OS numeric probe failed')
            if args.os_vendor and 'QEMU_SCREEN_IME_EXIT=0' not in text: raise ValueError('OS IME probe failed')
            summary['checks']['os'] = {'status': 'passed', 'machine': 'virt', 'guest_cpus': 2,
                'ime': args.os_vendor,
                'scope': 'Linux boot and RVV process; no K1 SoC or cycle model'}
        summary['status'] = 'passed'
    except Exception as error:
        summary.update(status='failed', error=str(error))
        raise
    finally:
        (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
        (out/'SHA256SUMS').write_text(''.join(
            sha(p)+'  '+str(p.relative_to(out))+'\n' for p in sorted(out.rglob('*'))
            if p.is_file() and not p.is_symlink() and p.name != 'SHA256SUMS'))
    print(json.dumps(summary['checks'], indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--vendor-root', type=Path)
    parser.add_argument('--os', action='store_true')
    parser.add_argument('--os-vendor', action='store_true')
    args = parser.parse_args()
    if args.os_vendor and (not args.os or not args.vendor_root): parser.error('--os-vendor requires --os and --vendor-root')
    main(args)
