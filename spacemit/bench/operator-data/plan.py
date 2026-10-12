#!/usr/bin/env python3
"""先固定形状分组，再采集训练数据。"""
import itertools
import json
import random
import sys

rng = random.Random(2026101201)
families = {
    'ime': list(itertools.product([96,160,224,320,480,768,1152,1792,2304,3584,4608], [16,32,48,64,96,128])),
    'conv': list(itertools.product([160,320,640,896,1280,1792,2560,3584,4608,5632,6656,9216], [2,5,7,11,17,23,40,56])),
}
plan = {'schema': 1, 'seed': 2026101201, 'scope': 'hot-repeated-input', 'repeats': 7, 'lengths': 3, 'groups': []}
for family, pool in families.items():
    rng.shuffle(pool)
    for index, shape in enumerate(pool[:36]):
        split = 'train' if index < 8 else 'calibration' if index < 27 else 'test'
        plan['groups'].append({'id': f'{family}-{index:02d}', 'family': family, 'shape': shape,
            'split': split, 'threads': [1,4], 'seed': 12000 + index*13, 'padding': (index%2)*3 if family=='conv' else 0})
rng.shuffle(plan['groups'])
with open(sys.argv[1], 'x') as handle:
    json.dump(plan, handle, indent=2)
    handle.write('\n')
