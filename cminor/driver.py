import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from .diagnostics import CompilerError, CompilerErrors, Diagnostic, Location, format_diagnostic
from .lexer import Lexer
from .parser import Parser
from .semantic import SemanticAnalyzer
from .ir import IRLowerer, dump_ir
from .llvm_backend import emit_llvm
from .ast_dump import dump_ast

VERSION = "1.0.0"
BACKEND = "llvm"

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(2, f"cminorcc: COMMAND_ERROR: {message}\n")

def make_parser():
    parser = ArgumentParser(prog="cminorcc", add_help=False, description="C Minor compiler with a student-owned LLVM backend lowering stage.")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--check", action="store_true")
    actions.add_argument("--dump-tokens", action="store_true")
    actions.add_argument("--dump-ast", action="store_true")
    actions.add_argument("--dump-symbols", action="store_true")
    actions.add_argument("--dump-ir", action="store_true")
    actions.add_argument("--emit-backend-ir", action="store_true")
    actions.add_argument("--capabilities", action="store_true")
    actions.add_argument("--version", action="store_true")
    actions.add_argument("--help", action="store_true")
    parser.add_argument("--backend", choices=["llvm"], default="llvm")
    parser.add_argument("-o", dest="output")
    parser.add_argument("source", nargs="?")
    return parser

def source_error(code, message, path):
    return CompilerError(Diagnostic(code, message, Location(str(path), 1, 1)))

def read_source(path):
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise source_error("IO_ERROR", f"cannot read source file: {exc}", path)
    if len(data) > 32768:
        raise source_error("LIMIT_ERROR", "source exceeds the 32768-byte input limit", path)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as exc:
        prefix = data[:exc.start].decode("utf-8", errors="replace")
        line = prefix.count("\n") + 1
        column = len(prefix.rsplit("\n", 1)[-1]) + 1
        raise CompilerError(Diagnostic("LEXICAL_ERROR", "source must contain ASCII characters only", Location(str(path), line, column)))

def frontend(source_path):
    source = read_source(source_path)
    tokens = Lexer(source, source_path).scan()
    program = Parser(tokens).parse()
    semantics = SemanticAnalyzer().analyze(program)
    module_ir = IRLowerer(semantics).lower(program)
    return source, tokens, program, semantics, module_ir

def dump_tokens(tokens):
    lines = ["TOKENS"]
    for token in tokens:
        value = token.value.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
        lines.append(f"{token.path}:{token.line}:{token.column} {token.kind} {value!r}")
    return "\n".join(lines) + "\n"

def llc_version():
    executable = shutil.which("llc")
    if executable is None:
        return None, "unavailable"
    try:
        result = subprocess.run([executable, "--version"], capture_output=True, text=True, timeout=5, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return executable, f"unavailable ({exc})"
    output = (result.stdout or result.stderr).strip().splitlines()
    return executable, output[0] if output else f"exit status {result.returncode}"

def capabilities():
    executable, version = llc_version()
    lines = [
        "C Minor compiler capabilities",
        f"Compiler version: {VERSION}",
        "Language profile: C Minor SRS 1.0",
        "Target: x86_64-pc-linux-gnu; System V AMD64 ABI; ELF",
        "Supported backend: LLVM llc",
        f"LLVM backend executable: {executable or 'not found'}",
        f"LLVM backend version: {version}",
        "Accepted source files: one self-contained .cm or .c file",
        "Value type: signed 32-bit int; void function return only",
        "Functions: 0-6 int parameters; exactly one int main(void) definition",
        "Resource limits: 32768 bytes; 4000 tokens; 2048 characters per line; 16 block levels; 16 expression levels; 32 function definitions; 64 locals per block",
        "Preprocessing: disabled; directives and line splicing rejected",
        "Optional extensions: none",
        "Optimization: student optimization passes not implemented; backend flags use -O0"
    ]
    return "\n".join(lines) + "\n"

def write_atomic(path, content, binary=False):
    destination = Path(path)
    parent = destination.parent if str(destination.parent) else Path(".")
    if not parent.exists() or not parent.is_dir():
        raise source_error("IO_ERROR", f"output directory does not exist: {parent}", path)
    try:
        fd, temp_name = tempfile.mkstemp(prefix=f".{destination.name}.", suffix=".tmp", dir=str(parent))
        if binary:
            stream = os.fdopen(fd, "wb")
        else:
            stream = os.fdopen(fd, "w", encoding="utf-8", newline="\n")
        with stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, destination)
    except OSError as exc:
        try:
            if "temp_name" in locals() and os.path.exists(temp_name):
                os.unlink(temp_name)
        except OSError:
            pass
        raise source_error("IO_ERROR", f"cannot write output file: {exc}", path)

def compile_to_assembly(module_ir, output_path):
    executable, version = llc_version()
    if executable is None:
        command = ["llc", "-no-integrated-as", "-O0", "-mtriple=x86_64-pc-linux-gnu", "-filetype=asm", "module.ll", "-o", "module.s"]
        raise source_error("BACKEND_ERROR", f"tool=llc command={command!r}; exit_status=not_started; executable was not found", output_path)
    destination = Path(output_path)
    parent = destination.parent if str(destination.parent) else Path(".")
    if not parent.exists() or not parent.is_dir():
        raise source_error("IO_ERROR", f"output directory does not exist: {parent}", output_path)
    llvm_text = emit_llvm(module_ir)
    try:
        with tempfile.TemporaryDirectory(prefix="cminorcc-", dir=str(parent)) as temp_dir:
            ir_path = Path(temp_dir) / "module.ll"
            asm_path = Path(temp_dir) / "module.s"
            ir_path.write_text(llvm_text, encoding="utf-8")
            command = [executable, "-no-integrated-as", "-O0", "-mtriple=x86_64-pc-linux-gnu", "-filetype=asm", str(ir_path), "-o", str(asm_path)]
            result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
            if result.returncode != 0 or not asm_path.is_file():
                detail = (result.stderr or result.stdout or "no diagnostic output").strip()
                raise source_error("BACKEND_ERROR", f"LLVM llc failed; command={command!r}; exit_status={result.returncode}; output={detail}", output_path)
            data = asm_path.read_bytes()
            write_atomic(output_path, data, binary=True)
    except subprocess.TimeoutExpired:
        raise source_error("BACKEND_ERROR", f"tool=llc command={command!r}; exit_status=timeout; timed out after 30 seconds", output_path)
    except OSError as exc:
        raise source_error("IO_ERROR", f"cannot write output file: {exc}", output_path)

def run(argv=None):
    parser = make_parser()
    args = parser.parse_args(argv)
    if args.help:
        parser.print_help()
        return 0
    if args.version:
        print(f"cminorcc {VERSION}")
        return 0
    if args.capabilities:
        print(capabilities(), end="")
        return 0
    if not args.source:
        parser.error("exactly one .cm or .c source file is required")
    if Path(args.source).suffix not in (".cm", ".c"):
        parser.error("source file must have .cm or .c extension")
    if args.dump_tokens:
        tokens = Lexer(read_source(args.source), args.source).scan()
        print(dump_tokens(tokens), end="")
        return 0
    if args.dump_ast:
        source_text = read_source(args.source)
        tokens = Lexer(source_text, args.source).scan()
        program = Parser(tokens).parse()
        print(dump_ast(program), end="")
        return 0
    source_text = read_source(args.source)
    tokens = Lexer(source_text, args.source).scan()
    program = Parser(tokens).parse()
    semantics = SemanticAnalyzer().analyze(program)
    if args.dump_symbols:
        print(semantics.dump_symbols(), end="")
        return 0
    if args.check:
        return 0
    module_ir = IRLowerer(semantics).lower(program)
    if args.dump_ir:
        print(dump_ir(module_ir), end="")
        return 0
    if args.emit_backend_ir:
        output = emit_llvm(module_ir)
        if args.output:
            write_atomic(args.output, output)
        else:
            sys.stdout.write(output)
        return 0
    output_path = args.output or str(Path(args.source).with_suffix(".s"))
    compile_to_assembly(module_ir, output_path)
    return 0

def main():
    try:
        return run()
    except CompilerErrors as exc:
        for diagnostic in exc.diagnostics:
            print(format_diagnostic(diagnostic), file=sys.stderr)
        return 1
    except CompilerError as exc:
        print(format_diagnostic(exc.diagnostic), file=sys.stderr)
        return 1
    except RecursionError:
        print("<compiler>:1:1: error LIMIT_ERROR: expression or syntax nesting exceeded the supported recursion limit", file=sys.stderr)
        return 1
    except MemoryError:
        print("<compiler>:1:1: error LIMIT_ERROR: compiler exhausted available memory", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("<compiler>:1:1: error COMMAND_ERROR: interrupted", file=sys.stderr)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
