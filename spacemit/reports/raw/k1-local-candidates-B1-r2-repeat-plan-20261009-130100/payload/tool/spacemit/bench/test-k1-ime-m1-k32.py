#!/usr/bin/env python3
"""Check that unrolling preserves the complete original assembly trace."""
import importlib.util
from pathlib import Path
import re
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('patcher',HERE/'make-k1-ime-m1-k32.py')
patcher=importlib.util.module_from_spec(spec); spec.loader.exec_module(patcher)
SOURCE=HERE.parent/'reports/raw/k1-ime-m1-k32-20261007-121231/baseline-ime-m1-k32.cpp'


def instructions(fragment, source):
    macros={}
    for match in re.finditer(r'^#define (\w+)[^\n]*\n((?:.*\\\n)*[^\n]*)',source,re.M):
        macros[match[1]]=match[2]
    result=[]
    for line in fragment.splitlines():
        stripped=line.strip()
        if stripped in macros:
            result.extend(instructions(macros[stripped],source)); continue
        match=re.search(r'"([^"\n]*)\\n\\t"',line)
        if match:
            ins=' '.join(match[1].split())
            if ins.startswith(('LOOP_INNER', 'addi t5,', 'bnez t5,')): continue
            result.append(ins)
    return result


class TestFixedKernel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=SOURCE.read_text(); cls.new=patcher.generate(cls.old)

    def test_instruction_trace(self):
        start=self.old.index('template <bool HasZeroPoint>\nvoid SQ4BitGemmM1Kernel_')
        end=self.old.index('\n\n\n// ---- Q8_0',start)
        fragment=self.old[start:end].split('    } else {\n',1)[1]
        begin=fragment.index('                "LOOP_INNER%=')
        stop=fragment.index('                "bnez         t5, LOOP_INNER%=',begin)
        step=fragment[begin:stop]
        fragment=fragment[:begin]+step+step+fragment[stop:]
        fixed=self.new[self.new.index('static __attribute__((noinline)) void k1_m1_k32_fixed'):self.new.index('#undef K1_M1_K32_LOAD')]
        expected=instructions(fragment,self.old); actual=instructions(fixed,self.new)
        self.assertGreater(len(expected),100)
        self.assertEqual(expected,actual)
        self.assertNotIn('LOOP_INNER',fixed); self.assertNotIn('t5',fixed)

    def test_preserved_other_kernels(self):
        # The full original M1 function and every original macro remain exact;
        # Q8 and quantizer bodies also remain intact in the generated unit.
        for left,right in [
            ('template <bool HasZeroPoint>\nvoid SQ4BitGemmM1Kernel_', '\n\n\n// ---- Q8_0'),
            ('#define SQ4BIT_KERNEL_LOAD_1x8x2_4X8X4 ', '\n\n#define SQ4BIT_KERNEL_LOAD_ZP_')]:
            begin=self.old.index(left); end=self.old.index(right,begin)
            self.assertIn(self.old[begin:end],self.new)
        begin=self.old.index('size_t gemm_kernel_i8i8(')
        self.assertEqual(self.old[begin:],self.new[self.new.index('size_t gemm_kernel_i8i8('):])

    def test_refuse_source_drift(self):
        with self.assertRaises(ValueError): patcher.generate(self.old.replace('vfmacc.vv','vfmul.vv',1))
        with self.assertRaises(ValueError): patcher.generate(self.new)


if __name__=='__main__': unittest.main()
