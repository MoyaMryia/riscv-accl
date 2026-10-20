"""小型 BERT 分类器的公共参数和数值运算。"""
import math

from classifier import LABELS, DEFAULT_MIN_SCORE

DEFAULTS = {'max_tokens': 256, 'epochs': 12, 'batch_size': 16, 'seed': 42,
            'encoder_lr': 5e-5, 'head_lr': 5e-4, 'weight_decay': 0.01, 'threads': 8}


def select_content(tokens, budget):
    """按固定预算保留开头、中间和结尾，保持 token 顺序。"""
    if len(tokens) <= budget:
        return list(tokens)
    head = (budget + 1) // 2
    middle = budget // 4
    tail = budget - head - middle
    start = head + (len(tokens) - head - tail - middle) // 2
    return list(tokens[:head]) + list(tokens[start:start + middle]) + list(tokens[-tail:])


def add_special(tokens, metadata):
    return [metadata['cls_token_id'], *select_content(tokens, metadata['max_tokens'] - 2), metadata['sep_token_id']]


def classify_embedding(weights, bias, embedding):
    """对已检查的向量计算线性投影和 softmax。"""
    logits = [offset + math.fsum(w * value for w, value in zip(row, embedding))
              for row, offset in zip(weights, bias)]
    peak = max(logits)
    exponentials = [math.exp(value - peak) for value in logits]
    denominator = sum(exponentials)
    scores = [value / denominator for value in exponentials]
    index = max(range(len(scores)), key=scores.__getitem__)
    return {'category': LABELS[index], 'score': scores[index],
            'scores': dict(zip(LABELS, scores)), 'logits': logits}
