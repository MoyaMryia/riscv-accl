"""按完整动态调用顺序计算有限时序，不添加合成循环指令。"""
import math

ALU = {'lui','auipc','addi','slti','sltiu','xori','ori','andi','slli','srli','srai',
       'addiw','slliw','srliw','sraiw','add','sll','slt','sltu','xor','srl','or','and',
       'addw','sllw','srlw','sub','sra','subw','sraw','c.addi4spn','c.addi','c.addiw',
       'c.li','c.addi16sp','c.lui','c.srli','c.srai','c.andi','c.sub','c.xor','c.or',
       'c.and','c.subw','c.addw','c.slli','c.add','c.mv'}


def category(op):
    name = op['name']
    if op['control'] == 'branch':return 'branch'
    if op['control'] in ('direct','indirect'):return 'jump'
    if name in ALU:return 'add'
    if name in ('mul','mulw'):return 'mul'
    if name == 'vsetvli':return 'vset'
    if name in ('vmv.v.i','vmv.v.x'):return 'vmove'
    if name == 'vse8.v':return 'vstore'
    if 'memory_bytes' in op and not name.startswith('v'):
        return 'store' if op['store'] else 'load'
    raise ValueError('有限时序未覆盖指令：'+name)


def compile_trace(rows):
    """保存寄存器与实际重叠访存的依赖，缓存状态不在此步骤推断。"""
    names = sorted({r for row in rows for r in row['operation']['reads']+row['operation']['writes']})
    registers = {r:i for i,r in enumerate(names)}
    stores, loads, ops = {}, {}, []
    for index,row in enumerate(rows):
        op = row['operation'];kind = category(op)
        memory_dependencies = set()
        addresses = {item['address']+i for item in row['memory'] for i in range(item['bytes'])}
        if kind in ('load','store','vstore'):
            for address in addresses:
                if address in stores:
                    memory_dependencies.add((stores[address], 'store-store' if op['store'] else 'store-load'))
                if op['store']:
                    memory_dependencies.update((previous,'load-store') for previous in loads.get(address,()))
                    stores[address] = index
                    loads[address] = set()
                else:
                    loads.setdefault(address,set()).add(index)
        ops.append(dict(kind=kind,reads=tuple(registers[r] for r in op['reads']),
            writes=tuple(registers[r] for r in op['writes']),memory_dependencies=tuple(sorted(memory_dependencies)),
            memory_bytes=op.get('memory_bytes',0),vector_bytes=row.get('vl',0),
            vector_registers=1 << (row.get('vtype',0)&7) if kind=='vmove' else 0))
    return dict(ops=ops,registers=len(names))


def initial_parameters(prior):
    """旧参数只作为初始有效时序，不转移旧预测界限。"""
    return dict(width=prior['width'],scalar_units=prior['scalar_units'],lsu_units=prior['lsu_units'],
        multiply_units=prior.get('multiply_units',1),scalar_queue_depth=prior.get('scalar_queue_depth',0),
        scalar_capture=prior.get('scalar_capture','ready'),completion_order=prior.get('completion_order','resource'),
        waw_policy=prior.get('waw_policy','completion'),waw=prior['waw'],
        latency={k:prior['latency'][k] for k in ('add','mul','load')},
        occupancy={k:prior['occupancy'][k] for k in ('add','mul','load')},
        bypass=dict(prior['bypass']),write_gap=dict(prior.get('write_gap',{})),
        store_latency=1,store_occupancy=1,store_queue_depth=4,add_store_bypass=1,load_store_bypass=2,
        branch_gap=0,jump_gap=1,store_load_gap=1,store_store_gap=1,
        vector_bytes_per_cycle=32,vector_start=2,vector_move_per_register=1,vset_latency=2)


def validate(p):
    for key in ('width','scalar_units','lsu_units','multiply_units','store_queue_depth','vector_bytes_per_cycle'):
        if type(p[key]) is not int or p[key]<=0:raise ValueError('时序资源参数无效：'+key)
    if type(p['scalar_queue_depth']) is not int or p['scalar_queue_depth']<0:
        raise ValueError('标量队列深度无效。')
    if p['scalar_capture'] not in ('ready','execute') or p['completion_order'] not in ('none','resource','global'):
        raise ValueError('完成顺序或操作数捕获假设未覆盖。')
    if p['waw_policy'] not in ('pending','completion'):raise ValueError('重复写入假设未覆盖。')
    values = [p[k] for k in ('store_latency','store_occupancy','add_store_bypass','load_store_bypass',
        'branch_gap','jump_gap','store_load_gap','store_store_gap','vector_start','vector_move_per_register','vset_latency')]
    values += [value for key in ('latency','occupancy','bypass','write_gap') for value in p[key].values()]
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in values):
        raise ValueError('时序参数必须为非负有限数。')


def execute(program, p, events=None):
    validate(p)
    registers, ops = program['registers'], program['ops']
    ready=[0]*registers;written=[0]*registers;writers=[None]*registers;read_until=[0]*registers
    resources={'scalar':[0]*p['scalar_units'],'lsu':[0]*p['lsu_units'],
               'multiply':[0]*p['multiply_units'],'vector':[0]}
    completions={key:0 for key in resources};completions['global']=0
    scalar_queue=[];store_queue=[];starts=[];ends=[]
    clock=used=maximum_completion=0
    for index,op in enumerate(ops):
        kind=op['kind']
        if kind in ('add','mul','load'):
            latency=p['latency'][kind];occupancy=p['occupancy'][kind]
        elif kind=='store':latency=p['store_latency'];occupancy=p['store_occupancy']
        elif kind=='vstore':
            occupancy=max(1,math.ceil(op['memory_bytes']/p['vector_bytes_per_cycle']))
            latency=p['vector_start']+occupancy
        elif kind=='vmove':
            occupancy=max(1,op['vector_registers']*p['vector_move_per_register']);latency=p['vector_start']+occupancy
        elif kind=='vset':latency=p['vset_latency'];occupancy=1
        else:latency=occupancy=1
        group='lsu' if kind in ('load','store','vstore') else 'multiply' if kind=='mul' else 'vector' if kind in ('vmove','vset') else 'scalar'
        queued=kind in ('add','mul','load') and p['scalar_queue_depth']>0
        store_queued=kind in ('store','vstore')
        queue=store_queue if store_queued else scalar_queue
        depth=p['store_queue_depth'] if store_queued else p['scalar_queue_depth']
        if used>=p['width']:
            clock+=1;used=0
        if queued or store_queued:
            queue[:]=[t for t in queue if t>clock]
            if len(queue)>=depth:
                clock=min(queue);used=0
                queue[:]=[t for t in queue if t>clock]
        pool=resources[group];pool.sort();available=max(clock,pool[0]);captures=[]
        for register in op['reads']:
            producer=writers[register]
            if producer is not None:
                delay=p['latency'].get(producer,ready[register]-written[register])
                if kind in ('store','vstore') and producer in ('add','load'):
                    delay=p['add_store_bypass'] if producer=='add' else p['load_store_bypass']
                else:delay=p['bypass'].get(producer+':'+kind,delay)
                captured=max(clock,written[register]+delay)
            else:captured=clock
            available=max(available,captured);captures.append(captured)
        for register in op['writes']:
            producer=writers[register]
            if producer is not None:
                available=max(available,written[register]+p['write_gap'].get(producer+':'+kind,0))
                if p['waw']:
                    available=max(available,ready[register]-latency if p['waw_policy']=='completion' else ready[register])
            available=max(available,read_until[register])
        for previous,relation in op['memory_dependencies']:
            if relation=='store-load':
                available=max(available,ends[previous] if ops[previous]['kind']=='vstore' else starts[previous]+p['store_load_gap'])
            elif relation=='store-store':
                available=max(available,ends[previous] if ops[previous]['kind']=='vstore' else starts[previous]+p['store_store_gap'])
            else:available=max(available,starts[previous])
        completion_key='global' if p['completion_order']=='global' else group
        if p['completion_order']!='none':available=max(available,completions[completion_key]-latency)
        if not queued and not store_queued and available>clock:
            clock=available;used=0
        started=available;complete=started+latency
        if p['completion_order']!='none':completions[completion_key]=complete
        pool[0]=started+occupancy
        if queued or store_queued:queue.append(complete)
        for register in op['writes']:
            ready[register]=complete;written[register]=started;writers[register]=kind
        if queued or store_queued:
            for register,captured in zip(op['reads'],captures):
                read_until[register]=max(read_until[register],captured if p['scalar_capture']=='ready' else started)
        starts.append(started);ends.append(complete);maximum_completion=max(maximum_completion,complete)
        if events is not None:
            events.append(dict(instruction=index,kind=kind,dispatch=clock,execute=started,complete=complete))
        used+=1
        gap=p['branch_gap'] if kind=='branch' else p['jump_gap'] if kind=='jump' else 0
        if gap:
            clock+=gap;used=0
    return dict(return_cycles=clock+(used>0),drained_cycles=max(clock+(used>0),maximum_completion),
                instructions=len(ops),pending_at_return=max(0,maximum_completion-(clock+(used>0))))


def slope(short, long, counts, parameters):
    if len(counts)!=2 or not 0<counts[0]<counts[1]:raise ValueError('调用差值必须使用两个递增次数。')
    a=execute(short,parameters);b=execute(long,parameters)
    value=(b['return_cycles']-a['return_cycles'])/(counts[1]-counts[0])
    if value<=0:raise ValueError('完整调用周期差值必须为正数。')
    return dict(cycles_per_call=value,short=a,long=b,
                limits=['参数是有效时序假设，不是已确认的硬件结构。',
                        '当前热访存假设不预测缓存缺失、TLB、预取或全局内存可见性。'])
