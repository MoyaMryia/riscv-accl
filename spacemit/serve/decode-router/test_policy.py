"""验证路由策略的输入边界和固定预测结果。"""
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).with_name('policy.py')
spec = importlib.util.spec_from_file_location('decode_policy', MODULE_PATH)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class PolicyTests(unittest.TestCase):
    """验证后端地址、请求文本和路由选择。"""

    def test_backend_validation(self):
        valid = {'direct': 'http://127.0.0.1:8001', 'prefix': 'http://127.0.0.1:8002'}
        self.assertEqual(policy.check_backends(valid), valid)
        self.assertEqual(set(policy.check_backends({**valid, 'full': 'http://127.0.0.1:8003'})),
                         {'direct', 'prefix', 'full'})
        invalid = [
            {'direct': valid['direct']},
            {**valid, 'other': 'http://127.0.0.1:8003'},
            {**valid, 'direct': 'http://127.0.0.1:8002'},
            {**valid, 'prefix': 'http://user:pass@127.0.0.1:8002'},
            {**valid, 'prefix': 'http://127.0.0.1:0'},
            {**valid, 'prefix': 'http://127.0.0.1:8002 '},
        ]
        for backends in invalid:
            with self.subTest(backends=backends), self.assertRaises(ValueError):
                policy.check_backends(backends)

    def test_request_text_uses_last_user_message_and_rejects_bad_input(self):
        payload = {'messages': [
            {'role': 'user', 'content': 'first'},
            {'role': 'assistant', 'content': 'answer'},
            {'role': 'user', 'content': ' last user '},
        ]}
        self.assertEqual(policy.request_text(payload), ' last user ')
        invalid = [
            {'messages': [{'role': 'assistant', 'content': 'not user'}]},
            {'messages': [{'role': 'user', 'content': 3}]},
            {'messages': [{'role': 'user', 'content': '\ud800'}]},
            {'messages': [{'role': 'user', 'content': '  '}]},
        ]
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises((ValueError, UnicodeError)):
                policy.request_text(payload)

    def test_fixed_predictions_select_routes_and_keep_category_external(self):
        two = {'direct': 'd', 'prefix': 'p'}
        three = {**two, 'full': 'f'}
        model = {'min_score': 0.65}
        cases = [
            ({'category': 'code', 'score': 0.9}, three, 'prefix', 'class_map'),
            ({'category': 'qa', 'score': 0.9}, three, 'full', 'class_map'),
            ({'category': 'qa', 'score': 0.9}, two, 'direct', 'class_map'),
            ({'category': 'text', 'score': 0.9}, three, 'direct', 'class_map'),
            ({'category': 'document', 'score': 0.9}, three, 'direct', 'class_map'),
            ({'category': 'code', 'score': 0.64}, three, 'direct', 'low_score'),
            ({'category': 'text', 'score': 0.64}, three, 'direct', 'low_score'),
        ]
        for prediction, backends, route, reason in cases:
            with self.subTest(prediction=prediction, backends=backends):
                self.assertEqual(policy.choose(model, prediction, backends, score_guard=True),
                                 {'route': route, 'reason': reason})
        self.assertEqual(policy.choose(model, {'category': 'code', 'score': .4}, two),
                         {'route': 'prefix', 'reason': 'class_map'})
        self.assertEqual(policy.check_mode('prefix', two), 'prefix')
        for mode in ('full', 'unknown'):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                policy.check_mode(mode, two)


if __name__ == '__main__':
    unittest.main()
