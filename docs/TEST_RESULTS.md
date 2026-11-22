# Test Results and Validation Status

## Local results

Command:

```sh
python3 -m unittest discover -s tests -v
```

Observed result in the WSL2 Ubuntu environment:

```text
Ran 18 tests
OK (skipped=2)

Result: 16 passed, 2 skipped, 0 failed.
```

The tested WSL2 Ubuntu 24.04.5 environment reported Python 3.12.3, LLVM `llc` 23.1.6, GCC 13.3.0 and GNU Binutils 2.42. The suite covers 60 positive source-profile cases and 78 negative source-profile cases. It also runs 100 distinct malformed source mutations with a five-second per-case timeout, checks the resource boundaries for byte size, token count, line length, block depth, expression depth, function count and locals per block, verifies CLI behavior, tests preservation of a pre-existing assembly output when backend processing fails, and IO_ERROR reporting with output preservation for an unwritable output directory.

The regression suite also verifies a 500-operand flat additive expression through `--check`, `--dump-ir` and `--emit-backend-ir`. A separate native execution check for a 500-operand expression returned the expected exit status 42.

The optional `llvmlite` verifier was unavailable, so its verification test was skipped. `llvmlite` is not a compiler runtime dependency and is not used for code generation. A separate automated test successfully assembled emitted LLVM IR with `llvm-as-23` and verified the resulting bitcode with `opt-23 -passes=verify`.

## Native backend validation

The native toolchain is installed and the integration test passed. The test compiled ten native programs: five acceptance programs, the expression semantics test, the statement control-flow test, the for-continue update test, the function coverage test, and the statement edge-coverage test. The function coverage test exercises mutual recursion and a six-argument function. The pipeline generated assembly through LLVM `llc`, assembled the output with GCC, linked native executables and ran them. All ten programs returned exit status 0.

The full test suite also passed: 16 tests passed, 2 were skipped and none failed. One skip applies because the missing-backend test is not applicable when `llc` is installed. The other applies because the optional `llvmlite` verifier is unavailable.






## Target integration test

With `llc`, GCC and GNU Binutils installed, run:

```sh
python3 -m unittest discover -s tests -p 'test_integration.py' -v
```

The integration test compiles the Appendix B examples through `cminorcc`, assembles generated `.s`, links the `.o`, runs each executable and checks for exit status 0.

## Tool command record

The backend command issued by the driver is:

```sh
llc -no-integrated-as -O0 -mtriple=x86_64-pc-linux-gnu -filetype=asm module.ll -o module.s
```

The reference assembly and link commands are:

```sh
gcc -c module.s -o module.o
gcc -no-pie module.o -o module
./module
printf 'exit=%s\n' "$?"
```

Recorded environment versions: Python 3.12.3, LLVM llc 23.1.6, GCC 13.3.0 and GNU Binutils 2.42. The full test suite ran 18 tests: 16 passed and 2 were skipped, with 0 failures. LLVM IR verification passed with `llvm-as-23` and `opt-23`. The native integration test passed for all ten native programs, each returning exit status 0.

## Reproducible command and exit-status record

This is a Python source project; no separate native build or package-install
step is required. Run all commands from the project root.

| Command | Expected/recorded result |
|---|---|
| `python3 --version` | Python 3.12.3; exit status 0 |
| `llc --version` | LLVM 23.1.6; exit status 0 |
| `gcc --version` | GCC 13.3.0; exit status 0 |
| `as --version` | GNU Binutils 2.42; exit status 0 |
| `ld --version` | GNU Binutils 2.42; exit status 0 |
| `python3 -m py_compile cminor/*.py tests/*.py` | Passed; exit status 0 |
| `python3 -m unittest discover -s tests -v` | 18 tests; 16 passed, 2 skipped, 0 failed; exit status 0 |
| `python3 -m unittest discover -s tests -p 'test_integration.py' -v` | Native integration passed; ten executables returned 0; test command exit status 0 |
| `llvm-as-23 module.ll -o module.bc` | LLVM IR assembled successfully; exit status 0 |
| `opt-23 -passes=verify module.bc -disable-output` | LLVM verifier passed; exit status 0 |

The native integration test performs the source-to-executable stages:
C Minor source -> compiler-generated LLVM IR -> LLVM-generated assembly ->
GCC assembly -> GCC linking -> executable. The test checks every executable's
main exit status. GCC is not used to compile C Minor or regenerated C source.

The commands above are reproducible verification instructions. The recorded
versions and results describe the tested WSL2 Ubuntu 24.04.5 environment.
