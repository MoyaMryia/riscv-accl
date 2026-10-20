"""通过独立 llama-server 编码器执行 BERT 请求分类。"""
import json
import math
from pathlib import Path
import urllib.parse
import urllib.request

import bert_common
import classifier
from proxy import NoRedirect


def load_head(path):
    with Path(path).open('rb') as source:
        raw = source.read(classifier.MAX_MODEL_BYTES + 1)
    if len(raw) > classifier.MAX_MODEL_BYTES:
        raise ValueError('BERT head exceeds the size limit')
    head = json.loads(raw)
    if not isinstance(head, dict) or type(head.get('format')) is not int or head['format'] != 1 or head.get('labels') != list(classifier.LABELS):
        raise ValueError('BERT head format differs')
    if head.get('max_tokens') != bert_common.DEFAULTS['max_tokens']:
        raise ValueError('BERT input budget differs')
    for key in ('hidden_size', 'vocab_size'):
        if type(head.get(key)) is not int or head[key] < 1:
            raise ValueError('invalid BERT dimension: ' + key)
    for key in ('cls_token_id', 'sep_token_id', 'pad_token_id'):
        if type(head.get(key)) is not int or not 0 <= head[key] < head['vocab_size']:
            raise ValueError('invalid BERT special token: ' + key)
    weights, bias = head.get('weights'), head.get('bias')
    if not isinstance(weights, list) or len(weights) != len(classifier.LABELS) or not isinstance(bias, list) or len(bias) != len(classifier.LABELS):
        raise ValueError('BERT head shape differs')
    for row, offset in zip(weights, bias):
        if not isinstance(row, list) or len(row) != head['hidden_size']:
            raise ValueError('BERT projection width differs')
        if any(type(value) not in (int, float) or not math.isfinite(value) for value in [offset, *row]):
            raise ValueError('BERT projection contains nonfinite values')
    threshold = head.get('min_score')
    if type(threshold) not in (int, float) or not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError('BERT score threshold differs')
    return head


class Client:
    def __init__(self, head_path, url, timeout):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or not parsed.port or parsed.username or parsed.password or parsed.path not in ('', '/') or parsed.query or parsed.fragment:
            raise ValueError('use a loopback HTTP encoder with an explicit port')
        if type(timeout) not in (float, int) or not math.isfinite(timeout) or timeout <= 0:
            raise ValueError('encoder timeout must be finite and positive')
        self.head = load_head(head_path)
        self.url = url.rstrip('/')
        self.timeout = timeout
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())

    def post(self, endpoint, payload):
        request = urllib.request.Request(self.url + endpoint,
            json.dumps(payload, ensure_ascii=False).encode('utf-8'),
            {'Content-Type': 'application/json'}, method='POST')
        with self.opener.open(request, timeout=self.timeout) as response:
            return json.load(response)

    def predict(self, text):
        tokens = self.post('/tokenize', {'content': text, 'add_special': False, 'parse_special': True})['tokens']
        if not isinstance(tokens, list) or not all(type(value) is int and 0 <= value < self.head['vocab_size'] for value in tokens):
            raise ValueError('encoder token response differs')
        selected = bert_common.add_special(tokens, self.head)
        data = self.post('/v1/embeddings', {'input': selected, 'embd_normalize': -1})['data']
        if not isinstance(data, list) or len(data) != 1:
            raise ValueError('encoder response count differs')
        embedding = data[0]['embedding']
        if not isinstance(embedding, list) or len(embedding) != self.head['hidden_size'] or any(type(value) not in (int, float) or not math.isfinite(value) for value in embedding):
            raise ValueError('encoder vector differs')
        result = bert_common.classify_embedding(self.head['weights'], self.head['bias'], embedding)
        return {**result, 'selected_token_ids': selected, 'cls_embedding': embedding}
