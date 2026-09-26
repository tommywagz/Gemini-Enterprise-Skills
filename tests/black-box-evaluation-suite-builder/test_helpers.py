"""Black-box checks of the packaged command-line helpers."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]


class HelperCLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def run_helper(self, name, *args):
        return subprocess.run(
            [sys.executable, str(PACKAGE / "scripts" / name), *map(str, args)],
            text=True, capture_output=True, check=False,
        )

    def put(self, name, data):
        path = self.root / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_scaffold_creates_linked_records_and_refuses_repeat_without_changes(self):
        output = self.root / "suite"
        first = self.run_helper("scaffold_suite.py", "--output", output)
        self.assertEqual(first.returncode, 0, first.stderr)
        matrix = output / "coverage_matrix.json"
        report = output / "evaluation_report.json"
        row = json.loads(matrix.read_text())["rows"][0]
        result = json.loads(report.read_text())["results"][0]
        self.assertEqual((row["id"], row["test_ids"][0]), (result["matrix_id"], result["test_id"]))
        original = matrix.read_bytes()
        repeat = self.run_helper("scaffold_suite.py", "--output", output)
        self.assertEqual(repeat.returncode, 2)
        self.assertEqual(matrix.read_bytes(), original)

    def test_scaffold_refuses_partial_existing_output_without_writing_missing_file(self):
        output = self.root / "suite"
        output.mkdir()
        (output / "evaluation_report.json").write_text("user data", encoding="utf-8")
        result = self.run_helper("scaffold_suite.py", "--output", output)
        self.assertEqual(result.returncode, 2)
        self.assertFalse((output / "coverage_matrix.json").exists())

    def test_measurement_reports_latency_throughput_and_jitter(self):
        result_path = self.root / "result.json"
        result = self.run_helper(
            "measure_samples.py", "--samples", self.put("latency.json", [10, 20, 30, 40]),
            "--arrival-times", self.put("arrival.json", [0, 10, 21, 31]),
            "--payload-bytes", 1000, "--output", result_path,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result_path.read_text())
        self.assertEqual(data["latency"]["median"], 25)
        self.assertEqual(data["latency"]["p90"], 40)
        self.assertEqual(data["latency"]["p99_status"], "inconclusive")
        self.assertEqual(data["latency"]["p99_99_status"], "inconclusive")
        self.assertEqual(data["transfer"]["payload_bytes"], 1000)
        self.assertEqual(data["jitter"]["maximum"], 1)

    def test_measurement_rejects_nonfinite_and_nonmonotonic_inputs(self):
        for numbers in ([float("nan")], [-1]):
            with self.subTest(numbers=numbers):
                output = self.root / "invalid.json"
                result = self.run_helper(
                    "measure_samples.py", "--samples", self.put("latency.json", numbers),
                    "--output", output,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())
        result = self.run_helper(
            "measure_samples.py", "--samples", self.put("latency.json", [10]),
            "--arrival-times", self.put("arrival.json", [1, 1]),
            "--output", self.root / "invalid.json",
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
