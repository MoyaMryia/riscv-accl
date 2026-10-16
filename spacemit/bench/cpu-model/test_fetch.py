"""检查阶段证据只在完整核验后发布。"""
import importlib.util
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from common import digest

spec=importlib.util.spec_from_file_location('fetch',Path(__file__).with_name('fetch-stage.py'))
fetch=importlib.util.module_from_spec(spec);spec.loader.exec_module(fetch)


class FetchTests(unittest.TestCase):
    def test_valid_stage_publishes_once(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source/run-test';source.mkdir(parents=True)
            (source/'exit-status').write_text('0\n');(source/'phase').write_text('complete\n')
            (source/'SHA256SUMS').write_text(''.join(f'{digest(p)}  run-test/{p.name}\n' for p in sorted(source.iterdir())))
            archive=root/'stage.tar.gz'
            with tarfile.open(archive,'w:gz') as target:target.add(source,arcname='run-test')
            out=root/'out';out.mkdir()
            self.assertEqual(fetch.publish(archive,out,'test'),2)
            with self.assertRaises(FileExistsError):fetch.publish(archive,out,'test')

    def test_corrupt_receipt_does_not_publish(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source=root/'source/run-test';source.mkdir(parents=True)
            (source/'exit-status').write_text('0\n');(source/'phase').write_text('complete\n')
            (source/'SHA256SUMS').write_text('0'*64+'  run-test/phase\n')
            archive=root/'stage.tar.gz'
            with tarfile.open(archive,'w:gz') as target:target.add(source,arcname='run-test')
            out=root/'out';out.mkdir()
            with self.assertRaises(ValueError):fetch.publish(archive,out,'test')
            self.assertFalse((out/'run-test').exists())

    def test_link_does_not_publish(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);archive=root/'stage.tar.gz';info=tarfile.TarInfo('run-test/link');info.type=tarfile.SYMTYPE;info.linkname='/tmp'
            with tarfile.open(archive,'w:gz') as target:target.addfile(info)
            out=root/'out';out.mkdir()
            with self.assertRaises(ValueError):fetch.publish(archive,out,'test')
            self.assertFalse((out/'run-test').exists())


if __name__=='__main__':unittest.main()
