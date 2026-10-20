"""检查独立人工任务集的结构和边界案例。"""
import json
from collections import Counter
from pathlib import Path
import unittest


TASKS_PATH = Path(__file__).with_name("tasks.jsonl")
LABELS = {"code", "qa", "text", "document"}
SPLIT_COUNTS = {"train": 80, "dev": 24, "test": 24}
PER_LABEL = {"train": 20, "dev": 6, "test": 6}


def load_tasks():
    """读取任务集，并在入口处解析 JSONL。"""
    with TASKS_PATH.open(encoding="utf-8") as source:
        return [json.loads(line) for line in source if line.strip()]


class TaskDatasetTests(unittest.TestCase):
    """验证任务数、分配和人工边界标签。"""

    @classmethod
    def setUpClass(cls):
        cls.tasks = load_tasks()

    def test_total_fields_and_split_counts(self):
        self.assertEqual(len(self.tasks), 128)
        self.assertTrue(all(set(task) == {"id", "split", "label", "text"}
                            for task in self.tasks))
        self.assertEqual(Counter(task["split"] for task in self.tasks), SPLIT_COUNTS)
        self.assertTrue(all(task["label"] in LABELS for task in self.tasks))
        self.assertTrue(all(task["split"] in SPLIT_COUNTS for task in self.tasks))
        for split, count in PER_LABEL.items():
            with self.subTest(split=split):
                self.assertEqual(
                    Counter(task["label"] for task in self.tasks if task["split"] == split),
                    {label: count for label in LABELS},
                )

    def test_ids_and_normalized_text_are_unique(self):
        ids = [task["id"] for task in self.tasks]
        normalized = [" ".join(task["text"].casefold().split()) for task in self.tasks]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(normalized), len(set(normalized)))

    def test_splits_have_no_exact_text_overlap(self):
        texts = {split: {task["text"] for task in self.tasks if task["split"] == split}
                 for split in SPLIT_COUNTS}
        self.assertTrue(texts["train"].isdisjoint(texts["dev"]))
        self.assertTrue(texts["train"].isdisjoint(texts["test"]))

    def test_handwritten_confusion_cases(self):
        by_id = {task["id"]: task for task in self.tasks}
        expected = {
            "train-qa-02": "qa",       # 解释代码，不要求实现
            "test-qa-02": "qa",        # 解释代码，不要求实现
            "test-code-02": "code",    # 依据短资料编写 SQL
            "test-document-01": "document",  # 查询资料中的质保数值
            "train-text-06": "text",   # 中文邮件写作
            "test-qa-04": "qa",        # 简单账目计算
        }
        for task_id, label in expected.items():
            with self.subTest(task_id=task_id):
                self.assertEqual(by_id[task_id]["label"], label)

    def test_long_document_input_lengths(self):
        by_id = {task["id"]: task for task in self.tasks}
        long_test_docs = [by_id[f"test-document-{number:02d}"]["text"]
                          for number in (3, 5)]
        self.assertTrue(all(len(text) >= 250 for text in long_test_docs))


if __name__ == "__main__":
    unittest.main()
