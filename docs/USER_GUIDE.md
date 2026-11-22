# User Guide

## Environment

The reference target is Linux x86-64, System V AMD64 ABI and ELF. Python 3.10 or newer runs the compiler driver. LLVM `llc` is the selected native backend; version 23.1.3 is the SRS reference, and version 23.1.6 was used for the current verification. GNU GCC and GNU Binutils provide assembly and linking.

## Compilation workflow

1. Run `./cminorcc --check program.cm` to validate tokens, syntax and semantics without invoking a backend.
2. Run `./cminorcc --dump-tokens program.cm` to inspect lexical tokens.
3. Run `./cminorcc --dump-ast program.cm` to inspect the source-spanned syntax tree.
4. Run `./cminorcc --dump-symbols program.cm` to inspect functions, variable scopes and name resolutions.
5. Run `./cminorcc --dump-ir program.cm` to inspect the independent student IR.
6. Run `./cminorcc --emit-backend-ir program.cm -o program.ll` to write LLVM IR.
7. Run `./cminorcc program.cm -o program.s` to invoke `llc` and generate assembly.
8. Run `gcc -c program.s -o program.o`, then `gcc -no-pie program.o -o program` and `./program` to assemble, link and execute.

A normal compile defaults to `program.s` for `program.cm` or `program.c`. `-o` sets the destination. Backend output is written to a temporary file and replaces the requested `.s` only after a successful `llc` run.

## Normative grammar (SRS Appendix A)

The following EBNF is the compulsory C Minor grammar from SRS Version 1.0, Appendix A.

### Declarations and statements

```ebnf
program                   = { external } ;
external                  = function_decl | function_def ;
return_type               = "int" | "void" ;
function_decl             = return_type identifier "(" prototype_params ")" ";" ;
function_def              = return_type identifier "(" definition_params ")" block ;
prototype_params          = "void" | prototype_param { "," prototype_param } ;
prototype_param           = "int" [ identifier ] ;
definition_params         = "void" | definition_param { "," definition_param } ;
definition_param          = "int" identifier ;
local_decl                = "int" identifier [ "=" assignment_expr ] ";" ;
block                     = "{" { block_item } "}" ;
block_item                = local_decl | statement ;
statement                 = block | expr_stmt | if_stmt | while_stmt | for_stmt
                          | "break" ";" | "continue" ";"
                          | "return" [ assignment_expr ] ";" ;
expr_stmt                 = [ assignment_expr ] ";" ;
if_stmt                   = "if" "(" assignment_expr ")" statement
                          [ "else" statement ] ;
while_stmt                = "while" "(" assignment_expr ")" statement ;
for_stmt                  = "for" "(" for_init [ assignment_expr ] ";"
                          [ assignment_expr ] ")" statement ;
for_init                  = local_decl | [ assignment_expr ] ";" ;

```

### Expressions and lexical forms

```ebnf
assignment_expr           = logical_or [ "=" assignment_expr ] ;
logical_or                = logical_and { "||" logical_and } ;
logical_and               = equality { "&&" equality } ;
equality                  = relational { ( "==" | "!=" ) relational } ;
relational                = additive { ( "<" | "<=" | ">" | ">=" ) additive } ;
additive                  = multiplicative { ( "+" | "-" ) multiplicative } ;
multiplicative            = unary { ( "*" | "/" | "%" ) unary } ;
unary                     = ( "+" | "-" | "!" ) unary | primary ;
primary                   = integer_literal | identifier [ "(" [ arg_list ] ")" ]
                          | "(" assignment_expr ")" ;
arg_list                  = assignment_expr { "," assignment_expr } ;
identifier                = (ASCII letter | "_") { ASCII letter | digit | "_" } ;
integer_literal           = "0" | ("1" ... "9") { "0" ... "9" } ;

```

### Semantic restrictions

- Assignment-এর বাম পাশটি identifier lvalue হতে হবে, প্রয়োজনে parentheses-এ থাকতে পারে।
- Function call-এর আগে function দৃশ্যমান হতে হবে এবং definition সামঞ্জস্যপূর্ণ হতে হবে।
- Global object declaration অনুমোদিত নয়।
- ঠিক একটি `int main(void)` definition থাকতে হবে।
- Function-এ সর্বোচ্চ ছয়টি integer parameter থাকতে পারে।
- প্রতিটি `int` function-এর শেষ top-level block item-এ return expression থাকতে হবে।
- Zero-argument function declaration ও definition-এ `(void)` ব্যবহার করতে হবে; function call-এ `name()` ব্যবহার করতে হবে।

## CLI actions

| Action | Result |
|---|---|
| `--check` | Run through semantic analysis; no native backend invocation |
| `--dump-tokens` | Deterministic token dump to standard output |
| `--dump-ast` | Deterministic source-spanned AST dump |
| `--dump-symbols` | Function and variable symbols plus resolution relationships |
| `--dump-ir` | Deterministic student IR dump |
| `--emit-backend-ir` | LLVM IR to standard output or `-o PATH` |
| `--capabilities` | Language profile, target, backend, version and limits |
| `--version` | Compiler version |
| `--help` | CLI help |

These actions are mutually exclusive. `--backend=llvm` is supported; QBE is not implemented in this release.

No student-authored optimization passes are implemented; the LLVM backend is invoked with `-O0`.

## Language rules

A translation unit consists only of function prototypes and definitions. Exactly one `int main(void)` definition is required. Other declared functions need one compatible definition in the same file. Functions accept up to six `int` parameters. A function must be declared before a call to it; self-recursion works, and mutual recursion requires earlier prototypes.

The only object and expression value type is signed 32-bit `int`. `void` is permitted only as a function result or as `void` in an empty parameter list. Local declarations declare one scalar name and may include an initializer. A nested block may shadow an outer declaration but may not redeclare a name in the same scope. A `for` initializer declaration is scoped to that loop.

Expressions follow the SRS precedence order: unary; multiplicative; additive; relational; equality; logical AND; logical OR; assignment. Assignment associates right-to-left. Other binary operators associate left-to-right. Evaluation is left-to-right for binary operands and call arguments; an assignment evaluates its right side before storing. `&&` and `||` short-circuit. Comparisons, equality, logical operators and `!` yield 0 or 1.

Integer division truncates toward zero and remainder uses signed remainder semantics. Overflow, division by zero, `INT_MIN / -1` and reads of uninitialized automatic integers are undefined; tests should avoid those cases.

An `int` function, including `main`, must have an explicit top-level final `return` with an integer expression. Earlier returns are permitted. A `void` function uses `return;` and may reach its closing brace.

## Exclusions and limits

The baseline excludes preprocessing, source line splicing, globals, arrays, pointers, structures, unions, floating point, `char`, `bool`, unsigned types, strings, character literals, casts, function pointers, variadic functions, external functions and separate translation units. It also excludes `do-while`, `switch`, `goto`, labels, increment/decrement, compound assignments, bitwise operators, shifts, `?:` and the comma operator.

The enforced implementation limits are 32768 input bytes, 4000 tokens, 2048 characters per line, 16 block nesting levels, 16 expression nesting levels, 32 function definitions, six parameters per function and 64 local declarations per block. Exceeding a declared limit produces a controlled `LIMIT_ERROR`.

## Diagnostics and exit statuses

Diagnostics include a stable category, severity, source path, one-based line and column, and a concise message. Related declaration locations are shown where available. External backend errors include the command, arguments and exit status when the process was executed.

- 0: successful requested action
- 1: source, I/O, unsupported-feature, compiler or backend failure
- 2: invalid command line or incompatible action selection

Standard output is reserved for requested dumps or LLVM IR. Diagnostics are written to standard error.
