# C Minor Compiler

A Python implementation of the C Minor language profile in `C_Minor_Compiler_SRS_v1_0.pdf`. The selected native backend is LLVM `llc`. The compiler owns the scanner, parser, AST, semantic analysis, symbol tables, student intermediate representation, and LLVM IR lowering.

## Prerequisites

- Python 3.10 or newer
- Linux x86-64
- LLVM `llc`; LLVM 23.1.3 is the SRS reference release
- GNU GCC driver and GNU Binutils for assembling and linking generated assembly

The compiler implementation uses only the Python standard library. `llc`, GCC, the assembler, and the system linker are external tools. No C Minor preprocessor, project runtime, C frontend, or third-party compiler translation library is used.

## Toolchain sources

See [`docs/TOOLCHAIN.md`](docs/TOOLCHAIN.md) for dependency roles, reference versions, official download sources and reproducible verification commands.

## Quick start

Run commands from the project root:

```sh
python3 --version
llc --version
gcc --version
./cminorcc --capabilities
./cminorcc --check examples/acceptance_b1.cm
./cminorcc examples/acceptance_b2.cm -o acceptance_b2.s
gcc -c acceptance_b2.s -o acceptance_b2.o
gcc -no-pie acceptance_b2.o -o acceptance_b2
./acceptance_b2
printf 'exit=%s\n' "$?"
```

The normal compiler command produces GNU-compatible x86-64 assembly. It does not assemble or link the result. The separate commands above demonstrate the required `.s` to `.o` to executable path.

## Compiler commands

```sh
./cminorcc input.cm -o output.s
./cminorcc input.c
./cminorcc --check input.cm
./cminorcc --dump-tokens input.cm
./cminorcc --dump-ast input.cm
./cminorcc --dump-symbols input.cm
./cminorcc --dump-ir input.cm
./cminorcc --emit-backend-ir input.cm
./cminorcc --emit-backend-ir input.cm -o output.ll
./cminorcc --capabilities
./cminorcc --version
./cminorcc --help
```

`--emit-backend-ir` writes LLVM IR to standard output unless `-o PATH` is supplied. Stage dumps and `--check` do not invoke `llc` and do not create assembly. `--backend=llvm` is the only supported backend selection. QBE is not listed or selectable.

Exit status is 0 for a successful action, 1 for source, I/O, unsupported-feature, compiler, or backend failure, and 2 for command-line misuse. Diagnostics are written to standard error.

## C Minor profile

The compiler implements the compulsory subset rather than complete ISO C23:

- Signed 32-bit `int`; `void` only for function return types and the sole empty-parameter marker.
- Decimal integer literals from 0 through 2147483647.
- Identifiers, local scalar declarations, nested blocks, shadowing and parameters.
- `+`, `-`, `*`, `/`, `%`, comparisons, equality, `!`, `&&`, `||`, assignment, and direct named function calls.
- `if`/`else`, `while`, `for`, `break`, `continue`, expression statements and `return`.
- Prototypes, definitions, 0 through 6 integer parameters, direct calls, recursion and mutual recursion when declarations precede calls.
- `//` and non-nested `/* ... */` comments, ASCII whitespace, LF and CRLF.

The baseline excludes globals, arrays, pointers, aggregates, additional scalar types, casts, strings, character literals, variadic functions, external calls, function pointers, preprocessing, line splicing, `do-while`, `switch`, labels, `goto`, compound assignments, increment/decrement, bitwise operators, shifts, the conditional operator and comma expressions. Every function declaration must have one compatible definition in the same source file. Exactly one `int main(void)` definition is required. Every `int` function must end with a top-level `return` expression.

Preprocessing is disabled. A source file is exactly one self-contained `.cm` or `.c` file. The compiler never sends source C Minor text to GCC or Clang.

## Build and test

No package installation is required. The source is directly runnable with Python:

```sh
python3 -m unittest discover -s tests -v
```

The suite includes positive and negative language cases, 100 malformed-input mutations with a five-second per-case timeout, limit-boundary checks, CLI checks, output-preservation checks, and LLVM IR verification when the optional local `llvmlite` verifier is available. `llvmlite` is not a runtime dependency and is not used as a backend.

The integration test below uses the approved backend, assembler, and linker when they are installed:

```sh
python3 -m unittest discover -s tests -p 'test_integration.py' -v
```

The native toolchain has been tested in the target Linux x86-64 environment. The verified environment uses Python 3.12.3, LLVM llc 23.1.6, GCC 13.3.0, and GNU Binutils 2.42. The full test suite completed with 15 passed, 2 skipped, and 0 failed (17 tests total). The native integration test assembled, linked, and executed all ten native programs successfully; each returned exit status 0. The optional llvmlite verifier test was skipped because llvmlite is unavailable; LLVM IR verification also passed using llvm-as-23 and opt-23. See `docs/TEST_RESULTS.md` for the recorded results.

## Project structure

- `cminor/lexer.py`: handwritten scanner and token source positions
- `cminor/parser.py`: recursive-descent grammar and AST construction
- `cminor/ast_nodes.py`: source-spanned AST node model
- `cminor/semantic.py`: function signatures, scopes, name/type checks, resolution and symbol dump
- `cminor/ir.py`: independent three-address student IR and control-flow lowering
- `cminor/llvm_backend.py`: student IR to textual LLVM IR transformation
- `cminor/driver.py`: CLI, diagnostics, external backend invocation and atomic assembly output
- `tests/`: positive, negative, robustness, limits and integration tests
- `examples/`: acceptance and demonstration inputs
- `docs/`: user guide, developer report, test status and requirement traceability

## Academic integrity

This project was produced with AI assistance. Disclose that assistance, review reused material and licences, and follow the institution's course rules. Every team member must understand and be able to explain the compulsory compiler stages and demonstrate ownership of the implementation during review.

## Change control

C Minor Compiler SRS Version 1.0 is the compulsory project baseline.
Any change to compulsory requirements, the accepted grammar, approved
tool families, reference target, or acceptance criteria requires a
documented course-wide amendment before the affected work is evaluated.
Optional features do not replace or excuse any compulsory requirement.
