# Toolchain and Dependencies

## Required components

| Component | Version policy | Role | Official source |
|---|---|---|---|
| Python | 3.10 or newer | Runs the compiler implementation; standard library only | https://www.python.org/downloads/ |
| LLVM `llc` | 23.1.3 is the SRS reference release | Translates the student-generated LLVM IR into GNU-compatible x86-64 assembly | https://discourse.llvm.org/t/llvm-23-1-3-released/92432 |
| GNU GCC driver | Installed Linux toolchain version | Assembles generated `.s` files and links generated `.o` files | https://gcc.gnu.org/ |
| GNU Binutils | Installed Linux toolchain version | Provides GNU assembler and linker components | https://sourceware.org/binutils/ |

The compiler runtime uses only the Python standard library. `llvmlite` was used as an optional local LLVM IR parser/verifier during development; it is not imported by the compiler and is not a required dependency.

## Installation checks

Run these commands after installing the toolchain:

```sh
python3 --version
llc --version
gcc --version
as --version
ld --version
./cminorcc --capabilities
```

The target is Linux x86-64, System V AMD64 ABI and ELF. Install the LLVM package that provides `llc` for the target. The SRS baseline invocation is `llc -O0 -mtriple=x86_64-pc-linux-gnu -filetype=asm`.

## Reproducible verification

```sh
python3 -m py_compile cminor/*.py tests/*.py
python3 -m unittest discover -s tests -v
python3 -m unittest discover -s tests -p 'test_integration.py' -v
```

The integration test invokes the compiler, `llc`, GNU assembler/linker through GCC, and the generated executables. Record the output of all version commands and each test command for the project submission. Do not pass C Minor source files to GCC or Clang.
