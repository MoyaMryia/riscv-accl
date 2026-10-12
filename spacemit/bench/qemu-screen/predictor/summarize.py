"""汇总真实候选、覆盖缺口和标定验收结果。"""
from collections import Counter
import json
from pathlib import Path

from analyze import load, sha, write


def summarize(traces,coverage,validation,out,native=None):
    result = {'schema':1,'automatic_performance_rejection':False,'candidates':[],
        'K1_prediction_accuracy':'not-accepted','inputs':{},'static_coverage':[]}
    lines = ['# K1 候选统一分析报告','','性能估算只辅助安排板端测量。',
             '性能结果用于安排投入和补测。','完整数值差异必须停止对应候选。','']
    for path in traces:
        result['inputs'][str(path.resolve())] = sha(path)
        trace = load(path)
        for case in trace['cases']:
            record = {'id':case['id'],'status':case['status'],'source':str(path),'arms':{},
                'K1_cycles':None,'K1_board_gain':None,'automatic_performance_rejection':False}
            lines += ['## '+case['id'],'','状态：'+case['status']+'。','']
            for arm,value in case['arms'].items():
                threads = list(value['threads'].values())
                gaps = Counter()
                for thread in threads: gaps.update(thread['gaps'])
                complete = all(not t['end']['truncated'] for t in threads)
                summary = {'recorded_instructions':sum(t['instructions'] for t in threads),
                    'total_instructions':sum(t['end']['instructions'] for t in threads),
                    'complete_trace':complete,'load_bytes':sum(t['load_bytes'] for t in threads),
                    'store_bytes':sum(t['store_bytes'] for t in threads),'distinct_thread_ids':len(threads),
                    'gaps':dict(gaps),'dump_sha256':value['dump_sha256'],
                    'image_sha256':value.get('image_sha256',value['elf_sha256']),
                    'mca_statuses':dict(Counter(t['mca']['status'] for t in threads if 'mca' in t)),
                    'cache_scenarios':value.get('cache_scenarios',[])}
                record['arms'][arm] = summary
                label = '控制' if arm=='control' else '候选'
                lines += [f'{label}臂记录 {summary["recorded_instructions"]} 条指令，具有 {len(threads)} 个线程标识。',
                    ('轨迹覆盖完整热点执行。' if complete else '轨迹达到预先声明的上限，未覆盖全部热点执行。'),
                    f'已记录读取 {summary["load_bytes"]} 字节，写入 {summary["store_bytes"]} 字节。','']
                if gaps: lines += ['覆盖缺口：'+ '、'.join(sorted(gaps))+'。','']
            if 'control' in record['arms'] and 'candidate' in record['arms']:
                a,b = record['arms']['control'],record['arms']['candidate']
                record['full_dump_match'] = a['dump_sha256']==b['dump_sha256']
                if a['complete_trace'] and b['complete_trace'] and case['id'].startswith('conv-'):
                    record['instruction_change_percent'] = 100*(b['total_instructions']/a['total_instructions']-1)
                    lines += [f'候选热点指令变化为 {record["instruction_change_percent"]:+.4f}%。','']
                lines += ['完整转储一致。' if record['full_dump_match'] else '完整转储不一致，必须检查该次停止记录。','']
            result['candidates'].append(record)
    if coverage:
        value = load(coverage)
        result['inputs'][str(coverage.resolve())] = sha(coverage)
        result['static_coverage'] = value['records']
        lines += ['## 实际库的静态控制流检查','','静态检查不提供函数耗时。','',
                  '| 函数 | 静态指令 | 配置不明确的向量位置 | 回边 | 调用 |',
                  '| --- | ---: | ---: | ---: | ---: |']
        for record in value['records']:
            c = record['cfg']
            lines.append(f'| `{record["symbol"]}` | {record["static_instructions"]} | {c["ambiguous_vector_uses"]} | {len(c["backedges"])} | {len(c["calls"])} |')
        lines += ['','入口、调用后的配置和无法解析的跳转必须保留为缺口。',
                  '向量长度的标量表达式尚未获得静态值证明。','IME 点积的寄存器布局和 X60 写调度仍未覆盖。','']
    if validation:
        value = load(validation);result['validation'] = value
        result['inputs'][str(validation.resolve())] = sha(validation)
        lines += ['## 独立小内核误差检查','',f'验收状态：{value["status"]}。',
            '本次数据只代表固定指令混合小内核，不代表真实算子或完整模型。','']
        if 'cycle_error_median' in value:
            lines += [f'周期误差中位数为 {100*value["cycle_error_median"]:.4f}%，最大值为 {100*value["cycle_error_max"]:.4f}%。',
                f'相对变化误差最大值为 {value["relative_change_error_max_percentage_points"]:.4f} 个百分点。',
                f'方向错误为 {value.get("direction_errors",value["ranking_errors"])} 个，候选间排序错误为 {value.get("pair_order_errors",0)} 个。',
                f'观测误淘汰风险为 {value["false_rejection_risks"]} 个。','',
                '| 测试组 | 实测变化 | 模型变化 | 变化误差／百分点 |',
                '| --- | ---: | ---: | ---: |']
            for pair in value['pairs']:
                lines.append(f'| `{pair["control"]}` | {100*pair["measured_gain"]:.4f}% | {100*pair["predicted_gain"]:.4f}% | {pair["error_percentage_points"]:.4f} |')
            lines += ['','误差区间使用本次最大误差，不是总体置信区间。',
                '部分有效长度没有对应的 MCA 时序参数。','模型未通过本协议验收，不能自动淘汰任何候选。','']
    if native:
        value = load(native)
        result['inputs'][str(native.resolve())] = sha(native)
        result['native_prototype_screen'] = value
        lines += ['## 板端真实原型短测','','本节使用独立的真实原型夹具，不属于上述小内核测试集。',
            '卷积使用既有原型可执行文件，不能把其耗时直接对应另一夹具的轨迹窗口。',
            'B2 计时对照使用同一候选共享库的 tile0 路径。',
            'B2 四个工作线程仅可使用 CPU 0 至 CPU 3，但未启用 strict_cpu。',
            'IME 只测热输入局部加载函数及其完整输出存储，不代表完整内核。',
            '每臂六个样本，全部候选均保留。','',
            '| 原型 | 形状 | 候选臂 | 时间降幅 | 对照极差占比 |',
            '| --- | --- | ---: | ---: | ---: |']
        for item in value['results']:
            g = item.get('comparison',item.get('gate'))
            lines.append(f'| {item["candidate"]} | {item["a"]}/{item["b"]} | {item["arm"]} | '
                f'{g["reduction_percent"]:.4f}% | {g["control_range_percent"]:.4f}% |')
        lines += ['','正降幅表示候选更快，负降幅表示候选更慢。',
            '单组短测不能替代多形状性能评估。',
            'IME 局部夹具的判定不能替代完整 IME 内核验收。',
            '本节不改变模型验收状态，也不触发自动发布或自动性能淘汰。','']
    lines += ['## 实现与限制','','已实现：实际二进制身份、静态配置传播、逐线程轨迹、寄存器依赖和地址重叠检查。',
        '已实现：私有一级缓存和簇共享二级缓存的声明式重放。',
        '缓存容量来自 K1 手册，其他缓存参数仍是假设。',
        '缓存统计不能直接转换为 DDR 流量或周期。',
        '待验证：完整 IME 时序、缓存参数、物理地址、预热、同步、一致性和执行重叠。',
        '未实现：经过标定的 gem5 后端和完整系统预测。',
        '单项通过后仍须验证组合，不能相加单项收益。','']
    write(out/'suite.json',result)
    (out/'report.md').write_text('\n'.join(lines)+'\n')
    return result
