#!/usr/bin/env python3
"""核实每核扩展并保存可访问的平台资料。"""
import argparse
import glob
import os
from pathlib import Path
import subprocess
import resource
from common import digest, seal, write


def main(a):
    a.output.mkdir(parents=True,exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    patterns=['/sys/devices/system/cpu/cpu*/cache/index*/*',
        '/sys/devices/system/cpu/cpu*/topology/*',
        '/sys/devices/system/cpu/cpufreq/policy*/scaling_*',
        '/sys/devices/system/cpu/cpufreq/policy*/cpuinfo_*',
        '/sys/devices/system/cpu/cpufreq/policy*/affected_cpus',
        '/sys/devices/system/cpu/cpufreq/policy*/stats/time_in_state',
        '/sys/class/thermal/thermal_zone*/temp','/sys/class/thermal/thermal_zone*/type',
        '/sys/bus/event_source/devices/cpu/type','/sys/bus/event_source/devices/cpu/events/*',
        '/sys/bus/event_source/devices/cpu/format/*','/proc/sys/kernel/perf_event_paranoid',
        '/proc/cpuinfo','/proc/version','/proc/meminfo']
    files={}
    for pattern in patterns:
        for name in sorted(glob.glob(pattern)):
            path=Path(name)
            if path.is_file():
                try: files[name]=dict(value=path.read_text())
                except OSError as error: files[name]=dict(error=str(error))
    write(a.output/'sysfs-proc.json',files)
    result=[]
    for cpu in sorted(os.sched_getaffinity(0)):
        for mode in ('vector','ime'):
            try:
                run=subprocess.run([str(a.probe.resolve()),str(cpu),mode],capture_output=True,text=True,timeout=10)
                row=dict(cpu=cpu,mode=mode,returncode=run.returncode,stdout=run.stdout,stderr=run.stderr)
            except subprocess.TimeoutExpired:
                row=dict(cpu=cpu,mode=mode,returncode='timeout')
            result.append(row)
    write(a.output/'core-probes.json',dict(probe_sha256=digest(a.probe),records=result,
        limits=['successful fixed IME operation verifies this encoding and input only',
                'a failed probe does not identify a hardware cause',
                'frequency and thermal values are snapshots; no constant-frequency claim']))
    seal(a.output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--probe',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    main(p.parse_args())
