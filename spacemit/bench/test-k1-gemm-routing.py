#!/usr/bin/env python3
"""Ensure routing gates reject inactive candidates and wrong phase routing."""
import importlib.util
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('route',HERE/'k1-gemm-routing.py')
route=importlib.util.module_from_spec(spec); spec.loader.exec_module(route)


class Gates(unittest.TestCase):
    def test_phase_specific_dispatch(self):
        for mode in (0,1,2,3):
            text='\n'.join(f'K1_GEMM_ROUTE mode={mode} phase={phase} eligible=1 bypass={int(mode==3 or mode==(1 if phase=="prefill" else 2))} buffer_size=131072'
                           for phase in ('prefill','single'))
            route.check_activation(text,mode,('prefill','single'))
            for bad in (text.replace('eligible=1','eligible=0'), text.replace('131072','0'),
                        text.replace('bypass=1','bypass=0') if mode else text.replace('bypass=0','bypass=1')):
                with self.assertRaises(ValueError): route.check_activation(bad,mode,('prefill','single'))
            with self.assertRaises(ValueError): route.check_activation('',mode,('prefill','single'))

    def test_original_library_has_no_candidate_dispatch(self):
        route.check_activation('original',-1,('prefill',))
        with self.assertRaises(ValueError):
            route.check_activation('K1_GEMM_ROUTE mode=0 phase=prefill eligible=1 bypass=0 buffer_size=131072',-1,('prefill',))


if __name__=='__main__': unittest.main()
