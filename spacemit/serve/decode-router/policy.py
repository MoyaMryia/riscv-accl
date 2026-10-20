"""检查路由入口，并选择两个或三个解码后端。"""
from urllib.parse import urlsplit, urlunsplit

ROUTES = ('direct', 'prefix', 'full')


def check_backends(values):
    if set(values) not in ({'direct', 'prefix'}, set(ROUTES)):
        raise ValueError('配置必须提供 direct、prefix，可选 full')
    result = {}
    for route, value in values.items():
        if not isinstance(value, str) or not value.isascii() or any(ord(c) <= 32 or ord(c) == 127 for c in value):
            raise ValueError('后端地址必须为无空白和控制字符的 ASCII 字符串')
        url = urlsplit(value)
        if url.scheme not in ('http', 'https') or not url.hostname or url.username is not None or url.password is not None:
            raise ValueError('后端必须使用无内嵌凭证的 HTTP 地址')
        if url.query or url.fragment:
            raise ValueError('后端基地址不能含 query 或 fragment')
        if url.port == 0:
            raise ValueError('后端端口无效')
        result[route] = urlunsplit((url.scheme, url.netloc.lower(), url.path.rstrip('/'), '', ''))
    if len(set(result.values())) != len(result):
        raise ValueError('不同解码路径必须配置不同地址')
    return result


def request_text(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get('messages'), list):
        raise ValueError('请求必须提供 messages 列表')
    last = None
    for message in payload['messages']:
        if not isinstance(message, dict) or not isinstance(message.get('role'), str) or not isinstance(message.get('content'), str):
            raise ValueError('实验代理只接受文本消息')
        if message['role'] == 'user':
            last = message['content']
    if last is None or not last.strip():
        raise ValueError('请求必须包含非空 user 文本')
    last.encode('utf-8')
    return last


def check_mode(mode, backends):
    if mode != 'auto' and mode not in backends:
        raise ValueError('请求的解码路径未启用')
    return mode


def choose(model, prediction, backends, score_guard=False):
    if score_guard and prediction['score'] < model['min_score']:
        return {'route': 'direct', 'reason': 'low_score'}
    mapping = {'code': 'prefix', 'qa': 'full' if 'full' in backends else 'direct',
               'text': 'direct', 'document': 'direct'}
    return {'route': mapping[prediction['category']], 'reason': 'class_map'}
