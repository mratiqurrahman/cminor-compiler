import contextlib
import io
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]

POSITIVE = [
    "int main(void){return 0;}",
    "int main(void){return 2147483647;}",
    "int main(void){int x=7; return x;}",
    "int main(void){return 2+3;}",
    "int main(void){return 2+3*4==14?0:1;}".replace("?0:1", ""),
    "int main(void){return (2+3)*4;}",
    "int main(void){return -(-5)+!0;}",
    "int main(void){return (3<4)+(4<=4)+(5>4)+(5>=5);}",
    "int main(void){return (1==1)+(1!=0);}",
    "int main(void){int x=0; x=1; x=x+2; return x;}",
    "int main(void){int x=0; x=(x=3)+2; return x;}",
    "int main(void){; return 0;}",
    "int main(void){{int x=1; x=x+1;} return 0;}",
    "int main(void){if(1)return 1; else return 0; return 0;}",
    "int main(void){int x=0; while(x<3){x=x+1;} return x;}",
    "int main(void){int x=0; for(int i=0;i<4;i=i+1)x=x+i; return x;}",
    "int main(void){int x=0; int i=0; for(;i<3;i=i+1)x=x+1; return x;}",
    "int main(void){int i=0; for(;i<3;)i=i+1; return i;}",
    "int main(void){int i=0; for(;;){i=i+1;break;} return i;}",
    "int main(void){int i=0; while(i<5){i=i+1; if(i==3)break;} return i;}",
    "int main(void){int i=0; while(i<4){i=i+1;continue;} return i;}",
    "int main(void){int i=0; for(int j=0;j<4;j=j+1){i=i+1;continue;} return i;}",
    "int main(void){int x=1; {int x=2; x=x+1;} return x;}",
    "int inc(int x); int main(void){return inc(4)-5;} int inc(int x){return x+1;}",
    "int add(int a,int b){return a+b;} int main(void){return add(19,23)-42;}",
    "int fact(int n); int main(void){return fact(5)-120;} int fact(int n){if(n<=1)return 1; return n*fact(n-1);}",
    "int even(int n); int odd(int n); int main(void){return even(8)-1;} int even(int n){if(n==0)return 1;return odd(n-1);} int odd(int n){if(n==0)return 0;return even(n-1);}",
    "void noop(void){return;} int main(void){noop();return 0;}",
    "int sum6(int a,int b,int c,int d,int e,int f){return a+b+c+d+e+f;} int main(void){return sum6(1,2,3,4,5,6)-21;}",
    "int value(void){return 9;} int main(void){return value()-9;}",
    "int id(int x){return x;} int add(int a,int b){return a+b;} int main(void){return add(id(2),id(3))-5;}",
    "int main(void){int x=0; if(0&&(x=1))x=2; if(1||(x=3))x=x; return x;}",
    "int main(void){int x=0; if(1&&1)x=x+1; if(0||1)x=x+1; return x-2;}",
    "int main(void){int x=0; x=1|| (x=2); return x-1;}",
    "int main(void){int x=0; x=0&& (x=2); return x;}",
    "int main(void){int x=1; int y=2; return (x<y)+(x!=y)-2;}",
    "int main(void){int x=12; return x%5-2;}",
    "int main(void){int x=9; return x/2-4;}",
    "int main(void){int x=1; int y=2; int z=3; return x+y*z-7;}",
    "int main(void){int x=1; int y=2; return (x+y)*(x+y)-9;}",
    "int main(void){return +3-3;}",
    "int main(void){return !5;}",
    "int main(void){return !!5-1;}",
    "int main(void){int x=0; for(int i=0;i<4;i=i+1){if(i==2)continue;x=x+1;} return x-3;}",
    "int main(void){int x=0; {int a=1; {int a=2; x=a;}} return x-2;}",
    "int f(int); int main(void){return f(8)-8;} int f(int x){return x;}",
    "void f(void); int main(void){f();return 0;} void f(void){;}",
    "int main(void){int x=0; x=(x=2)+(x=3); return x-5;}",
    "int main(void){int x=0; for(x=0;x<2;x=x+1); return x-2;}",
    "int main(void){int x=0; for(x=0;x<3;x=x+1)x=x+1; return x-4;}",
    "int main(void){int x=0; while(0){x=1;} return x;}",
    "int main(void){int x=0; for(;;){x=1;break;} return x-1;}",
    "int main(void){int x=0; if(0)x=1; else x=2; return x-2;}",
    "int main(void){int x=0; if(1)if(0)x=1;else x=2; return x-2;}",
    "int main(void){int x=0; // line comment\n x=x+1; /* block */ return x-1;}",
    "int main(void){int/**/x=2; return x-2;}",
    "// #include <stdio.h>\nint main(void){return 0;}",
    "int main(void){return 0;}\r\n",
    "int\tmain(void){\vint\f x=1; return x-1;}",
    "int main(void){int x=0; for(int i=0;i<1;i=i+1)x=x+1; return x-1;}"
]

NEGATIVE = [
    ("", "SYNTAX_ERROR"),
    ("int f(void){return 0;}", "NAME_ERROR"),
    ("void main(void){return;}", "TYPE_ERROR"),
    ("int main(int x){return 0;}", "TYPE_ERROR"),
    ("int main(void){return x;}", "NAME_ERROR"),
    ("int main(void){int x=1; int x=2; return 0;}", "NAME_ERROR"),
    ("int main(void){int x=y; return 0;}", "NAME_ERROR"),
    ("int main(void){return f();}", "NAME_ERROR"),
    ("int f(void); int main(void){return f();}", "NAME_ERROR"),
    ("int f(int); int f(void){return 0;} int main(void){return 0;}", "TYPE_ERROR"),
    ("int main(void){return f(1);} int f(void){return 0;}", "NAME_ERROR"),
    ("int main(void){int f=1; return f();}", "CALL_ERROR"),
    ("int f(void){return 0;} int main(void){return f(1);}", "CALL_ERROR"),
    ("int f(int x); int main(void){return f();} int f(int x){return x;}", "CALL_ERROR"),
    ("int main(void){return 1=2;}", "TYPE_ERROR"),
    ("int main(void){int x=1; return (x+1)=2;}", "TYPE_ERROR"),
    ("int main(void){break; return 0;}", "CONTROL_FLOW_ERROR"),
    ("int main(void){continue; return 0;}", "CONTROL_FLOW_ERROR"),
    ("int main(void){for(int i=0;i<2;i=i+1); return i;}", "NAME_ERROR"),
    ("int main(void){return;}", "RETURN_ERROR"),
    ("void f(void){return 1;} int main(void){return 0;}", "RETURN_ERROR"),
    ("int main(void){if(1)return 0;}", "RETURN_ERROR"),
    ("int f(int n){if(n==0)return 0;} int main(void){return 0;}", "RETURN_ERROR"),
    ("int main(void){}", "RETURN_ERROR"),
    ("int main(void){int x=1;}", "RETURN_ERROR"),
    ("int main(void){int x=0; return f(x);} int f(int x){return x;}", "NAME_ERROR"),
    ("int main(void){int x=0; x(); return 0;}", "CALL_ERROR"),
    ("int main(void){int x=; return 0;}", "SYNTAX_ERROR"),
    ("int main(void){return 012;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){return 0x10;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){return 0b10;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){return 2147483648;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){return 1.0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){return 1u;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int a[2]; return 0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int *p; return 0;}", "UNSUPPORTED_FEATURE"),
    ("int x; int main(void){return 0;}", "UNSUPPORTED_FEATURE"),
    ("float f(void){return 0;} int main(void){return 0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=0; x++; return 0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=1; x--; return 0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=1; x+=1; return 0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=1; x-=1; return 0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=1; x*=2; return 0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=1; x/=2; return 0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=1; x%=2; return 0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=1; return x<<1;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=1; return x>>1;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=1; return x&1;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=1; return x|1;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=1; return x^1;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=1; return ~x;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=1; x->1; return 0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=1; x[0]; return 0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){return 1?2:3;}", "UNSUPPORTED_FEATURE"),
    ("#include <stdio.h>\nint main(void){return 0;}", "UNSUPPORTED_PREPROCESSING_DIRECTIVE"),
    ("  #define X 1\nint main(void){return 0;}", "UNSUPPORTED_PREPROCESSING_DIRECTIVE"),
    ("%:define X 1\nint main(void){return 0;}", "UNSUPPORTED_PREPROCESSING_DIRECTIVE"),
    ("int main(void){ /* unfinished", "LEXICAL_ERROR"),
    ("int main(void){return \"x\";}", "UNSUPPORTED_FEATURE"),
    ("int main(void){return 'x';}", "UNSUPPORTED_FEATURE"),
    ("int main(void){return @;}", "LEXICAL_ERROR"),
    ("int main(void){return 0;} \\\n", "UNSUPPORTED_LINE_SPLICING"),
    ("int main(void){return 0;} \\\r\n", "UNSUPPORTED_LINE_SPLICING"),
    ("int main(void){do;while(0);return 0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){switch(1){}return 0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){return 0}", "SYNTAX_ERROR"),
    ("int main(void){if(1)return 0;else}return 0;", "SYNTAX_ERROR"),
    ("int main(void){return 0;} int main(void){return 0;}", "NAME_ERROR"),
    ("int main(void){int x; {int x;} int x; return 0;}", "NAME_ERROR"),
    ("int main(void){return 1+;}", "SYNTAX_ERROR"),
    ("int main(void){void x; return 0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){return 0;} int f(int a,int b,int c,int d,int e,int f,int g){return a;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){int x=0; return x(1);}", "CALL_ERROR"),
    ("int main(void){return (float)0;}", "UNSUPPORTED_FEATURE"),
    ("int main(void){return 0;} int f(void);", "NAME_ERROR"),
    ("int main(void){return 0;} int f(void){return 1;} int f(void){return 2;}", "NAME_ERROR"),
    ("int main(void){return 0;} int f(void){return 1;} int g(void){return h();} int h(void){return 2;}", "NAME_ERROR"),
    ("int main(void){return 0;} int main(int x);", "TYPE_ERROR")
]

class CompilerTests(unittest.TestCase):
    def run_source(self, source, *options, path_suffix=".cm", timeout=5, extra_env=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / ("case" + path_suffix)
            path.write_text(source, encoding="utf-8", newline="")
            from cminor.driver import main
            old_argv = sys.argv
            sys.argv = ["cminorcc", *options, str(path)]
            stdout = io.StringIO()
            stderr = io.StringIO()
            code = 0
            previous_handler = None
            if hasattr(signal, "SIGALRM") and timeout:
                previous_handler = signal.signal(signal.SIGALRM, lambda signum, frame: (_ for _ in ()).throw(TimeoutError("compiler exceeded per-case timeout")))
                signal.setitimer(signal.ITIMER_REAL, timeout)
            try:
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    try:
                        code = main()
                    except SystemExit as exc:
                        code = exc.code if isinstance(exc.code, int) else 1
            finally:
                if previous_handler is not None:
                    signal.setitimer(signal.ITIMER_REAL, 0)
                    signal.signal(signal.SIGALRM, previous_handler)
                sys.argv = old_argv
            return SimpleNamespace(returncode=code, stdout=stdout.getvalue(), stderr=stderr.getvalue())

    def test_lexer_identifier_and_character_rules(self):
        valid = [
            "int main(void){int _value=1; return _value-1;}",
            "int main(void){int value_2=2; return value_2-2;}",
            "int main(void){int Value9=9; return Value9-9;}",
        ]
        for source in valid:
            with self.subTest(source=source):
                result = self.run_source(source, "--check")
                self.assertEqual(result.returncode, 0, result.stderr)

        invalid = [
            ("int main(void){int auto=1; return 0;}", "UNSUPPORTED_FEATURE"),
            ("int main(void){int char=1; return 0;}", "UNSUPPORTED_FEATURE"),
            ("int main(void){int sizeof=1; return 0;}", "UNSUPPORTED_FEATURE"),
            ("int main(void){int café=1; return 0;}", "LEXICAL_ERROR"),
            ("int main(void){return é;}", "LEXICAL_ERROR"),
        ]
        for source, expected in invalid:
            with self.subTest(source=source):
                result = self.run_source(source, "--check")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected, result.stderr)

    def test_positive_language_cases(self):
        self.assertGreaterEqual(len(POSITIVE), 50)
        for index, source in enumerate(POSITIVE):
            with self.subTest(case=index):
                result = self.run_source(source, "--check")
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_negative_language_cases(self):
        for index, (source, expected) in enumerate(NEGATIVE):
            with self.subTest(case=index, expected=expected):
                result = self.run_source(source, "--check")
                self.assertNotEqual(result.returncode, 0)
                self.assertRegex(
                    result.stderr,
                    rf"case\.cm:\d+:\d+: error {expected}:"
                )

    def test_diagnostic_reports_source_line_and_column(self):
        source = "int main(void) {\n    return missing;\n}\n"
        result = self.run_source(source, "--check")

        self.assertEqual(result.returncode, 1)
        self.assertRegex(
            result.stderr,
            r"case\.cm:2:12: error NAME_ERROR:"
        )

    def test_parser_reports_independent_later_errors(self):
        result = self.run_source("int main(void){int a=; int b=; return 0;}", "--check")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr.count("SYNTAX_ERROR"), 2)

    def test_malformed_mutations_are_controlled(self):
        for index in range(100):
            source = f"int main(void){{return 0 @ {index};}}"
            with self.subTest(mutation=index):
                result = self.run_source(source, "--check", timeout=5)
                self.assertEqual(result.returncode, 1)
                self.assertIn("LEXICAL_ERROR", result.stderr)

    def test_dump_commands_and_backend_ir(self):
        source = "int id(int x){return x;} int main(void){int a=id(3); return a-3;}"
        tokens = self.run_source(source, "--dump-tokens")
        ast = self.run_source(source, "--dump-ast")
        symbols = self.run_source(source, "--dump-symbols")
        ir = self.run_source(source, "--dump-ir")
        self.assertEqual(tokens.returncode, 0, tokens.stderr)
        self.assertEqual(ast.returncode, 0, ast.stderr)
        self.assertEqual(symbols.returncode, 0, symbols.stderr)
        self.assertEqual(ir.returncode, 0, ir.stderr)
        self.assertIn("INT_LITERAL", tokens.stdout)
        self.assertIn("Definition int main", ast.stdout)
        self.assertIn("RESOLUTIONS", symbols.stdout)
        self.assertIn("call @id", ir.stdout)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "module.ll"
            result = self.run_source(source, "--emit-backend-ir", "-o", str(target))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("target triple", target.read_text())

    def run_exact_path(self, path, *options):
        from cminor.driver import main
        old_argv = sys.argv
        sys.argv = ["cminorcc", *options, str(path)]
        stdout = io.StringIO()
        stderr = io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                try:
                    code = main()
                except SystemExit as exc:
                    code = exc.code if isinstance(exc.code, int) else 1
        finally:
            sys.argv = old_argv
        return SimpleNamespace(returncode=code, stdout=stdout.getvalue(), stderr=stderr.getvalue())

    def test_c_extension_and_deterministic_dumps(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source with spaces.c"
            path.write_text("int main(void){int x=1; return x-1;}")
            checked = self.run_exact_path(path, "--check")
            self.assertEqual(checked.returncode, 0, checked.stderr)
            outputs = {}
            for option in ("--dump-tokens", "--dump-ast", "--dump-symbols", "--dump-ir", "--emit-backend-ir"):
                first = self.run_exact_path(path, option)
                second = self.run_exact_path(path, option)
                self.assertEqual(first.returncode, 0, first.stderr)
                self.assertEqual(first.stdout, second.stdout)
                outputs[option] = first.stdout
            self.assertIn("target triple", outputs["--emit-backend-ir"])

    def test_command_line_error_statuses(self):
        from cminor.driver import main
        old_argv = sys.argv
        try:
            sys.argv = ["cminorcc"]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as missing:
                    main()
            self.assertEqual(missing.exception.code, 2)
        finally:
            sys.argv = old_argv
        result = self.run_source("int main(void){return 0;}", "--check", "--dump-ir")
        self.assertEqual(result.returncode, 2)

    def test_cli_capabilities_and_backend_selection(self):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(ROOT)
        cap = subprocess.run([sys.executable, "-m", "cminor", "--capabilities"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(cap.returncode, 0)
        self.assertIn("LLVM llc", cap.stdout)
        self.assertIn("Preprocessing: disabled", cap.stdout)
        qbe = subprocess.run([sys.executable, "-m", "cminor", "--backend=qbe", "x.cm"], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertEqual(qbe.returncode, 2)

    def test_failed_backend_preserves_existing_output_when_llc_missing(self):
        if shutil.which("llc"):
            self.skipTest("llc is installed; missing-backend preservation case is not applicable")
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.cm"
            output = Path(directory) / "existing.s"
            source.write_text("int main(void){return 0;}")
            output.write_text("preserve")
            env = os.environ.copy()
            env["PYTHONPATH"] = str(ROOT)
            env["PATH"] = ""
            result = subprocess.run([sys.executable, "-m", "cminor", str(source), "-o", str(output)], cwd=ROOT, env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn("BACKEND_ERROR", result.stderr)
            self.assertEqual(output.read_text(), "preserve")


    def test_compulsory_resource_limits(self):
        valid_blocks = "int main(void){" + "{" * 15 + "}" * 15 + "return 0;}"
        invalid_blocks = "int main(void){" + "{" * 16 + "}" * 16 + "return 0;}"
        self.assertEqual(self.run_source(valid_blocks, "--check").returncode, 0)
        self.assertIn("LIMIT_ERROR", self.run_source(invalid_blocks, "--check").stderr)
        valid_expr = "int main(void){return " + "(" * 16 + "1" + ")" * 16 + ";}"
        invalid_expr = "int main(void){return " + "(" * 17 + "1" + ")" * 17 + ";}"
        self.assertEqual(self.run_source(valid_expr, "--check").returncode, 0)
        self.assertIn("LIMIT_ERROR", self.run_source(invalid_expr, "--check").stderr)
        valid_unary = "int main(void){return " + "+ " * 16 + "1;}"
        invalid_unary = "int main(void){return " + "+ " * 17 + "1;}"
        self.assertEqual(self.run_source(valid_unary, "--check").returncode, 0)
        self.assertIn("LIMIT_ERROR", self.run_source(invalid_unary, "--check").stderr)
        declarations = "".join(f"int v{i};" for i in range(64))
        self.assertEqual(self.run_source(f"int main(void){{{declarations}return 0;}}", "--check").returncode, 0)
        declarations = "".join(f"int v{i};" for i in range(65))
        self.assertIn("LIMIT_ERROR", self.run_source(f"int main(void){{{declarations}return 0;}}", "--check").stderr)
        functions = "".join(f"void f{i}(void){{return;}}" for i in range(31)) + "int main(void){return 0;}"
        self.assertEqual(self.run_source(functions, "--check").returncode, 0)
        functions = "".join(f"void f{i}(void){{return;}}" for i in range(32)) + "int main(void){return 0;}"
        self.assertIn("LIMIT_ERROR", self.run_source(functions, "--check").stderr)
        exact_tokens = "int main(void){" + "1;\n" * 1995 + "return 0;}"
        over_tokens = "int main(void){" + "1;\n" * 1996 + "return 0;}"
        self.assertEqual(self.run_source(exact_tokens, "--check").returncode, 0)
        self.assertIn("LIMIT_ERROR", self.run_source(over_tokens, "--check").stderr)
        line_ok = "int main(void){return 0;}\n" + " " * 2048
        line_bad = "int main(void){return 0;}\n" + " " * 2049
        self.assertEqual(self.run_source(line_ok, "--check").returncode, 0)
        self.assertIn("LIMIT_ERROR", self.run_source(line_bad, "--check").stderr)
        base = "int main(void){return 0;}"
        remaining = 32768 - len(base.encode("ascii")) - 1
        full_lines = remaining // 2048
        remainder = remaining % 2048
        exact_bytes = base + "\n" + (" " * 2047 + "\n") * full_lines + " " * remainder
        self.assertEqual(len(exact_bytes.encode("ascii")), 32768)
        self.assertEqual(self.run_source(exact_bytes, "--check").returncode, 0)
        self.assertIn("LIMIT_ERROR", self.run_source(exact_bytes + " ", "--check").stderr)

    def test_flat_binary_chain_with_500_operands(self):
        source = "int main(void){return " + "+".join(["1"] * 500) + ";}"

        for option in ("--check", "--dump-ir", "--emit-backend-ir"):
            with self.subTest(option=option):
                result = self.run_source(source, option, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_backend_process_failure_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake = root / "llc"
            fake.write_text("#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo 'LLVM version 23.1.3-test'; exit 0; fi\nexit 7\n")
            fake.chmod(0o755)
            source = root / "input.cm"
            output = root / "existing.s"
            source.write_text("int main(void){return 0;}")
            output.write_text("keep-existing-assembly")
            with patch.dict(os.environ, {"PATH": str(root)}):
                result = self.run_exact_path(source, "-o", str(output))
            self.assertEqual(result.returncode, 1)
            self.assertIn("BACKEND_ERROR", result.stderr)
            self.assertIn("exit_status=7", result.stderr)
            self.assertEqual(output.read_text(), "keep-existing-assembly")

    def test_unwritable_output_directory_reports_io_error_and_preserves_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            locked = root / "locked"
            locked.mkdir()
            source = root / "input.cm"
            output = locked / "existing.s"
            source.write_text("int main(void){return 0;}")
            output.write_text("keep-existing-assembly")

            locked.chmod(0o555)
            try:
                result = self.run_exact_path(source, "-o", str(output))
            finally:
                locked.chmod(0o755)

            self.assertEqual(result.returncode, 1)
            self.assertIn("IO_ERROR", result.stderr)
            self.assertNotIn("BACKEND_ERROR", result.stderr)
            self.assertEqual(output.read_text(), "keep-existing-assembly")

    def test_llvm_ir_verifies_with_llvm_tools(self):
        assembler = shutil.which("llvm-as-23") or shutil.which("llvm-as")
        verifier = shutil.which("opt-23") or shutil.which("opt")

        if not assembler or not verifier:
            self.skipTest("LLVM assembler or opt verifier is unavailable")

        source = (
            "int f(int n); "
            "int main(void){"
            "int x=0; "
            "if(0&&(x=f(2)))x=1; "
            "if(1||(x=f(3)))x=2; "
            "return x-2;"
            "} "
            "int f(int n){if(n==0)return 0;return n;}"
        )

        with tempfile.TemporaryDirectory() as directory:
            ir_path = Path(directory) / "verification.ll"
            bitcode_path = Path(directory) / "verification.bc"

            result = self.run_source(source, "--emit-backend-ir")
            self.assertEqual(result.returncode, 0, result.stderr)
            ir_path.write_text(result.stdout, encoding="utf-8")

            assembled = subprocess.run(
                [assembler, str(ir_path), "-o", str(bitcode_path)],
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(assembled.returncode, 0, assembled.stderr)

            verified = subprocess.run(
                [verifier, "-passes=verify", "-disable-output", str(bitcode_path)],
                capture_output=True,
                text=True,
                timeout=15,
            )
            self.assertEqual(verified.returncode, 0, verified.stderr)

    def test_llvm_ir_verifies_when_llvmlite_is_available(self):
        try:
            from llvmlite import binding as llvm
        except ImportError:
            self.skipTest("optional llvmlite verifier is unavailable")
        source = "int f(int n); int main(void){int x=0; if(0&&(x=f(2)))x=1; if(1||(x=f(3)))x=2; return x-2;} int f(int n){if(n==0)return 0;return n;}"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "input.cm"
            path.write_text(source)
            result = self.run_source(source, "--emit-backend-ir")
            self.assertEqual(result.returncode, 0, result.stderr)
            module = llvm.parse_assembly(result.stdout)
            module.verify()

if __name__ == "__main__":
    unittest.main()
