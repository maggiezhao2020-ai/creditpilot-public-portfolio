"""Self-contained checks for the independently copied public package."""

import ast
import hashlib
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from streamlit.testing.v1 import AppTest

from creditpilot.public_portfolio import app, components, contracts, loader


class PackageTests(unittest.TestCase):
    def test_package_imports_and_complete_pinned_bundle(self):
        for module in (app, components, contracts, loader):
            self.assertTrue(Path(module.__file__).resolve().is_relative_to(ROOT))
        self.assertEqual(app.BUNDLE_DIRECTORY.resolve(), ROOT / 'public_artifacts' / 'v1')
        self.assertEqual(app.MANIFEST_PIN,
                         'aefd27fac4321c7d56e0466eba63233f0aa1fda9ca3fd893992beca31c50086e')
        expected = {
            'manifest.json': '500c43af8fa23806b233e25a11cd6b5f209a533c0f5673b4dee5f194d9f59fac',
            'cp-001.json': 'd97df09bf3bc0a475177a5ff73d22fef59a2ae5ff2fde11b394933740014b56f',
            'cp-002.json': 'd9628fd9bde5b5c654c2b964ac8387a3b019ac55272d94b33a385249c84a0852',
            'cp-003.json': 'eadbf650edb81338ebebc540d6ae2af215ea7a5382e94974a00e66cbd47fe891',
        }
        self.assertEqual({p.name for p in app.BUNDLE_DIRECTORY.iterdir()}, set(expected))
        for name, digest in expected.items():
            path = app.BUNDLE_DIRECTORY / name
            self.assertFalse(path.is_symlink())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        bundle = loader.load_bundle(app.BUNDLE_DIRECTORY,
                                    expected_manifest_sha256=app.MANIFEST_PIN)
        self.assertEqual(set(bundle), {'CP-001', 'CP-002', 'CP-003'})
        investigation = bundle['CP-003']
        self.assertFalse(investigation['decision']['engine_reached'])
        self.assertIsNone(investigation['decision']['system_recommendation'])
        self.assertEqual(investigation['human_route']['disposition'], 'HUMAN_INVESTIGATION')
        self.assertEqual(investigation['human_route']['review_status'], 'PENDING')
        for key, (_, digest, _) in components.ARCHITECTURE_ASSETS.items():
            self.assertEqual(hashlib.sha256(components.architecture_asset(key)).hexdigest(), digest)

    def test_entrypoint_navigation_and_recorded_outcomes(self):
        page = AppTest.from_file(str(ROOT / 'src' / 'app.py'), default_timeout=20).run()
        self.assertFalse(page.exception)
        self.assertEqual([x.label for x in page.button], list(app.SECTIONS))
        sidebar = '\n'.join(x.value for x in page.sidebar.markdown)
        self.assertIn('Bundle Verified · v1.1.0', sidebar)
        for section in app.SECTIONS:
            next(x for x in page.button if x.label == section).click().run()
            self.assertFalse(page.exception)
            self.assertEqual('\n'.join(x.value for x in page.sidebar.markdown), sidebar)
        next(x for x in page.button if x.label == 'Golden Scenario Explorer').click().run()
        self.assertEqual(page.session_state['public_scenario'], 'CP-002')
        self.assertEqual([x.label for x in page.tabs], list(app.TABS))
        self.assertFalse(page.sidebar.button or page.sidebar.radio)
        for scenario_id in ('CP-001', 'CP-002', 'CP-003'):
            next(x for x in page.button if x.label == app.SCENARIO_LABELS[scenario_id]).click().run()
            self.assertFalse(page.exception)
            self.assertEqual(page.session_state['public_scenario'], scenario_id)
            self.assertIn(scenario_id, '\n'.join(x.value for x in page.markdown))
            if scenario_id == 'CP-003':
                self.assertIn('Decision Engine NOT REACHED', '\n'.join(x.value for x in page.markdown))
        self.assertFalse(page.radio or page.get('file_uploader') or page.get('download_button'))

    def test_missing_bundle_fails_without_verified_status(self):
        with tempfile.TemporaryDirectory() as td:
            directory = Path(td) / 'v1'
            shutil.copytree(app.BUNDLE_DIRECTORY, directory)
            (directory / 'cp-003.json').unlink()
            with patch.object(app, 'BUNDLE_DIRECTORY', directory):
                page = AppTest.from_string('from creditpilot.public_portfolio.app import main\nmain()').run()
        self.assertEqual([e.value for e in page.error],
                         ['Recorded scenarios unavailable. Bundle validation did not pass.'])
        self.assertNotIn('Bundle Verified', '\n'.join(x.value for x in page.sidebar.markdown))
        self.assertFalse(page.tabs or page.table)

    def test_no_privileged_application_imports_or_actions(self):
        forbidden = ('creditpilot.demo', 'creditpilot.api', 'creditpilot.portfolio_export',
                     'creditpilot.workflow', 'creditpilot.agents', 'sqlite3', 'requests',
                     'urllib', 'socket', 'subprocess', 'joblib', 'sklearn', 'shap')
        for module in (app, components, contracts, loader):
            tree = ast.parse(Path(module.__file__).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertTrue(all(not alias.name.startswith(forbidden) for alias in node.names))
                elif isinstance(node, ast.ImportFrom) and node.module:
                    self.assertFalse(node.module.startswith(forbidden))


if __name__ == '__main__':
    unittest.main()
