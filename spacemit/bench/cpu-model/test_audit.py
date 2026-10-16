"""检查机器码变化、证据遗漏与归档覆盖保护。"""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import audit
from common import digest
import snapshot


class AuditTests(unittest.TestCase):
    def test_control_flow_change_is_rejected(self):
        plan=dict(records=[dict(id='cpu_000',instructions=[dict(kind='add',asm='add t0,t0,a4')])])
        text='00000000 <cpu_000>:\n 80: 00e282b3 add t0,t0,a4\n 84: fff50513 add a0,a0,-1\n 88: fe051ce3 bnez a0,80\n'
        self.assertEqual(audit.binary(plan,text)['instructions'],1)
        with self.assertRaises(ValueError):
            audit.binary(plan,text.replace('fe051ce3','fe051ae3'))

    def test_missing_receipt_entry_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            run=Path(directory)/'run-training';run.mkdir()
            sample=run/'samples.jsonl';sample.write_text('evidence\n')
            (run/'SHA256SUMS').write_text(f'{digest(sample)}  run-training/samples.jsonl\n')
            self.assertEqual(audit.receipts(run),1)
            (run/'unlisted.log').write_text('extra\n')
            with self.assertRaises(ValueError):
                audit.receipts(run)

    def test_changed_evidence_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            run=Path(directory)/'run-training';run.mkdir()
            sample=run/'samples.jsonl';sample.write_text('evidence\n')
            (run/'SHA256SUMS').write_text(f'{digest(sample)}  run-training/samples.jsonl\n')
            sample.write_text('changed\n')
            with self.assertRaises(ValueError):
                audit.receipts(run)

    def test_archive_failure_does_not_publish(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'work';root.mkdir()
            target=Path(directory)/'evidence.tar.gz'
            with patch.object(snapshot.tarfile,'open',side_effect=OSError('interrupted')):
                with self.assertRaises(OSError):
                    snapshot.publish(root,target)
            self.assertFalse(target.exists())
            self.assertTrue(target.with_name(target.name+'.partial').exists())

    def test_archive_does_not_replace_existing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'work';root.mkdir()
            target=Path(directory)/'evidence.tar.gz';target.write_bytes(b'original')
            with self.assertRaises(FileExistsError):
                snapshot.publish(root,target)
            self.assertEqual(target.read_bytes(),b'original')


if __name__=='__main__':
    unittest.main()
