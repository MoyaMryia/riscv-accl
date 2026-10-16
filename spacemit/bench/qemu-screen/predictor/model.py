"""检查真实路径、依赖与缓存假设。"""
from collections import Counter, OrderedDict, defaultdict, deque
from fractions import Fraction
import re

X = 'zero ra sp gp tp t0 t1 t2 s0 s1 a0 a1 a2 a3 a4 a5 a6 a7 s2 s3 s4 s5 s6 s7 s8 s9 s10 s11 t3 t4 t5 t6'.split()
F = 'ft0 ft1 ft2 ft3 ft4 ft5 ft6 ft7 fs0 fs1 fa0 fa1 fa2 fa3 fa4 fa5 fa6 fa7 fs2 fs3 fs4 fs5 fs6 fs7 fs8 fs9 fs10 fs11 ft8 ft9 ft10 ft11'.split()
ALIASES = {name: 'x'+str(i) for i, name in enumerate(X)} | {name: 'f'+str(i) for i, name in enumerate(F)} | {'fp':'x8'}
REGISTER = re.compile(r'\b(?:x\d+|f\d+|v\d+|'+ '|'.join(sorted(ALIASES, key=len, reverse=True))+r')\b')
BRANCH = {'beq','bne','blt','bge','bltu','bgeu','c.beqz','c.bnez'}
LOAD = {'lb','lbu','lh','lhu','lw','lwu','ld','flh','flw','fld','c.lw','c.ld','c.lwsp','c.ldsp','c.fld','c.fldsp'}
STORE = {'sb','sh','sw','sd','fsh','fsw','fsd','c.sw','c.sd','c.swsp','c.sdsp','c.fsd','c.fsdsp'}
INTEGER = set('add addw addi addiw sub subw mul mulw mulh mulhu mulhsu div divu divw rem remu remw and andi or ori xor xori sll slli sllw slliw srl srli srlw srliw sra srai sraw sraiw slt slti sltu sltiu sh1add sh2add sh3add sh1add.uw sh2add.uw sh3add.uw add.uw lui auipc'.split())
COMPRESSED = set('c.add c.addw c.addi c.addiw c.addi16sp c.addi4spn c.mv c.li c.lui c.xor c.or c.and c.sub c.subw c.slli c.srli c.srai c.andi'.split())
VECTOR = set('vmv1r.v vmv2r.v vmv4r.v vmv8r.v vmv.v.i vmv.v.v vmv.v.x vmv.s.x vfmv.s.f vfmv.v.f vfmv.f.s vmv.x.s vfmul.vv vfmul.vf vfadd.vv vfadd.vf vfsub.vv vfsub.vf vfmacc.vv vfmacc.vf vfwmacc.vv vfwmacc.vf vfmadd.vv vfmadd.vf vfnmacc.vv vfnmacc.vf vfredusum.vs vfredosum.vs vadd.vi vadd.vv vadd.vx vand.vi vand.vv vsrl.vi vsll.vi vsub.vv vxor.vv vrgather.vv vfcvt.f.x.v vfcvt.x.f.v vfwcvt.f.f.v vfmerge.vfm vfslide1down.vf'.split())


def registers(text):
    return [ALIASES.get(r, r) for r in REGISTER.findall(text)]


def vector_context(event):
    if any(event.get(k) is None for k in ('vl','vtype','vlenb','vstart')):
        return None, 'vector-register-unavailable'
    value = event['vtype']
    if value >> 63 or value & ~255:
        return None, 'vector-type-illegal'
    exponent = value & 7
    if exponent == 4:
        return None, 'vector-lmul-reserved'
    exponent = exponent if exponent < 4 else exponent-8
    lmul = Fraction(2)**exponent
    sew = 8 << ((value >> 3) & 7)
    maximum = event['vlenb']*8*lmul/sew
    if sew > 64 or maximum < 1 or event['vl'] > maximum or event['vstart']:
        return None, 'vector-context-unsupported'
    return {'vl':event['vl'], 'sew':sew, 'lmul':str(lmul), 'vlmax':int(maximum),
            'tail_agnostic':bool(value & 64), 'mask_agnostic':bool(value & 128)}, None


def semantics(item, context):
    """对模型支持范围外的语义返回缺口，并标记依赖信息不完整。"""
    name, operands = item['objdump_mnemonic'], item['operands']
    words = operands.split(',')
    groups = [registers(word) for word in words]
    masked = bool(words and '.t' in words[-1])
    if masked: groups[-1] = []
    flat = [r for group in groups for r in group]
    read, write, gaps = set(), set(), []
    vector = name.startswith('v') and not name.startswith('vset')
    vload = bool(re.fullmatch(r'vl(?:e(?:8|16|32|64)|se(?:8|16|32|64)|[1248]re(?:8|16|32|64))\.v', name))
    vstore = bool(re.fullmatch(r'vs(?:e(?:8|16|32|64)|se(?:8|16|32|64)|[1248]r)\.v', name))
    segment = re.fullmatch(r'v([ls])s?seg([2-8])e(8|16|32|64)\.v',name)
    if segment:
        vload = segment[1]=='l'; vstore = segment[1]=='s'
    if name in BRANCH or name in STORE or vstore:
        read.update(flat)
    elif name in LOAD or vload or name in INTEGER or name in COMPRESSED or name in VECTOR or re.fullmatch(r'f(?:add|sub|mul|div|sqrt|madd|msub|nmadd|nmsub|sgnj|sgnjn|sgnjx|min|max|eq|lt|le)\.[hsd]', name) or name.startswith(('fcvt.','fmv.')):
        write.update(groups[0])
        read.update(flat[len(groups[0]):])
        if name.startswith(('vfmacc.','vfwmacc.','vfnmacc.','vfmadd.')) or name.startswith('c.') and name not in LOAD and name not in ('c.mv','c.li','c.lui','c.addi4spn'):
            read.update(write)
        if name == 'c.addi16sp':
            read.add('x2'); write.add('x2')
        if name == 'c.addi4spn': read.add('x2')
    elif name in ('vsetvli','vsetivli','vsetvl'):
        write.update(groups[0]); write.update(('vl','vtype'))
        read.update(flat[len(groups[0]):])
        if len(words) > 1 and words[1].strip() == 'zero' and words[0].strip() == 'zero': read.add('vl')
    elif name in ('c.j','jal','jalr','c.jr','c.jalr'):
        read.update(flat)
        if name in ('jal','jalr') and groups[0]:
            write.update(groups[0]); read.difference_update(groups[0])
        if name == 'c.jalr': write.add('x1')
    elif name in ('csrrs','csrrw'):
        write.update(groups[0]); read.update(flat[len(groups[0]):])
        csr = words[1].strip()
        read.add(csr)
        if name == 'csrrw' or words[-1].strip() != 'zero':
            write.add(csr); gaps.append('csr-side-effects-unmodeled')
    elif item['family'] == 'ime-known-encoding':
        gaps.append('ime-register-layout-unmodeled')
    else:
        gaps.append('instruction-semantics-unsupported:'+name)
    if vector:
        read.update(('vl','vtype'))
        whole_move = re.fullmatch(r'vmv([1248])r\.v',name)
        if whole_move or re.match(r'v[ls][1248]r',name):
            read.discard('vl');read.discard('vtype')
        if not context:
            gaps.append('vector-group-context-missing')
        else:
            lmul = Fraction(context['lmul'])
            width = max(1, int(lmul))
            # 整组访存独立于当前 LMUL。
            whole = re.match(r'v[ls]([1248])r', name)
            if whole: width = int(whole[1])
            if whole_move: width = int(whole_move[1])
            eew = re.search(r'e(8|16|32|64)\.v$',name) if vload or vstore else None
            if eew and not whole:
                emul = lmul*int(eew[1])/context['sew']
                if not Fraction(1,8) <= emul <= 8: gaps.append('memory-EMUL-unsupported')
                width = max(1,int(emul))
            for target in (read, write):
                for register in list(target):
                    if register.startswith('v') and register[1:].isdigit():
                        index = int(register[1:])
                        group_width = width
                        if name.startswith(('vfred','vred','vwred')):
                            if target is write or len(groups)>2 and register in groups[2]: group_width = 1
                        if name in ('vfmv.f.s','vmv.x.s','vmv.s.x','vfmv.s.f'): group_width = 1
                        if name.startswith('vfw'):
                            if name not in ('vfwcvt.f.f.v','vfwmacc.vv','vfwmacc.vf'):
                                gaps.append('widening-group-semantics-unmodeled')
                            elif target is write or name.startswith('vfwmacc.') and register in groups[0]:
                                group_width = max(1,int(lmul*2))
                        registers_used = group_width*(int(segment[2]) if segment else 1)
                        if index+registers_used > 32 or group_width > 1 and index % group_width:
                            gaps.append('vector-register-group-alignment')
                        target.update('v'+str(j) for j in range(index, min(32,index+registers_used)))
        if masked or name.startswith('vfmerge.'):
            read.add('v0')
            gaps.append('masked-lane-dependencies-conservative')
    # 部分向量写入保留旧值；保守依赖不用于周期求和。
    if vector and context and (not context['tail_agnostic'] or not context['mask_agnostic']):
        read.update(write)
    read.discard('x0'); write.discard('x0')
    return read, write, sorted(set(gaps))


def target(item):
    match = re.search(r'(?:^|,)\s*([0-9a-f]+)\s*<', item['operands'])
    return int(match[1],16) if match else None


def cfg(function):
    """对全部静态路径传播配置集合，不假定入口配置。"""
    items = function['instructions']
    by_pc = {i['address']:i for i in items}
    incoming = defaultdict(set)
    incoming[items[0]['address']].add('unknown-entry')
    todo = deque([items[0]['address']])
    backedges, calls, unresolved = set(), set(), set()
    while todo:
        pc = todo.popleft(); item = by_pc[pc]
        name, op = item['objdump_mnemonic'], item['operands']
        state = set(incoming[pc]); following = pc+item['bytes']
        if name in ('vsetvli','vsetivli'):
            match = re.search(r'\be(8|16|32|64),\s*(m(?:f[248]|[1248]))(?:,|$)',op)
            state = {match[0].rstrip(',')+'; AVL='+op.split(',')[1].strip()} if match else {'unknown-vset'}
        elif name == 'vsetvl': state = {'unknown-vsetvl'}
        successors = [following] if following in by_pc else []
        dest = target(item)
        if name in BRANCH or name == 'c.j' or name == 'jal' and op.startswith('zero,'):
            if name not in BRANCH: successors = []
            if dest in by_pc:
                successors.append(dest)
                if dest <= pc: backedges.add((pc,dest))
            else: unresolved.add(pc)
        elif name in ('jal','jalr','c.jalr'):
            calls.add(pc); state = {'unknown-after-call'}
        elif name == 'c.jr':
            successors = []
            if op.strip() != 'ra': unresolved.add(pc)
        for successor in successors:
            new = incoming[successor] | state
            if new != incoming[successor]:
                incoming[successor] = new; todo.append(successor)
    uses = [{ 'pc':i['address'], 'contexts':sorted(incoming[i['address']]),
              'ambiguous':len(incoming[i['address']]) != 1 or any(s.startswith('unknown') for s in incoming[i['address']])}
             for i in items if i['objdump_mnemonic'].startswith('v') and not i['objdump_mnemonic'].startswith('vset')]
    return {'vector_uses':uses, 'ambiguous_vector_uses':sum(i['ambiguous'] for i in uses),
            'backedges':sorted(backedges), 'calls':sorted(calls), 'unresolved_transfers':sorted(unresolved),
            'unreachable_pcs':sorted(set(by_pc)-set(incoming)),
            'limit':'static contexts retain AVL expressions; no scalar value proof; calls invalidate context'}


class Cache:
    def __init__(self, size, line, ways):
        if min(size,line,ways) <= 0 or size % (line*ways): raise ValueError('cache dimensions invalid')
        self.line, self.ways = line, ways
        self.sets = [OrderedDict() for _ in range(size//line//ways)]
        self.hits = self.misses = self.writebacks = 0

    def access(self, line, store):
        bucket = self.sets[line % len(self.sets)]
        hit = line in bucket
        dirty = bucket.pop(line, False) or store
        evicted = None
        if not hit and len(bucket) == self.ways:
            evicted, old_dirty = bucket.popitem(last=False)
            if not old_dirty: evicted = None
            else: self.writebacks += 1
        bucket[line] = dirty
        self.hits += hit; self.misses += not hit
        return hit, evicted


def cache_replay(threads, parameters, interleave):
    """只重放声明的虚拟地址假设，不预测周期。"""
    mapping = parameters['thread_to_core']
    clusters = parameters['core_to_cluster']
    line = parameters['line_bytes']
    if set(map(str,threads)) != set(mapping): raise ValueError('thread map differs from trace threads')
    if len(set(mapping.values())) != len(mapping): raise ValueError('one thread per target core is required')
    l1 = {core:Cache(parameters['l1_bytes'],line,parameters['l1_ways']) for core in mapping.values()}
    l2 = {clusters[str(core)]:Cache(parameters['l2_bytes'],line,parameters['l2_ways']) for core in mapping.values()}
    events = {cpu:[e for e in rows if e['kind']=='memory'] for cpu,rows in threads.items()}
    if interleave == 'serial':
        order = ((cpu,event) for cpu in sorted(events) for event in events[cpu])
    elif interleave == 'round-robin':
        def rounds():
            pending = {cpu:iter(events[cpu]) for cpu in sorted(events)}
            while pending:
                for cpu in list(pending):
                    event = next(pending[cpu],None)
                    if event is None: del pending[cpu]
                    else: yield cpu,event
        order = rounds()
    else: raise ValueError('target interleave is not declared')
    lower_fills = lower_writebacks = 0
    owners = defaultdict(set)
    for cpu,event in order:
        core = mapping[str(cpu)]; cluster = clusters[str(core)]
        address, size = event['address'],event['bytes']
        if size <= 0: raise ValueError('memory size invalid')
        for block in range(address//line,(address+size-1)//line+1):
            owners[block].add(cpu)
            hit, evict = l1[core].access(block,event['store'])
            if evict is not None:
                lower_hit, _ = l2[cluster].access(evict,True)
                lower_fills += not lower_hit
            if not hit:
                lower_hit, _ = l2[cluster].access(block,False)
                lower_fills += not lower_hit
    lower_writebacks = sum(c.writebacks for c in l2.values())
    return {'interleave':interleave, 'parameters':parameters,
            'l1':{str(k):{'hits':v.hits,'misses':v.misses,'dirty_evictions':v.writebacks} for k,v in l1.items()},
            'l2':{str(k):{'hits':v.hits,'misses':v.misses,'dirty_evictions':v.writebacks} for k,v in l2.items()},
            'lower_level_line_fills':lower_fills, 'lower_level_dirty_evictions':lower_writebacks,
            'cross_thread_virtual_lines':sum(len(v)>1 for v in owners.values()),
            'cycles':None,'DDR_bytes':None,
            'gaps':['virtual-address-indexing','cold-ROI-only; pre-ROI warmup unknown','no-coherence','no-prefetch',
                    'no-TLB','no-inclusive-eviction','no-latency-or-bandwidth','no-synchronization','no-compute-memory-overlap']}
