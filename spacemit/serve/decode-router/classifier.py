"""字符 n-gram 轻量分类器。"""
import gzip
import json
import math
import random
import zlib

LABELS = ('code', 'qa', 'text', 'document')
DEFAULT_MIN_SCORE = 0.65
WINDOW = 256
FORMAT_VERSION = 1
MAX_DIMENSIONS = 65536
MAX_MODEL_BYTES = 8 * 1024 * 1024


def _features(text, dimensions):
    """生成归一化稀疏字符特征。"""
    sample = (text if len(text) <= 2 * WINDOW else text[:WINDOW] + '\n' + text[-WINDOW:]).casefold()
    values = {}
    for size in (2, 3, 4):
        for start in range(len(sample) - size + 1):
            gram = sample[start:start + size].encode('utf-8')
            index = zlib.crc32(gram) % dimensions
            values[index] = values.get(index, 0.0) + 1.0
    norm = math.sqrt(sum(value * value for value in values.values()))
    if norm:
        return {index: value / norm for index, value in values.items()}
    return {}


def _softmax(logits):
    """计算稳定的 softmax 概率。"""
    peak = max(logits)
    values = [math.exp(value - peak) for value in logits]
    total = sum(values)
    return [value / total for value in values]


def train(rows, epochs=80, dimensions=4096, seed=42):
    """用已检查的样本训练四类线性分类器。"""
    if type(dimensions) is not int or not 1 <= dimensions <= MAX_DIMENSIONS:
        raise ValueError('训练维度无效')
    if type(epochs) is not int or not 1 <= epochs <= 10000:
        raise ValueError('训练轮数无效')
    weights = [[0.0] * dimensions for _ in LABELS]
    bias = [0.0] * len(LABELS)
    examples = [(_features(row['text'], dimensions), LABELS.index(row['label'])) for row in rows]
    rng = random.Random(seed)
    losses = []
    for epoch in range(epochs):
        order = list(range(len(examples)))
        rng.shuffle(order)
        rate = 0.15 / (1.0 + epoch * 0.02)
        total_loss = 0.0
        for item in order:
            features, target = examples[item]
            logits = [bias[label] + sum(weights[label][index] * value
                                        for index, value in features.items())
                      for label in range(len(LABELS))]
            probabilities = _softmax(logits)
            total_loss -= math.log(max(probabilities[target], 1e-15))
            for label in range(len(LABELS)):
                error = (1.0 if label == target else 0.0) - probabilities[label]
                bias[label] += rate * error
                for index, value in features.items():
                    weights[label][index] += rate * error * value
        losses.append(total_loss / len(examples) if examples else 0.0)
    sparse = [{str(index): value for index, value in enumerate(row) if value}
              for row in weights]
    return {
        'format': FORMAT_VERSION,
        'labels': list(LABELS),
        'dimensions': dimensions,
        'window': WINDOW,
        'min_score': DEFAULT_MIN_SCORE,
        'weights': sparse,
        'bias': bias,
        'loss_history': losses,
    }


def predict(model, text):
    """返回类别、最高分和各类分数。"""
    features = _features(text, model['dimensions'])
    logits = []
    for label in range(len(LABELS)):
        row = model['weights'][label]
        logits.append(model['bias'][label] + sum(
            row.get(str(index), 0.0) * value for index, value in features.items()))
    probabilities = _softmax(logits)
    scores = dict(zip(LABELS, probabilities))
    best = max(range(len(LABELS)), key=probabilities.__getitem__)
    return {'category': LABELS[best], 'score': probabilities[best], 'scores': scores}


def _validate_model(model):
    """检查外部模型的格式、范围和数值。"""
    if not isinstance(model, dict) or type(model.get('format')) is not int or model['format'] != FORMAT_VERSION:
        raise ValueError('模型格式无效')
    dimensions = model.get('dimensions')
    if type(dimensions) is not int or not 1 <= dimensions <= MAX_DIMENSIONS:
        raise ValueError('模型维度无效')
    if model.get('labels') != list(LABELS) or model.get('window') != WINDOW:
        raise ValueError('模型元信息无效')
    threshold = model.get('min_score')
    if type(threshold) not in (int, float) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('模型阈值无效')
    bias, weights = model.get('bias'), model.get('weights')
    if not isinstance(bias, list) or len(bias) != len(LABELS):
        raise ValueError('模型偏置形状无效')
    if not isinstance(weights, list) or len(weights) != len(LABELS):
        raise ValueError('模型权重形状无效')
    for value in bias:
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError('模型偏置数值无效')
    for index, row in enumerate(weights):
        if not isinstance(row, dict) or len(row) > dimensions:
            raise ValueError('模型权重形状无效')
        for key, value in row.items():
            if not key.isascii() or not key.isdecimal() or key != str(int(key)) or int(key) >= dimensions:
                raise ValueError('模型权重索引无效')
            if type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError('模型权重数值无效')
        if not math.isfinite(abs(bias[index]) + sum(abs(value) for value in row.values())):
            raise ValueError('模型点积存在溢出风险')
    history = model.get('loss_history', [])
    if not isinstance(history, list) or any(
            type(value) not in (int, float) or not math.isfinite(value) for value in history):
        raise ValueError('模型训练记录无效')


def save_model(model, path):
    """保存已检查或训练得到的 gzip JSON 模型。"""
    payload = json.dumps(model, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    if len(payload) > MAX_MODEL_BYTES:
        raise ValueError('模型超过资源上限')
    with open(path, 'wb') as target:
        with gzip.GzipFile(filename='', fileobj=target, mode='wb', mtime=0) as stream:
            stream.write(payload)


def load_model(path):
    """读取并验证 gzip JSON 模型。"""
    with open(path, 'rb') as source:
        with gzip.GzipFile(fileobj=source, mode='rb') as stream:
            payload = stream.read(MAX_MODEL_BYTES + 1)
    if len(payload) > MAX_MODEL_BYTES:
        raise ValueError('模型超过资源上限')
    model = json.loads(payload.decode('utf-8'))
    _validate_model(model)
    return model
