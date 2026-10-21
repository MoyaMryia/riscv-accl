"""核对普通启动后实际生效的配置。"""
import re


def verify(text, config, *, context=12288):
    records = re.findall(r'^K1_EFFECTIVE_DEFAULTS (.+)$', text, re.MULTILINE)
    if len(records) != 1:
        raise ValueError('effective defaults record is absent or duplicated')
    actual = dict(item.split('=', 1) for item in records[0].split())
    expected = dict(threads=str(config['threads']), batch_threads=str(config['threads']),
        batch=str(config['ubatch']), ubatch=str(config['ubatch']), context=str(context), slots='1',
        flash='1', gpu='0', key='f16', value='f16', mask=str(config['mask']))
    if actual != expected:
        raise ValueError('effective defaults differ: ' + repr(actual))
    return actual
