import json,hashlib,re
from pathlib import Path
namespace={}
source=Path(__file__).with_name('review-functions-source.py').read_text().split("b=raw/")[0]
exec(compile(source,'previous-review-functions','exec'),namespace)
root=Path('spacemit/reports/raw/k1-local-candidates-B1-r2-repeat1-20261009-141200');result=json.loads((root/'repeat-1/result.json').read_text());summary=json.loads((root/'summary.json').read_text());initial=Path('spacemit/reports/raw/k1-local-candidates-B1-r2-model-result-20261009-130000');pilot=json.loads((initial/'summary.json').read_text());assert summary['identity']==pilot['identity'];assert result['independent_repeat']==1 and result['status']=='eligible' and len(result['comparisons'])==8
assert namespace['cold'](root,Path('repeat-1'),result['comparisons'],'B0','B1',True)==32
commands=json.loads((root/'commands.json').read_text());assert len(commands)==32
for command in commands:
 label=command['label'];runtime=command['runtime'];arm=int('-B1-' in label);assert runtime['SPINE_K1_FA_GQA']==str(arm);assert all(runtime[k]=='0' for k in ['SPINE_K1_FA_DECODE','SPINE_GDN_PREFILL','SPINE_K1_SSM_CONV','SPINE_K1_CONV_SILU']);assert runtime['SPINE_K1_TRACE']=='1';assert runtime['SPINE_FA_WIDE_TILE']=='1' and runtime['SPINE_FA_K1_LAYOUT']=='0' and runtime['SPINE_K1_GEMM_ROUTE']=='3';argv=command['argv'];assert argv[argv.index('--threads')+1]=='4'
for path in (root/'repeat-1').glob('*.jsonl'):
 rows=[json.loads(line) for line in path.read_text().splitlines()];config=next(x for x in rows if x['kind']=='config');assert config['capture_token_ids'] and config['ignore_eos'] and config['mode']=='plain' and config['parallel']==1
 old=[json.loads(line) for line in (initial/'cold'/path.name).read_text().splitlines()];now=next(x for x in rows if x['kind']=='measurement');before=next(x for x in old if x['kind']=='measurement');assert now['prompt_token_sha256']==before['prompt_token_sha256'];assert now['results'][0]['token_ids']==before['results'][0]['token_ids']
primary={x['model']:x['metrics']['decode'] for x in result['comparisons'] if x['tokens']==2048 and x['outputs']==65}
review={'状态':'第一轮八项冷请求比较通过','独立轮次':1,'冷请求数':32,'全部门槛独立重算':True,'完整输入哈希及输出词元与初筛相同':True,'冷缓存与固定配置通过':True,'实际 B1 开关与四个工作线程通过':True,'主指标':primary,'身份与初筛一致':True,'限制':'每臂每配置两次请求，不能证明总体置信区间。路径日志开销计入计时。第二轮、完整回答和最终基线复核待完成。'}
(root/'local-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2)+'\n');print(json.dumps(review,ensure_ascii=False,indent=2))
