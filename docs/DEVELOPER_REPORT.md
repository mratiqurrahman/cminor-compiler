# Developer Report

## Architecture

The compiler is a modular Python package with a handwritten frontend and a separately inspectable student IR. It uses only Python standard-library facilities at runtime. The only native code-generation backend exposed by the driver is LLVM `llc`.

## Lexer and token model

`cminor/lexer.py` performs a character-by-character scan. Every token records its source path and one-based start and end coordinates. The lexer recognizes the compulsory keywords, ASCII identifiers, decimal integer literals, punctuation, operators, line comments and non-nested block comments. Longest two-character matching is applied to `<=`, `>=`, `==`, `!=`, `&&` and `||`. Unsupported operators and literal forms receive controlled diagnostics. Preprocessing directives and backslash-newline splicing are rejected; there is no preprocessing stage.

The scanner enforces byte, token and line-length limits. LF and CRLF are treated as line endings. Comment text does not create tokens, and comments preserve token boundaries.

## Grammar and AST

`cminor/parser.py` is a recursive-descent parser for the EBNF productions in Appendix A. It implements right-associative assignment and left-associative binary precedence levels. The AST classes in `cminor/ast_nodes.py` represent prototypes, definitions, parameters, blocks, declarations, statements, literals, identifiers, parenthesized expressions, unary and binary expressions, assignments and calls. Nodes retain source spans. Parentheses remain explicit in the tree so the AST dump preserves grouping.

## Scope and semantic analysis

`cminor/semantic.py` maintains the visible file-level function declarations and a stack of lexical variable scopes. A function becomes visible at its declaration or definition; a definition is registered before its body is analyzed, enabling self-recursion. A function call is resolved only against declarations already visible at that source position. Prototypes support forward and mutual recursion.

Parameters share the function body's outer scope. Nested blocks create scopes and permit shadowing. A `for` statement creates a scope for its initializer declaration. The semantic pass verifies declaration uniqueness, call counts, value categories, assignment lvalues, return forms, loop-only jump statements, compatible prototypes and definitions, the required `main` signature, unresolved functions and the final top-level return restriction.

Expression analysis records result categories and lvalue identities. Variable and call resolution relationships are retained for `--dump-symbols`.

## Student IR

`cminor/ir.py` lowers the AST to a three-address control-flow IR that is independent of LLVM IR. It includes constants, loads, stores, unary and binary operations, boolean control flow, labels, branches, jumps, calls, parameter bindings, returns and phi-style merge values for short-circuit expressions. Variables use unique semantic symbol identities; temporaries and labels are deterministic within each function.

The lowering pass creates explicit condition, body, update and exit blocks for loops. `continue` targets the loop condition for `while` and the update block for `for`. Short-circuit expressions branch around the right operand and merge normalized integer results.

## LLVM lowering and native backend

`cminor/llvm_backend.py` is the student-authored conversion from the student IR to textual LLVM IR. Source values and function parameters use `i32`; comparisons use `icmp` and `zext` to produce integer 0/1 values; signed division and remainder use `sdiv` and `srem`; branch tests use `i1`. Variables are represented by entry-block `alloca` storage and loads/stores. Function calls and returns are emitted with the declared `i32` or `void` type.

`cminor/driver.py` invokes `llc` with structured process arguments and the SRS baseline flags: `-O0 -mtriple=x86_64-pc-linux-gnu -filetype=asm`. It does not invoke GCC or Clang on C Minor input. GNU GCC and Binutils are reserved for generated `.s` and `.o` files. Assembly replacement is atomic: a temporary assembly file is created in the destination directory and replaces the output only after successful backend completion.

## Error handling and reproducibility

The driver separates command-line misuse from source and external-tool failures. Source diagnostics contain a stable category, source location and concise message. Output dumps and IR generation are deterministic for an identical input path and compiler/toolchain configuration. External processes receive argument arrays rather than source-derived shell command strings.

## Build, tests and evidence

The compiler is directly runnable with Python 3.10 or newer and does not need a Python package installation. `python3 -m unittest discover -s tests -v` runs the local suite. The tests include 60 positive and 78 negative source-profile cases, 100 distinct malformed mutations with per-case timeout handling, limit-boundary checks, CLI actions, output preservation and LLVM IR verification using the installed native LLVM assembler and verifier, plus an optional `llvmlite` verifier check.

The tested WSL2 Ubuntu 24.04.5 environment contains Python 3.12.3, LLVM `llc` 23.1.6, GCC 13.3.0 and GNU Binutils 2.42. The native integration test compiled ten native programs: five acceptance programs, the expression semantics test, the statement control-flow test, the for-continue update test, the function coverage test, and the statement edge-coverage test. The function coverage test exercises mutual recursion and a six-argument function. It generated assembly with `llc`, assembled and linked them with GCC, and ran all ten executables successfully; each returned exit status 0. The full test suite completed with 16 passed, 2 skipped and 0 failed (18 tests total). The new automated LLVM verification test successfully assembled emitted IR with `llvm-as-23` and verified its bitcode using `opt-23 -passes=verify`. The separate optional `llvmlite` verifier test was skipped because `llvmlite` is unavailable; `llvmlite` is not a runtime dependency.

## Reused components and disclosure

Runtime implementation: Python standard library only. Native backend: LLVM `llc`. Assembly/linking: GCC driver and installed GNU Binutils. No C parser, C semantic checker, C-to-LLVM translator, student-IR lowering library, source preprocessor or project runtime is used. AI assistance was used to prepare this implementation and must be disclosed under the applicable course academic-integrity rules.
