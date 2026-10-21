#!/usr/bin/env python3
"""检测连续重复行，并在生成退化时提前停止请求。"""

DEFAULT_WINDOW = 3
DEFAULT_MIN_CHARS = 20
DEFAULT_MAX_PERIOD = 3


class DegenerateOutput(RuntimeError):
    """生成文本连续重复同一行。"""


class RepeatGuard:
    """按增量文本检测重复行序列。

    window 为重复次数。min_chars 为参与判断的最短行长。
    周期 1 到 max_period 的重复块都算退化：单行重复，以及 A/B 交替重复。
    短行和空行会重置序列，避免把正常代码判为退化。
    """

    def __init__(self, window=DEFAULT_WINDOW, min_chars=DEFAULT_MIN_CHARS,
                 max_period=DEFAULT_MAX_PERIOD):
        if type(window) is not int or window < 2:
            raise ValueError('window must be an integer of at least 2')
        if type(min_chars) is not int or min_chars < 4:
            raise ValueError('min_chars must be an integer of at least 4')
        if type(max_period) is not int or max_period < 1:
            raise ValueError('max_period must be a positive integer')
        self.window = window
        self.min_chars = min_chars
        self.max_period = max_period
        self.line = ''
        self.lines = []

    def feed(self, delta):
        """接收一段增量文本；检测到连续重复时抛出 DegenerateOutput。"""
        if not isinstance(delta, str):
            raise TypeError('delta must be text')
        for char in delta:
            if char != '\n':
                self.line += char
                continue
            normalized = ' '.join(self.line.split())
            self.line = ''
            if len(normalized) < self.min_chars:
                self.lines.clear()
                continue
            self.lines.append(normalized)
            keep = self.max_period * self.window
            if len(self.lines) > keep:
                del self.lines[:-keep]
            for period in range(1, self.max_period + 1):
                need = period * self.window
                if len(self.lines) < need:
                    continue
                tail = self.lines[-need:]
                if all(tail[index] == tail[index % period] for index in range(need)):
                    raise DegenerateOutput('repeated block of {} lines {} times: {}'.format(
                        period, self.window, tail[0][:80]))
