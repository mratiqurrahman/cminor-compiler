import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class NativePipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        required = ["llc", "gcc"]
        missing = [name for name in required if shutil.which(name) is None]
        if missing:
            raise unittest.SkipTest("required native tools unavailable: " + ", ".join(missing))

    def test_acceptance_examples_through_executable(self):
        cases = [
            "acceptance_b1.cm",
            "acceptance_b2.cm",
            "acceptance_b3.cm",
            "acceptance_b4.cm",
            "loop_call_trace.cm",
            "expression_native_test.cm",
            "statement_control_test.cm",
            "for_continue_update_test.cm",
            "function_coverage_test.cm",
            "statement_edge_coverage_test.cm"
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            for name in cases:
                source = ROOT / "examples" / name
                assembly = work / (source.stem + ".s")
                object_file = work / (source.stem + ".o")
                executable = work / source.stem
                compiler = subprocess.run([sys.executable, "-m", "cminor", str(source), "-o", str(assembly)], cwd=ROOT, env=env, capture_output=True, text=True, timeout=30)
                self.assertEqual(compiler.returncode, 0, compiler.stderr)
                assembler = subprocess.run(["gcc", "-c", str(assembly), "-o", str(object_file)], capture_output=True, text=True, timeout=15)
                self.assertEqual(assembler.returncode, 0, assembler.stderr)
                linker = subprocess.run(["gcc", "-no-pie", str(object_file), "-o", str(executable)], capture_output=True, text=True, timeout=15)
                self.assertEqual(linker.returncode, 0, linker.stderr)
                run = subprocess.run([str(executable)], capture_output=True, text=True, timeout=5)
                self.assertEqual(run.returncode, 0, f"{name} returned {run.returncode}; stdout={run.stdout}; stderr={run.stderr}")

if __name__ == "__main__":
    unittest.main()
