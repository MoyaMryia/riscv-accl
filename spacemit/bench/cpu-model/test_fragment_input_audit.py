"""检查轨迹身份错配与不完整收据均停止预测。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from common import digest,seal

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fragment_input_audit',HERE/'fragment-input-audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)


class InputAuditTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name);self.plan=dict(cases=[dict(id='case')],kernels=[dict(id='kernel')],baseline='kernel')
        self.name='case-kernel';self.identity='binary'
        trace=self.root/(self.name+'-cpu0.jsonl');trace.write_text('{}\n')
        (self.root/'trace.so').write_bytes(b'plugin')
        record=dict(case='case',kernel='kernel',audit=dict(status='complete-invocation-audited',symbol='fragment_repeat',
            binary_sha256=self.identity,trace_sha256=digest(trace)))
        self.data=dict(status='selected-complete-invocations-audited',binary_sha256=self.identity,trace_calls=3,
            selected_cases=['case'],records=[record],plugin_sha256=digest(self.root/'trace.so'),
            tool_files={name:digest(HERE/name) for name in ('fragment-invocation.py','fragment-call.py','fragment-trace.c')})
        self.command=['qemu','-cpu',audit.CPU,'-plugin','trace.so','fragment','trace','0','0','17','3',self.name+'.bin','exact']
        self.save()

    def save(self):
        (self.root/'result.json').write_text(json.dumps(self.data))
        (self.root/(self.name+'-command.json')).write_text(json.dumps(self.command))
        (self.root/'SHA256SUMS').unlink(missing_ok=True);seal(self.root)

    def check(self):
        return audit.capture(self.root,self.plan,self.identity)

    def test_valid_capture(self):
        self.assertEqual(self.check()['trace_calls'],3)

    def test_wrong_case_kernel_seed_count_or_cpu_is_failure(self):
        for position,value in [(2,'max,vlen=128'),(7,'1'),(8,'1'),(9,'18'),(10,'9')]:
            with self.subTest(position=position):
                original=self.command[position];self.command[position]=value;self.save()
                with self.assertRaises(ValueError):self.check()
                self.command[position]=original

    def test_missing_or_duplicate_record_is_failure(self):
        original=self.data['records']
        for rows in ([],original*2):
            with self.subTest(records=len(rows)):
                self.data['records']=rows;self.save()
                with self.assertRaises(ValueError):self.check()

    def test_changed_decoder_is_failure(self):
        self.data['tool_files']['fragment-invocation.py']='different';self.save()
        with self.assertRaises(ValueError):self.check()

    def test_wrong_trace_record_is_failure(self):
        self.data['records'][0]['audit']['trace_sha256']='different';self.save()
        with self.assertRaises(ValueError):self.check()

    def test_empty_missing_or_duplicate_receipt_is_failure(self):
        receipt=self.root/'SHA256SUMS';valid=receipt.read_text();lines=valid.splitlines()
        for value in ('','\n'.join(lines[1:])+'\n',valid+lines[0]+'\n'):
            with self.subTest(receipt=value):
                receipt.write_text(value)
                with self.assertRaises(ValueError):self.check()

    def test_boolean_trace_count_is_failure(self):
        self.data['trace_calls']=True;self.save()
        with self.assertRaises(ValueError):self.check()

    def test_dot_prefix_receipts_are_valid(self):
        receipt=self.root/'SHA256SUMS'
        receipt.write_text(''.join(line.replace('  ','  ./',1)+'\n' for line in receipt.read_text().splitlines()))
        self.assertEqual(self.check()['trace_calls'],3)

    def test_path_alias_cannot_duplicate_receipt(self):
        receipt=self.root/'SHA256SUMS';value=receipt.read_text()
        receipt.write_text(value+value.splitlines()[0].replace('  ','  ./',1)+'\n')
        with self.assertRaises(ValueError):self.check()

    def test_model_freeze_mismatch_is_failure(self):
        model=self.root/'model.json';freeze=self.root/'pre-native-freeze.json'
        freeze.write_text('{}');model.write_text(json.dumps(dict(pre_native_freeze_sha256='different')))
        with self.assertRaises(ValueError):audit.validate(model,self.root,self.root,self.root)

    def test_frozen_decoder_mismatch_is_failure(self):
        fixed=dict(fit_tool_sha256=digest(HERE/'fragment-fit.py'),tools={name:digest(HERE/name)
            for name in ('fragment-state.py','fragment-invocation.py')})
        fixed['tools']['fragment-invocation.py']='different'
        freeze=self.root/'pre-native-freeze.json';freeze.write_text(json.dumps(fixed))
        model=self.root/'model.json';model.write_text(json.dumps(dict(pre_native_freeze_sha256=digest(freeze),
            fit_tool_sha256=fixed['fit_tool_sha256'])))
        with self.assertRaises(ValueError):audit.validate(model,self.root,self.root,self.root)


if __name__=='__main__':unittest.main()
