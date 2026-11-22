from .diagnostics import CompilerError, CompilerErrors, Diagnostic, Location
from . import ast_nodes as A

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = 0
        self.expression_depth = 0
        self.block_depth = 0
        self.errors = []

    def current(self):
        return self.tokens[self.index]

    def peek(self, offset=1):
        pos = min(self.index + offset, len(self.tokens) - 1)
        return self.tokens[pos]

    def advance(self):
        token = self.current()
        if token.kind != "EOF":
            self.index += 1
        return token

    def match(self, *kinds):
        if self.current().kind in kinds:
            return self.advance()
        return None

    def expect(self, kind, message=None):
        token = self.current()
        if token.kind != kind:
            self.error("SYNTAX_ERROR", message or f"expected {kind!r}, found {token.value or token.kind!r}")
        return self.advance()

    def error(self, code, message, token=None):
        token = token or self.current()
        raise CompilerError(Diagnostic(code, message, token.location()))

    def span(self, start, end=None):
        end = end or start
        return Location(start.path, start.line, start.column), Location(end.path, end.end_line, end.end_column)

    def parse(self):
        start = self.current()
        externals = []
        while self.current().kind != "EOF":
            before = self.index
            externals.append(self.parse_external())
            if self.index <= before:
                self.error("SYNTAX_ERROR", "parser made no progress")
        if not externals and not self.errors:
            self.error("SYNTAX_ERROR", "a compilation unit must contain at least one function declaration or definition")
        if self.errors:
            raise CompilerErrors(self.errors)
        first, last = self.span(start, self.tokens[-1])
        return A.Program(first, last, externals)

    def parse_type(self):
        token = self.current()
        if token.kind not in ("int", "void"):
            self.error("SYNTAX_ERROR", "expected return type 'int' or 'void'")
        self.advance()
        return token.value, token

    def parse_external(self):
        return_type, start = self.parse_type()
        if self.current().kind in ("(", "*"):
            self.error("UNSUPPORTED_FEATURE", "pointer and function-pointer declarations are outside C Minor")
        name = self.expect("IDENT", "expected function name")
        if self.current().kind in ("[", "*", "=") or self.current().kind == ";":
            self.error("UNSUPPORTED_FEATURE", "global objects, arrays and pointer declarations are outside C Minor", self.current())
        self.expect("(")
        params = self.parse_prototype_params(definition=False)
        self.expect(")")
        if self.match(";"):
            first, last = self.span(start, self.tokens[self.index - 1])
            return A.Function(first, last, return_type, name.value, params, False, None)
        body = self.parse_block()
        if any(p.name is None for p in params):
            self.error("SYNTAX_ERROR", "function definitions require a name for every parameter", name)
        first, last = self.span(start, self.tokens[self.index - 1])
        return A.Function(first, last, return_type, name.value, params, True, body)

    def parse_prototype_params(self, definition):
        if self.match("void"):
            return []
        params = []
        if self.current().kind == ")":
            self.error("SYNTAX_ERROR", "use '(void)' for a function with no parameters")
        while True:
            token = self.expect("int", "function parameters must have type int")
            name = None
            if self.current().kind in ("*", "["):
                self.error("UNSUPPORTED_FEATURE", "pointer and array parameters are outside C Minor", token)
            if self.current().kind == "IDENT":
                name = self.advance().value
                if self.current().kind == "[":
                    self.error("UNSUPPORTED_FEATURE", "array parameters are outside C Minor", token)
            elif definition:
                self.error("SYNTAX_ERROR", "function definition parameters require identifiers")
            first, last = self.span(token, self.tokens[self.index - 1])
            params.append(A.Parameter(first, last, name))
            if len(params) > 6:
                self.error("UNSUPPORTED_FEATURE", "functions may have at most six parameters", token)
            if not self.match(","):
                break
        return params

    def parse_block(self):
        start = self.expect("{", "expected '{' to begin block")
        self.block_depth += 1
        if self.block_depth > 16:
            self.error("LIMIT_ERROR", "block nesting exceeds 16 levels", start)
        items = []
        while self.current().kind not in ("}", "EOF"):
            before = self.index
            try:
                if self.current().kind == "int":
                    items.append(self.parse_local_decl())
                else:
                    items.append(self.parse_statement())
            except CompilerError as exc:
                if exc.diagnostic.code != "SYNTAX_ERROR":
                    raise
                self.errors.append(exc.diagnostic)
                self._synchronize_block()
            if self.index <= before and self.current().kind not in ("}", "EOF"):
                self.error("SYNTAX_ERROR", "parser made no progress in block")
        end = self.expect("}", "expected '}' to close block")
        self.block_depth -= 1
        first, last = self.span(start, end)
        return A.Block(first, last, items)

    def _synchronize_block(self):
        nested_braces = 0
        start = self.index
        while self.current().kind != "EOF":
            kind = self.current().kind
            if kind == "{" :
                nested_braces += 1
                self.advance()
                continue
            if kind == "}":
                if nested_braces == 0:
                    return
                nested_braces -= 1
                self.advance()
                continue
            if kind == ";" and nested_braces == 0:
                self.advance()
                return
            self.advance()
        if self.index == start and self.current().kind != "EOF":
            self.advance()

    def parse_local_decl(self):
        start = self.expect("int")
        if self.current().kind == "*":
            self.error("UNSUPPORTED_FEATURE", "pointer declarations are outside C Minor")
        name = self.expect("IDENT", "expected local variable name")
        if self.current().kind == "[":
            self.error("UNSUPPORTED_FEATURE", "array declarations are outside C Minor")
        initializer = None
        if self.match("="):
            initializer = self.parse_assignment()
        end = self.expect(";", "expected ';' after local declaration")
        first, last = self.span(start, end)
        return A.VarDecl(first, last, name.value, initializer)

    def parse_statement(self):
        if self.current().kind == "{":
            return self.parse_block()
        if token := self.match(";"):
            first, last = self.span(token)
            return A.ExprStmt(first, last, None)
        if token := self.match("if"):
            self.expect("(")
            condition = self.parse_assignment()
            self.expect(")")
            then_branch = self.parse_statement()
            else_branch = None
            if self.match("else"):
                else_branch = self.parse_statement()
            last_node = else_branch or then_branch
            return A.IfStmt(token.location(), last_node.end_location, condition, then_branch, else_branch)
        if token := self.match("while"):
            self.expect("(")
            condition = self.parse_assignment()
            self.expect(")")
            body = self.parse_statement()
            return A.WhileStmt(token.location(), body.end_location, condition, body)
        if token := self.match("for"):
            self.expect("(")
            initializer = None
            if self.current().kind == "int":
                initializer = self.parse_local_decl()
            else:
                if self.current().kind != ";":
                    initializer = self.parse_assignment()
                self.expect(";", "expected ';' after for initializer")
            condition = None if self.current().kind == ";" else self.parse_assignment()
            self.expect(";", "expected ';' after for condition")
            update = None if self.current().kind == ")" else self.parse_assignment()
            self.expect(")")
            body = self.parse_statement()
            return A.ForStmt(token.location(), body.end_location, initializer, condition, update, body)
        if token := self.match("break"):
            end = self.expect(";")
            first, last = self.span(token, end)
            return A.BreakStmt(first, last)
        if token := self.match("continue"):
            end = self.expect(";")
            first, last = self.span(token, end)
            return A.ContinueStmt(first, last)
        if token := self.match("return"):
            expression = None if self.current().kind == ";" else self.parse_assignment()
            end = self.expect(";", "expected ';' after return")
            first, last = self.span(token, end)
            return A.ReturnStmt(first, last, expression)
        if self.current().kind in ("void", "float", "double", "char", "long", "short", "unsigned", "struct"):
            self.error("UNSUPPORTED_FEATURE", f"declaration type {self.current().value!r} is outside C Minor")
        expression = None if self.current().kind == ";" else self.parse_assignment()
        end = self.expect(";", "expected ';' after expression statement")
        first, last = self.span(expression.location, self.tokens[self.index - 1]) if expression else self.span(end)
        return A.ExprStmt(first, last, expression)

    def parse_assignment(self):
        left = self.parse_logical_or()
        if self.match("="):
            operator_token = self.tokens[self.index - 1]
            self.expression_depth += 1
            try:
                if self.expression_depth > 16:
                    self.error("LIMIT_ERROR", "expression nesting exceeds 16 levels", operator_token)
                right = self.parse_assignment()
            finally:
                self.expression_depth -= 1
            return A.Assignment(left.location, right.end_location, left, right)
        return left

    def _binary_chain(self, lower, kinds):
        node = lower()
        while self.current().kind in kinds:
            op = self.advance()
            right = lower()
            node = A.Binary(node.location, right.end_location, op.value, node, right)
        return node

    def parse_logical_or(self):
        return self._binary_chain(self.parse_logical_and, {"||"})

    def parse_logical_and(self):
        return self._binary_chain(self.parse_equality, {"&&"})

    def parse_equality(self):
        return self._binary_chain(self.parse_relational, {"==", "!="})

    def parse_relational(self):
        return self._binary_chain(self.parse_additive, {"<", "<=", ">", ">="})

    def parse_additive(self):
        return self._binary_chain(self.parse_multiplicative, {"+", "-"})

    def parse_multiplicative(self):
        return self._binary_chain(self.parse_unary, {"*", "/", "%"})

    def parse_unary(self):
        if self.current().kind == "*":
            self.error("UNSUPPORTED_FEATURE", "pointer dereference is outside C Minor")
        if self.current().kind in ("+", "-", "!"):
            op = self.advance()
            self.expression_depth += 1
            try:
                if self.expression_depth > 16:
                    self.error("LIMIT_ERROR", "expression nesting exceeds 16 levels", op)
                operand = self.parse_unary()
            finally:
                self.expression_depth -= 1
            return A.Unary(op.location(), operand.end_location, op.value, operand)
        return self.parse_primary()

    def parse_primary(self):
        token = self.current()
        if token.kind == "INT_LITERAL":
            self.advance()
            first, last = self.span(token)
            return A.IntLiteral(first, last, int(token.value))
        if token.kind == "IDENT":
            name = self.advance()
            if self.match("("):
                args = []
                if self.current().kind != ")":
                    self.expression_depth += 1
                    try:
                        if self.expression_depth > 16:
                            self.error("LIMIT_ERROR", "expression nesting exceeds 16 levels", name)
                        args.append(self.parse_assignment())
                        while self.match(","):
                            args.append(self.parse_assignment())
                    finally:
                        self.expression_depth -= 1
                end = self.expect(")", "expected ')' after function arguments")
                if len(args) > 6:
                    self.error("UNSUPPORTED_FEATURE", "calls may have at most six arguments", name)
                first, last = self.span(name, end)
                return A.Call(first, last, name.value, args)
            first, last = self.span(name)
            return A.Identifier(first, last, name.value)
        if token.kind == "(":
            if self.peek().kind in ("int", "void"):
                self.error("UNSUPPORTED_FEATURE", "type casts are outside C Minor", token)
            self.advance()
            self.expression_depth += 1
            try:
                if self.expression_depth > 16:
                    self.error("LIMIT_ERROR", "expression nesting exceeds 16 levels", token)
                expression = self.parse_assignment()
                end = self.expect(")", "expected ')' after expression")
            finally:
                self.expression_depth -= 1
            first, last = self.span(token, end)
            return A.Parenthesized(first, last, expression)
        self.error("SYNTAX_ERROR", f"expected expression, found {token.value or token.kind!r}")
