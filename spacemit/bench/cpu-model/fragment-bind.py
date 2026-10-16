"""用封存包核验历史核心模块，再发布具有完整依赖身份的新模型。"""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
from pathlib import Path
import tarfile
from common import digest,read,write

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('fragment_toolchain',HERE/'fragment-toolchain.py')
toolchain=importlib.util.module_from_spec(spec);spec.loader.exec_module(toolchain)
CORE=('common.py','binary-input.py','fragment-check.py','fragment-invocation.py','fragment-state.py','fragment-fit.py')


def bind(model,archive,receipt,output):
    if Path(output).exists():raise ValueError('绑定模型输出已经存在。')
    archive=Path(archive);entries={}
    for line in Path(receipt).read_text().splitlines():
        identity,name=line.split('  ',1)
        if name in entries:raise ValueError('封存收据条目重复。')
        entries[name]=identity
    if entries.get(archive.name)!=digest(archive):raise ValueError('封存包与指定收据不同。')
    with tarfile.open(archive,'r:gz') as stream:
        members={}
        for member in stream.getmembers():
            if member.name in members:raise ValueError('封存包成员重复。')
            members[member.name]=member
        def content(name):
            member=members.get('portable/'+name)
            if member is None or not member.isfile():raise ValueError('封存包成员缺失或不是普通文件。')
            with stream.extractfile(member) as source:return source.read()
        if content('frozen-model.json')!=Path(model).read_bytes():raise ValueError('模型不属于指定封存包。')
        sums={}
        for line in content('SHA256SUMS').decode().splitlines():
            identity,name=line.split('  ',1)
            if name in sums:raise ValueError('包内收据条目重复。')
            sums[name]=identity
        for name in ('frozen-model.json',*('tools/'+name for name in CORE)):
            identity=hashlib.sha256(content(name)).hexdigest()
            if sums.get(name)!=identity:raise ValueError('包内核心文件与收据不同。')
            if name.startswith('tools/') and digest(HERE/Path(name).name)!=identity:
                raise ValueError('当前核心模块与封存版本不同：'+name)
    result=read(model)
    if 'runtime_binding' in result:raise ValueError('模型已经具有工具绑定。')
    result['runtime_binding']=dict(kind='post-measurement-integrity-check',tools=toolchain.identities(),
        source_model_sha256=digest(model),source_archive_sha256=digest(archive),
        source_receipt_sha256=digest(receipt),recorded_at_utc=datetime.now(timezone.utc).isoformat(),
        original_pre_native_tools_extended=False,parameters_changed=False)
    write(output,result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('model','archive','receipt','output'):parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();bind(args.model,args.archive,args.receipt,args.output)
