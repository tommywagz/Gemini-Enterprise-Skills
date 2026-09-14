"""Stdlib-only generator regression tests; run with unittest discovery."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/generate_polyglot_workspace.py'


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.output = self.root / 'space in destination'

    def invoke(self, *extra):
        return subprocess.run([sys.executable, str(SCRIPT), '--name', 'sample-team',
                               '--output', str(self.output), *extra],
                              text=True, capture_output=True, timeout=10)

    def test_preview_is_write_free(self):
        result = self.invoke('--dry-run')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['mode'], 'dry-run')
        self.assertEqual(list(self.root.iterdir()), [])

    def test_custom_names_ports_and_manifest(self):
        result = self.invoke('--agent-name', 'support_agent', '--web-port', '3101',
                             '--adk-port', '8101', '--model', 'gemini-2.5-pro')
        self.assertEqual(result.returncode, 0, result.stderr)
        descriptor = json.loads((self.output / 'workspace.json').read_text())
        actual = sorted(str(p.relative_to(self.output)) for p in self.output.rglob('*') if p.is_file())
        self.assertEqual(descriptor['files'], actual)
        self.assertEqual(len(actual), 12)
        self.assertIn('support_agent', (self.output / 'apps/web/src/app.ts').read_text())
        self.assertIn('8101', (self.output / 'WORKSPACE.md').read_text())
        for path in actual:
            self.assertNotIn('@@', (self.output / path).read_text())
        compile((self.output / 'apps/agents/support_agent/agent.py').read_text(), 'agent.py', 'exec')

    def test_existing_output_not_modified(self):
        self.output.mkdir()
        marker = self.output / 'user-work'
        marker.write_text('preserve')
        self.assertEqual(self.invoke().returncode, 2)
        self.assertEqual(marker.read_text(), 'preserve')
        self.assertEqual(list(self.output.iterdir()), [marker])

    def test_dangling_symlink_not_followed(self):
        self.output.symlink_to(self.root / 'missing')
        self.assertEqual(self.invoke().returncode, 2)
        self.assertFalse((self.root / 'missing').exists())

    def test_bad_inputs_write_nothing(self):
        for args in [('--name', '../escape'), ('--agent-name', 'class'),
                     ('--agent-name', '../bad'), ('--model', 'x";evil'),
                     ('--web-port', '8000'), ('--adk-port', '65536'),
                     ('--output', str(self.root / 'missing' / 'child'))]:
            with self.subTest(args=args):
                self.assertEqual(self.invoke(*args).returncode, 2)
                self.assertEqual(list(self.root.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
