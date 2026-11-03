import json
from pathlib import Path
import tempfile
import unittest

from webui.worker import retry_inputs


class RetryInputs(unittest.TestCase):
    def test_multiple_retries_reuse_original_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original, first, second = [root / (c * 32) for c in 'abc']
            for folder in (original, first, second):
                folder.mkdir()
            (original / 'inputs').mkdir()
            (original / 'task.json').write_text(json.dumps({'files': ['game.nsp']}), encoding='utf-8')
            (first / 'task.json').write_text(json.dumps({'files': ['game.nsp'], 'retry_of': original.name}), encoding='utf-8')
            self.assertEqual(retry_inputs(second, {'files': ['game.nsp'], 'retry_of': first.name}), original / 'inputs')
            self.assertEqual(retry_inputs(second, {'files': ['different.nsp'], 'retry_of': first.name}), second / 'inputs')
            (first / 'inputs').mkdir()
            self.assertEqual(retry_inputs(second, {'files': ['game.nsp'], 'retry_of': first.name}), first / 'inputs')

    def test_cycle_and_missing_ancestor_fall_back_to_new_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first, second = root / ('a' * 32), root / ('b' * 32)
            first.mkdir(); second.mkdir()
            (first / 'task.json').write_text(json.dumps({'files': [], 'retry_of': first.name}), encoding='utf-8')
            self.assertEqual(retry_inputs(second, {'files': [], 'retry_of': first.name}), second / 'inputs')
            self.assertEqual(retry_inputs(second, {'files': [], 'retry_of': 'f' * 32}), second / 'inputs')


if __name__ == '__main__':
    unittest.main()
