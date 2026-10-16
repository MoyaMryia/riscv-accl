"""执行区分结果就绪与标量重复写入间隔的有效时序模型。"""
from functools import lru_cache

KINDS=('add','mul','load','vadd','ime','vload','branch')


@lru_cache(maxsize=1024)
def compile_ops(ops):
    names=sorted({register for _,reads,writes in ops for register in reads+writes}|{'ctr'})
    index={name:i for i,name in enumerate(names)}
    result=[(kind,tuple(index[r] for r in reads),tuple(index[r] for r in writes)) for kind,reads,writes in ops]
    result.extend([(0,(index['ctr'],),(index['ctr'],)),(6,(index['ctr'],),())])
    return tuple(result),len(names)


def prepare_parameters(p):
    latency=[p['latency'][kind] for kind in KINDS[:6]]+[1]
    occupancy=[p['occupancy'][kind] for kind in KINDS[:6]]+[1]
    bypass=[[latency[producer]]*7 for producer in range(7)]
    for key,value in p['bypass'].items():
        producer,consumer=key.split(':')
        bypass[KINDS.index(producer)][KINDS.index(consumer)]=value
    gap=[[0]*7 for _ in range(7)]
    for key,value in p['vector_gap'].items():
        producer,consumer=key.split(':')
        gap[KINDS.index(producer)][KINDS.index(consumer)]=value
    pairs=[[False]*7 for _ in range(7)]
    for key in p.get('forbidden_pairs',[]):
        producer,consumer=key.split(':')
        pairs[KINDS.index(producer)][KINDS.index(consumer)]=True
    write_gap=[[0]*7 for _ in range(7)]
    for key,value in p.get('write_gap',{}).items():
        producer,consumer=key.split(':')
        write_gap[KINDS.index(producer)][KINDS.index(consumer)]=value
    return (p['width'],p['scalar_units'],p['lsu_units'],p['waw'],p['read_hold_ime'],
            p.get('branch_boundary_gap',1),latency,occupancy,bypass,gap,pairs,
            (0,4 if p.get('separate_multiply',False) else 0,1,2,2 if p['shared_vector'] else 3,1,0),p.get('arithmetic_queue_depth',0),p.get('multiply_units',1),p.get('waw_policy','pending'),write_gap)


def compiled(record):
    return compile_ops(tuple((KINDS.index(op['kind']),tuple(op['reads']),tuple(op['writes'])) for op in record['instructions']))


def execute(program,parameters,loops=32,detect_period=False):
    if loops<8 or loops%2:
        raise ValueError('循环数量必须为不小于 8 的偶数。')
    ops,registers=program
    width,scalar,lsu,waw,hold,boundary,latency,occupancy,bypass,gap,pairs,groups,queue_depth,multiply_units,waw_policy,write_gap=parameters
    resources=[[0]*scalar,[0]*lsu,[0],[0],[0]*multiply_units]
    ready=[0]*registers
    writers=[-1]*registers
    written=[0]*registers
    read_until=[0]*registers
    clock=used=halfway=0
    last_vector=-1
    last_vector_time=0
    last_kind=-1
    seen={}
    arithmetic_queue=[]
    maximum_bypass=[max(max(row),max(write_gap[i])) for i,row in enumerate(bypass)]
    maximum_gap=[max(row) for row in gap]
    for iteration in range(loops):
        if detect_period:
            key=(used,last_kind,last_vector,tuple(sorted(t-clock for t in arithmetic_queue if t>clock)),
                max(0,last_vector_time+maximum_gap[last_vector]-clock) if last_vector>=0 else 0,
                tuple(tuple(sorted(max(0,t-clock) for t in pool)) for pool in resources),
                tuple(max(0,t-clock) for t in ready),tuple(writers),
                tuple(max(0,written[i]+maximum_bypass[k]-clock) if k>=0 else 0 for i,k in enumerate(writers)),
                tuple(max(0,t-clock) for t in read_until))
            if key in seen:
                previous_iteration,previous_clock=seen[key]
                return (clock-previous_clock)/(iteration-previous_iteration)
            seen[key]=iteration,clock
        if iteration==loops//2:
            halfway=clock
        for kind,reads,writes in ops:
            queued=queue_depth>0 and kind in (3,4)
            if queued:
                if used==width or (used and last_kind>=0 and pairs[last_kind][kind]):
                    clock+=1
                    used=0
                arithmetic_queue=[t for t in arithmetic_queue if t>clock]
                if len(arithmetic_queue)>=queue_depth:
                    clock=min(arithmetic_queue)
                    used=0
                    arithmetic_queue=[t for t in arithmetic_queue if t>clock]
            pool=resources[groups[kind]]
            if len(pool)>1:
                pool.sort()
            available=max(clock,pool[-1] if kind==5 else pool[0])
            for register in reads:
                producer=writers[register]
                if producer>=0:
                    available=max(available,written[register]+bypass[producer][kind])
            for register in writes:
                if kind in (0,1,2) and writers[register] in (0,1,2):
                    available=max(available,written[register]+write_gap[writers[register]][kind])
                elif waw:
                    available=max(available,ready[register]-latency[kind] if waw_policy=='completion' or (waw_policy=='scalar-completion' and kind in (0,1,2,6)) else ready[register])
                available=max(available,read_until[register])
            if kind in (3,4,5) and last_vector>=0:
                available=max(available,last_vector_time+gap[last_vector][kind])
            if not queued and available==clock and (used==width or (used and last_kind>=0 and pairs[last_kind][kind])):
                available+=1
            if not queued and available!=clock:
                used=0
                clock=available
            started=available if queued else clock
            if queued:
                arithmetic_queue.append(started+latency[kind])
            if kind==5:
                for index in range(len(pool)):
                    pool[index]=started+occupancy[kind]
            else:
                pool[0]=started+occupancy[kind]
            for register in writes:
                ready[register]=started+latency[kind]
                writers[register]=kind
                written[register]=started
            if kind==4:
                for register in reads:
                    read_until[register]=max(read_until[register],started+hold)
            if kind in (3,4,5):
                last_vector=kind
                last_vector_time=started
            used+=1
            last_kind=kind
            if kind==6 and boundary:
                clock+=boundary
                used=0
    if detect_period:
        raise ValueError('在指定循环数量内未找到稳态周期。')
    return (clock-halfway)/(loops//2)


def predict(record,parameters,loops=32):
    return execute(compiled(record),prepare_parameters(parameters),loops)


def steady(program,parameters):
    return execute(program,parameters,512,detect_period=True)
