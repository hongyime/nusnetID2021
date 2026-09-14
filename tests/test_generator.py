"""Offline generator checks; never touch retained output files or live services."""

import contextlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load_generator():
    """Load with an I/O trap, including when testing the original unsafe module."""
    spec = importlib.util.spec_from_file_location("generator_fixture", ROOT / "generate.py")
    module = importlib.util.module_from_spec(spec)
    legacy_stub = types.SimpleNamespace(eval_js=lambda _script: lambda _value: "synthetic")
    with mock.patch.dict(sys.modules, {"js2py": legacy_stub}):
        with mock.patch("builtins.open", side_effect=AssertionError("Generation during import")):
            with contextlib.redirect_stdout(io.StringIO()) as captured:
                spec.loader.exec_module(module)
    return module, captured.getvalue()


class GeneratorTests(unittest.TestCase):
    """Compare old checksums independently and test only bounded temporary output."""

    def test_import_does_not_generate(self):
        """Importing helpers must never start a multi-million-line write."""
        _module, output = load_generator()
        self.assertEqual(output, "")

    def test_checksum_matches_original_javascript(self):
        """Exercise both prefixes, discarded digits, casing and legacy matching."""
        module, _output = load_generator()
        samples = ["", "wrong", "A123", "a1234567", "U123456", "u1234567",
                   "beforeU123456after", " A1234567", "A12345678", "U12345678",
                   "A１２３４５６７", "U0000000", "A0000000"]
        for prefix in ("A", "U"):
            for number in (1, 9, 10, 99, 100, 999, 1000, 9999, 10000,
                           99999, 100000, 999999, 1000000, 7654321, 9999999):
                samples.append(prefix + str(number).zfill(7))
        reference = subprocess.run(
            ["node", str(ROOT / "tests" / "fixtures" / "legacy-checksum.cjs")],
            input=json.dumps(samples), capture_output=True, text=True, check=True,
        )
        self.assertEqual([module.calculate(value) for value in samples],
                         json.loads(reference.stdout))

    def test_bounded_generation_appends_once_and_preserves_existing_bytes(self):
        """Explicit execution adds one pass to each file instead of two."""
        module, _output = load_generator()
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for prefix in ("A", "U"):
                (target / ("nusnetid" + prefix + ".txt")).write_bytes(b"retained\n")
            result = subprocess.run(
                [sys.executable, str(ROOT / "generate.py"), "--start", "1", "--stop", "4",
                 "--output-dir", directory, "--quiet"],
                capture_output=True, text=True, check=True,
            )
            self.assertEqual(result.stdout, "")
            for prefix in ("A", "U"):
                expected = "retained\n" + "".join(
                    module.calculate(prefix + str(value).zfill(7)) + "\n"
                    for value in range(1, 4)
                )
                self.assertEqual((target / ("nusnetid" + prefix + ".txt")).read_text(), expected)

    def test_invalid_range_does_not_create_output(self):
        """Reject invalid bounds before opening either destination."""
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(ROOT / "generate.py"), "--start", "4", "--stop", "1",
                 "--output-dir", directory], capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_prefix_selection_and_stdout_match_written_rows(self):
        """A limited single-prefix command leaves the other destination absent."""
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [sys.executable, str(ROOT / "generate.py"), "--prefix", "U", "--start", "12",
                 "--stop", "15", "--output-dir", directory],
                capture_output=True, text=True, check=True,
            )
            target = Path(directory)
            self.assertFalse((target / "nusnetidA.txt").exists())
            rows = (target / "nusnetidU.txt").read_text()
            self.assertEqual(rows, result.stdout)
            self.assertEqual(len(rows.splitlines()), 3)


if __name__ == "__main__":
    unittest.main()
