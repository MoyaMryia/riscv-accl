"""先核验完整输入和训练观测来源，再调用冻结 R4 拟合核心。"""
import argparse
from datetime import datetime,timezone
import importlib.util
from pathlib import Path
import tempfile
from common import digest,read,write

HERE=Path(__file__).resolve().parent


def load(name):
    spec=importlib.util.spec_from_file_location(name.replace('-','_'),HERE/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


audit=load('fragment-input-audit');toolchain=load('fragment-toolchain')
legacy=load('fragment-fit');training_view=load('fragment-training-view')


def fit(payload,short,long,prior,grid,training,freeze,tool_freeze,qemu,native,output):
    output=Path(output)
    if output.exists():raise ValueError('冻结模型输出已经存在。')
    locked=read(tool_freeze)
    if locked['status']!='fragment-toolchain-frozen':raise ValueError('工具清单没有冻结状态。')
    toolchain.verify(locked['tools'])
    audit.validate_inputs(payload,short,long)
    for root in (qemu,native):audit.receipts(root)
    with tempfile.TemporaryDirectory(prefix='fragment-fit-checked-') as temporary:
        temporary=Path(temporary)
        observed=training_view.extract(payload,qemu,native,temporary/'training.json')
        if observed!=read(training):raise ValueError('训练视图与原生证据重新提取结果不同。')
        result=legacy.fit(payload,short,long,prior,grid,training,freeze,temporary/'core-model.json')
        toolchain.verify(locked['tools'])
        result['runtime_binding']=dict(kind='checked-fit',tools=locked['tools'],
            tool_freeze_sha256=digest(tool_freeze),recorded_at_utc=datetime.now(timezone.utc).isoformat(),
            training_reextracted=True,input_identity_audited=True,
            native_receipt_sha256=digest(Path(native)/'SHA256SUMS'),
            qemu_receipt_sha256=digest(Path(qemu)/'SHA256SUMS'))
        write(output,result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('payload','short','long','prior','grid','training','freeze','tool-freeze','qemu','native','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    fit(args.payload,args.short,args.long,args.prior,args.grid,args.training,args.freeze,args.tool_freeze,args.qemu,args.native,args.output)
