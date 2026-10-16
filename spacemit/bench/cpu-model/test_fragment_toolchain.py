"""检查辅助模块漂移、历史绑定来源与拟合输入拒绝路径。"""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import tarfile
import unittest
from unittest.mock import patch
from common import digest

HERE=Path(__file__).resolve().parent


def load(name):
    spec=importlib.util.spec_from_file_location(name.replace('-','_'),HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


chain=load('fragment-toolchain');binder=load('fragment-bind');checked=load('fragment-fit-checked')


class ToolchainTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name)

    def test_each_helper_change_is_rejected(self):
        for name in chain.FILES:(self.root/name).write_bytes((HERE/name).read_bytes())
        with patch.object(chain,'HERE',self.root):
            frozen=chain.identities();chain.verify(frozen)
            for name in chain.FILES:
                with self.subTest(name=name):
                    path=self.root/name;original=path.read_bytes();path.write_bytes(original+b'\n')
                    with self.assertRaises(ValueError):chain.verify(frozen)
                    path.write_bytes(original)

    def test_missing_helper_is_rejected(self):
        frozen=chain.identities();frozen.pop('common.py')
        with self.assertRaises(ValueError):chain.verify(frozen)

    def archive(self,changed=None,missing=None):
        model=self.root/'model.json';model.write_text(json.dumps(dict(parameters=dict(width=2))))
        contents={'frozen-model.json':model.read_bytes()}
        for name in binder.CORE:
            if name!=missing:contents['tools/'+name]=(HERE/name).read_bytes()+(b'\n' if name==changed else b'')
        contents['SHA256SUMS']=''.join(hashlib.sha256(body).hexdigest()+'  '+name+'\n' for name,body in contents.items()).encode()
        archive=self.root/'portable.tar.gz'
        with tarfile.open(archive,'w:gz') as stream:
            for name,body in contents.items():
                member=tarfile.TarInfo('portable/'+name);member.size=len(body);stream.addfile(member,io.BytesIO(body))
        receipt=self.root/'SHA256SUMS';receipt.write_text(digest(archive)+'  portable.tar.gz\n')
        return model,archive,receipt,self.root/'bound.json'

    def test_bind_retains_parameters_and_marks_later_check(self):
        paths=self.archive();result=binder.bind(*paths)
        self.assertEqual(result['parameters'],dict(width=2))
        self.assertEqual(result['runtime_binding']['kind'],'post-measurement-integrity-check')
        self.assertFalse(result['runtime_binding']['original_pre_native_tools_extended'])
        chain.verify(result['runtime_binding']['tools'])

    def test_archived_helper_drift_is_rejected(self):
        for name in ('common.py','binary-input.py','fragment-check.py'):
            with self.subTest(name=name):
                with self.assertRaises(ValueError):binder.bind(*self.archive(changed=name))

    def test_missing_archived_helper_is_rejected(self):
        with self.assertRaises(ValueError):binder.bind(*self.archive(missing='common.py'))

    def test_archive_identity_is_required(self):
        paths=self.archive();paths[2].write_text('0'*64+'  portable.tar.gz\n')
        with self.assertRaises(ValueError):binder.bind(*paths)

    def test_model_must_belong_to_archive(self):
        paths=self.archive();paths[0].write_text('{}')
        with self.assertRaises(ValueError):binder.bind(*paths)

    def test_fit_rejects_bad_capture_before_core(self):
        locked=self.root/'tool-freeze.json';chain.freeze(locked)
        args=[self.root/name for name in ('payload','short','long','prior','grid','training','freeze')]
        with patch.object(checked.audit,'validate_inputs',side_effect=ValueError('错误配置。')):
            with patch.object(checked.legacy,'fit') as core:
                with self.assertRaises(ValueError):checked.fit(*args,locked,self.root/'qemu',self.root/'native',self.root/'model.json')
                core.assert_not_called()

    def test_fit_rejects_changed_training_view_before_core(self):
        locked=self.root/'tool-freeze.json';chain.freeze(locked)
        args=[self.root/name for name in ('payload','short','long','prior','grid','training','freeze')]
        args[5].write_text(json.dumps(dict(records=[dict(cycles_per_call=1)])))
        with patch.object(checked.audit,'validate_inputs'),patch.object(checked.audit,'receipts'):
            with patch.object(checked.training_view,'extract',return_value=dict(records=[dict(cycles_per_call=2)])):
                with patch.object(checked.legacy,'fit') as core:
                    with self.assertRaises(ValueError):checked.fit(*args,locked,self.root/'qemu',self.root/'native',self.root/'model.json')
                    core.assert_not_called()


if __name__=='__main__':unittest.main()
