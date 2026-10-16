"""检查冻结工具身份、完整收据与轨迹配置身份。"""
import importlib.util
from pathlib import Path
from common import digest,read

HERE=Path(__file__).resolve().parent
CPU='max,vlen=256,elen=64,vext_spec=v1.0'
spec=importlib.util.spec_from_file_location('fragment_toolchain',HERE/'fragment-toolchain.py')
toolchain=importlib.util.module_from_spec(spec);spec.loader.exec_module(toolchain)


def receipts(root):
    root=Path(root).resolve();listed={}
    for line in (root/'SHA256SUMS').read_text().splitlines():
        identity,name=line.split('  ',1);path=(root/name).resolve()
        if not path.is_relative_to(root) or digest(path)!=identity:
            raise ValueError('输入收据重复、越界或身份不同。')
        canonical=str(path.relative_to(root))
        if canonical in listed:raise ValueError('输入收据重复、越界或身份不同。')
        listed[canonical]=identity
    actual={str(path.relative_to(root)) for path in root.rglob('*') if path.is_file() and path.name!='SHA256SUMS'}
    if not listed or set(listed)!=actual:raise ValueError('输入收据为空或文件覆盖不完整。')


def capture(root,plan,binary_sha256):
    root=Path(root);receipts(root);data=read(root/'result.json')
    cases=[row['id'] for row in plan['cases']];kernels=[row['id'] for row in plan['kernels']]
    expected={(case,kernel) for case in cases for kernel in kernels}
    count=data['trace_calls']
    if type(count) is not int or not 0<count<=64:raise ValueError('调用循环次数无效。')
    if data['status']!='selected-complete-invocations-audited' or data['binary_sha256']!=binary_sha256:
        raise ValueError('轨迹状态或 ELF 身份不同。')
    if len(data['selected_cases'])!=len(cases) or set(data['selected_cases'])!=set(cases):
        raise ValueError('轨迹配置缺失或重复。')
    records={(row['case'],row['kernel']):row for row in data['records']}
    if len(records)!=len(data['records']) or set(records)!=expected:
        raise ValueError('轨迹单元缺失或重复。')
    for name in ('fragment-invocation.py','fragment-call.py','fragment-trace.c'):
        if data['tool_files'][name]!=digest(HERE/name):raise ValueError('轨迹采集或解码工具身份不同。')
    if data['plugin_sha256']!=digest(root/'trace.so'):raise ValueError('轨迹插件身份不同。')
    for ci,case in enumerate(cases):
        for ki,kernel in enumerate(kernels):
            name=case+'-'+kernel;row=records[(case,kernel)]
            command=read(root/(name+'-command.json'))
            suffix=['trace',str(ci),str(ki),'17',str(count)]
            if (len(command)!=13 or command[1:3]!=['-cpu',CPU] or command[3]!='-plugin'
                    or command[6:11]!=suffix or command[12]!='exact'
                    or Path(command[5]).name!='fragment' or Path(command[11]).name!=name+'.bin'):
                raise ValueError('轨迹命令与配置、实现、种子或调用次数不同。')
            audit=row['audit'];trace=root/(name+'-cpu0.jsonl')
            if (audit['status']!='complete-invocation-audited' or audit['symbol']!='fragment_repeat'
                    or audit['binary_sha256']!=binary_sha256 or audit['trace_sha256']!=digest(trace)):
                raise ValueError('轨迹记录与完整调用文件身份不同。')
    return data


def validate(model,payload,short,long,freeze=None):
    model=Path(model);frozen=read(model)
    freeze=Path(freeze) if freeze else model.with_name('pre-native-freeze.json')
    if digest(freeze)!=frozen['pre_native_freeze_sha256']:raise ValueError('采集前固定收据身份不同。')
    fixed=read(freeze)
    if (digest(HERE/'fragment-fit.py')!=frozen['fit_tool_sha256']
            or frozen['fit_tool_sha256']!=fixed['fit_tool_sha256']):
        raise ValueError('轨迹转换与估计工具不属于冻结模型。')
    for name in ('fragment-state.py','fragment-invocation.py'):
        if digest(HERE/name)!=fixed['tools'][name]:raise ValueError('时序引擎或解码器不属于冻结模型。')
    if 'runtime_binding' not in frozen:
        raise ValueError('模型缺少完整工具依赖绑定。必须从封存包发布绑定版本。')
    toolchain.verify(frozen['runtime_binding']['tools'])
    validate_inputs(payload,short,long)


def validate_inputs(payload,short,long):
    """拟合与预测共用完整输入核验，先核验全部单元。"""
    receipts(payload);plan=read(Path(payload)/'input-plan.json')
    cases=[row['id'] for row in plan['cases']];kernels=[row['id'] for row in plan['kernels']]
    if not cases or not kernels or len(set(cases))!=len(cases) or len(set(kernels))!=len(kernels) or plan['baseline'] not in kernels:
        raise ValueError('输入计划身份无效或重复。')
    identity=digest(Path(payload)/'fragment')
    a=capture(short,plan,identity);b=capture(long,plan,identity)
    if a['trace_calls']>=b['trace_calls']:raise ValueError('调用差值次数必须递增。')
    for key in ('qemu_sha256','plugin_sha256','plugin_header_sha256','tool_files'):
        if a[key]!=b[key]:raise ValueError('两组轨迹的采集工具身份不同。')
