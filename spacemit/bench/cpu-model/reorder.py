"""保留寄存器依赖顺序，并按操作类型选择就绪指令。"""
import heapq


def dependencies(ops):
    writers,readers={},{}
    edges=[]
    for index,op in enumerate(ops):
        previous=set()
        for register in op['reads']:
            if register in writers:
                previous.add(writers[register])
        for register in op['writes']:
            if register in writers:
                previous.add(writers[register])
            previous.update(readers.get(register,set()))
        previous.discard(index)
        edges.append(previous)
        for register in op['writes']:
            readers[register]=set()
            writers[register]=index
        for register in op['reads']:
            if register not in op['writes']:
                readers.setdefault(register,set()).add(index)
    return edges


def by_kind(ops,kinds):
    edges=dependencies(ops)
    followers=[[] for _ in ops]
    counts=[len(previous) for previous in edges]
    ready=[]
    for index,previous in enumerate(edges):
        for parent in previous:
            followers[parent].append(index)
        if not previous:
            heapq.heappush(ready,(kinds.index(ops[index]['kind']),index))
    order=[]
    while ready:
        _,index=heapq.heappop(ready)
        order.append(index)
        for child in followers[index]:
            counts[child]-=1
            if not counts[child]:
                heapq.heappush(ready,(kinds.index(ops[child]['kind']),child))
    if len(order)!=len(ops):
        raise ValueError('依赖图包含循环。')
    position={index:i for i,index in enumerate(order)}
    if any(position[parent]>=position[index] for index,previous in enumerate(edges) for parent in previous):
        raise ValueError('重排改变依赖顺序。')
    return [ops[index] for index in order],order
