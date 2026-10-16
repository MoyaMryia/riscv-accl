"""检查源码夹具、保护区与配对观测的失败处理。"""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from common import digest

HERE=Path(__file__).resolve().parent


def module(name):
    spec=importlib.util.spec_from_file_location(name.replace('-','_'),HERE/(name+'.py'))
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


builder=module('fragment-build')
assessor=module('fragment-assess')


class FragmentSourceTests(unittest.TestCase):
    def plan(self):
        return dict(schema=1,id='source_test',baseline='baseline',
            cases=[dict(id='small',work_units=8,input_bytes=8,output_bytes=8,offset=1)],
            kernels=[dict(id='baseline',symbol='baseline'),dict(id='candidate',symbol='candidate')],
            contract=dict(boundary='完整片段调用。'))

    def sessions(self):
        result=[]
        for session in (0,1):
            rows=[]
            for repeat in range(5):
                for count in (10,20,40):
                    for kernel,slope in (('baseline',100),('candidate',80)):
                        rows.append(dict(case='small',kernel=kernel,repeat=repeat,calls=count,work_units=8,cpu=0,
                            cycles=count*slope+19,wall_ns=count*slope+23,thread_cpu_ns=count*slope+29,
                            enabled=1000,running=1000,frequency_before_khz=1600000,frequency_after_khz=1600000,
                            voluntary_switches=0,involuntary_switches=0))
            result.append(rows)
        return result

    def test_source_ids_and_buffer_bounds(self):
        plan=self.plan();builder.validate(plan)
        plan['cases'][0]['offset']=64
        with self.assertRaises(ValueError):builder.validate(plan)

    def test_duplicate_kernel_is_failure(self):
        plan=self.plan();plan['kernels'][1]['symbol']='baseline'
        with self.assertRaises(ValueError):builder.validate(plan)

    def test_known_paired_slopes(self):
        result=assessor.summarize(self.plan(),self.sessions())
        self.assertEqual(result['status'],'paired-observations-verified')
        self.assertEqual(result['observations'],60)
        metric=result['cases'][0]['comparisons'][0]['metrics']['wall_ns']
        self.assertAlmostEqual(metric['candidate_over_baseline'],.8)
        self.assertEqual(metric['observed_paired_ratio_range'],[.8,.8])
        self.assertIsNone(result['prediction_confidence'])
        self.assertFalse(result['automatic_performance_rejection'])

    def test_missing_observation_is_failure(self):
        sessions=self.sessions();sessions[0].pop()
        with self.assertRaises(ValueError):assessor.summarize(self.plan(),sessions)

    def test_duplicate_call_count_is_failure(self):
        sessions=self.sessions();sessions[0][2]['calls']=10
        with self.assertRaises(ValueError):assessor.summarize(self.plan(),sessions)

    def test_unpaired_call_count_is_failure(self):
        sessions=self.sessions()
        for row in sessions[0]:
            if row['kernel']=='candidate':row['calls']*=2
        with self.assertRaises(ValueError):assessor.summarize(self.plan(),sessions)

    def test_counter_multiplex_is_failure(self):
        sessions=self.sessions();sessions[1][0]['running']=999
        with self.assertRaises(ValueError):assessor.summarize(self.plan(),sessions)

    def test_negative_slope_is_retained_failure(self):
        sessions=self.sessions()
        for rows in sessions:
            for row in rows:row['wall_ns']=10000-row['calls']
        result=assessor.summarize(self.plan(),sessions)
        self.assertEqual(result['status'],'nonpositive-slopes')
        self.assertTrue(result['nonpositive_slopes'])
        self.assertEqual(result['cases'][0]['comparisons'][0]['metrics'],{})

    @unittest.skipUnless(shutil.which('cc'),'需要本机 C 编译器。')
    def test_actual_host_fixture_guards_and_input_check(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'functions.c'
            good='''#include "fragment-fixture.h"
#include <string.h>
void baseline(const uint8_t *p,uint8_t *q,size_t n){memcpy(q,p,n);}
void candidate(const uint8_t *p,uint8_t *q,size_t n){memcpy(q,p,n);}
void fragment_reference(const uint8_t *p,uint8_t *q,size_t n){for(size_t i=0;i<n;i++)q[i]=p[i];}
'''
            for variant,body in [('good',good),('guard',good.replace('memcpy(q,p,n);}','memcpy(q,p,n);q[n]=0;}')),
                                 ('input',good.replace('memcpy(q,p,n);}','memcpy(q,p,n);((uint8_t *)p)[0]^=1;}'))]:
                source.write_text(body)
                plan=self.plan();plan.update(sources=[dict(path=str(source),sha256=digest(source))],
                    compiler_flags=['-O2','-std=c11','-Wall','-Wextra','-Werror'])
                path=root/(variant+'.json');path.write_text(json.dumps(plan))
                compiler=Path('/usr/bin/cc') if Path('/usr/bin/cc').exists() else Path(shutil.which('cc'))
                output=root/variant;builder.build(path,compiler,output)
                dumps=root/(variant+'-dumps');dumps.mkdir()
                rc=subprocess.run([str(output/'fragment'),'check-all',str(dumps)],capture_output=True).returncode
                self.assertEqual(rc,0 if variant=='good' else 5)
                if variant=='good':
                    self.assertEqual(len(list(dumps.iterdir())),6)
                    repeat_dump=root/'repeated.bin'
                    result=subprocess.run([str(output/'fragment'),'trace','0','0','17','9',str(repeat_dump),'exact'],capture_output=True)
                    self.assertEqual(result.returncode,0)
                    self.assertEqual(repeat_dump.read_bytes(),(dumps/'small-baseline-seed17.bin').read_bytes())
                    for count in ('0','65'):
                        result=subprocess.run([str(output/'fragment'),'trace','0','0','17',count,str(root/'invalid.bin'),'exact'],capture_output=True)
                        self.assertEqual(result.returncode,2)


if __name__=='__main__':unittest.main()
