import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from webui.build.windows.build_ipa_windows import check_shader_split_log, shader_split_command
from webui.file_tools import filesystem_path


class WindowsShaderPaths(unittest.TestCase):
    def test_unreadable_shader_files_stop_the_build(self):
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'shader_split.log'
            log.write_text('progress: 1/1\nshaders: 1\n', encoding='utf-8')
            check_shader_split_log(log)
            log.write_text('[RED] 1 file(s) could not be read, their shaders are left out (first: sample)\n', encoding='utf-8')
            with self.assertRaisesRegex(RuntimeError, 'left files unreadable'):
                check_shader_split_log(log)

    @unittest.skipUnless(os.name == 'nt', 'Windows extended paths')
    def test_scanner_reads_long_romfs_descendant(self):
        repo = Path(__file__).resolve().parents[2]
        root = Path(tempfile.mkdtemp())
        try:
            extracted = root / 'extract' / 'v720896'
            romfs = extracted / 'RomFS'
            nested = romfs / ('a' * 120) / ('b' * 120)
            filesystem_path(nested).mkdir(parents=True)
            target = filesystem_path(nested / 'test.bgyml')
            target.write_bytes(b'test fixture')
            self.assertGreater(len(str(nested / 'test.bgyml')), 260)
            command = shader_split_command(sys.executable, repo, extracted, root / 'shader', root / 'tables', ['map', 'facts', 'pairs'])
            code = (
                'import os, sys\n'
                'sys.path.insert(0, sys.argv[1])\n'
                'import shader_split as s\n'
                'root = sys.argv[2]\n'
                'files = [(os.path.join(dp, f), os.path.relpath(os.path.join(dp, f), root).replace(os.sep, "/")) '
                'for dp, _, fs in os.walk(root) for f in fs]\n'
                'assert len(files) == 1 and files[0][0].startswith("\\\\\\\\?\\\\")\n'
                'assert s.zip_jobs(files) == ([], set())\n'
                'result = s.scan_file(files[0])\n'
                'assert result[3] == {}, result\n'
            )
            env = dict(os.environ, DM_GAME='010015100B514000')
            result = subprocess.run([sys.executable, '-c', code, str(repo / 'dm/gfx/tools'), str(command[2])],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        finally:
            shutil.rmtree(filesystem_path(root))


if __name__ == '__main__':
    unittest.main()
