# Third-Party Tools and License Notices

This document records the external tools used to build and verify the C Minor Compiler. These tools are system dependencies; this project does not bundle or redistribute their binaries or source code.

## Tool inventory

| Tool | Verified version | Role | License information |
|---|---|---|---|
| Python | 3.12.3 | Runs the compiler implementation and driver | Python License (PSF); see the installed package copyright notice. |
| LLVM llc | 23.1.6 | Converts generated LLVM IR into x86-64 assembly | Apache License 2.0 with LLVM Exceptions. |
| GCC driver | 13.3.0 | Assembles generated assembly and links object files | GCC components have component-specific licensing; consult the installed GCC copyright notice. |
| GNU Binutils | 2.42 | Provides GNU assembler and linker tools | GNU GPL version 3 or later, according to the installed package copyright notice. |

The versions were observed in WSL2 Ubuntu 24.04.5 on 21 November 2026. The SRS reference LLVM version is 23.1.3; the version used for current verification is 23.1.6.

## Local license notices

The inspected Debian/Ubuntu package notices are:

- /usr/share/doc/python3.12/copyright
- /usr/share/doc/llvm-23/copyright
- /usr/share/doc/gcc-13/copyright
- /usr/share/doc/binutils/copyright

Common license texts, where provided, are available under /usr/share/common-licenses/. Consult each package copyright file for exact terms, file-level exceptions and additional notices.

## Optional development tooling

llvmlite is not imported by the compiler and is not a runtime dependency. Its optional verifier test is skipped when unavailable.

## Project implementation and assistance disclosure

The compiler is implemented in Python and uses the Python standard library at runtime. LLVM llc is an external backend. GCC and GNU Binutils are used only for assembling and linking compiler-generated native files; C Minor source files are not compiled by GCC or Clang.

AI assistance was used during implementation and documentation. This assistance must be disclosed according to the applicable course academic-integrity rules. The student remains responsible for understanding, validating and explaining the submitted implementation.

## Scope

This document inventories third-party tools and points to their installed license notices. It does not grant a new license for this project. No project-level license is asserted here. If third-party binaries or source are redistributed, review and comply with their applicable license obligations.
