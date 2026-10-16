"""检查传输失败或归档不完整时不发布接收目录。"""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from common import digest,seal

spec=importlib.util.spec_from_file_location('fragment_fetch_test',Path(__file__).with_name('fragment-fetch.py'))
fetch=importlib.util.module_from_spec(spec);spec.loader.exec_module(fetch)


class FragmentFetchTests(unittest.TestCase):
    def setUp(self):
        self.temporary=tempfile.TemporaryDirectory();self.addCleanup(self.temporary.cleanup)
        self.root=Path(self.temporary.name);native=self.root/'native';native.mkdir()
        (native/'exit-status').write_text('0\n');(native/'samples.jsonl').write_text('{}\n');seal(native)
        self.archive=self.root/'archive.tar.gz'
        with tarfile.open(self.archive,'w:gz') as stream:stream.add(native,arcname='native')
        self.receipt=dict(archive_bytes=self.archive.stat().st_size,archive_sha256=digest(self.archive))
        self.destination=self.root/'received'

    def remote(self,argv,**kwargs):
        if argv[0]=='ssh':return subprocess.CompletedProcess(argv,0,json.dumps(self.receipt),'')
        shutil.copy2(self.archive,argv[-1]);return subprocess.CompletedProcess(argv,0)

    def test_complete_transfer_publishes_verified_directory(self):
        with patch.object(fetch.subprocess,'run',side_effect=self.remote):
            value=fetch.receive('musepipro-wg','/project/batch',self.destination)
        self.assertEqual(value['status'],'passed')
        self.assertTrue((self.destination/'native/SHA256SUMS').exists())
        self.assertFalse(self.destination.with_name('received.partial').exists())

    def test_scp_failure_does_not_publish(self):
        def fail(argv,**kwargs):
            if argv[0]=='ssh':return self.remote(argv,**kwargs)
            Path(argv[-1]).write_bytes(b'partial');raise subprocess.CalledProcessError(255,argv)
        with patch.object(fetch.subprocess,'run',side_effect=fail):
            with self.assertRaises(subprocess.CalledProcessError):fetch.receive('musepipro-wg','/project/batch',self.destination)
        self.assertFalse(self.destination.exists())
        self.assertTrue((self.root/'received.partial/transfer-failure.json').exists())

    def test_changed_archive_does_not_publish(self):
        self.receipt['archive_sha256']='0'*64
        with patch.object(fetch.subprocess,'run',side_effect=self.remote):
            with self.assertRaises(ValueError):fetch.receive('musepipro-wg','/project/batch',self.destination)
        self.assertFalse(self.destination.exists())


if __name__=='__main__':unittest.main()
