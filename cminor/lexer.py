from dataclasses import dataclass
from .diagnostics import CompilerError, Diagnostic, Location

KEYWORDS = {"int", "void", "if", "else", "while", "for", "break", "continue", "return"}
RESERVED = {
    "auto", "case", "char", "const", "default", "do", "double", "enum", "extern", "float",
    "goto", "inline", "long", "register", "restrict", "short", "signed", "sizeof", "static",
    "struct", "switch", "typedef", "union", "unsigned", "volatile", "_Alignas", "_Alignof",
    "_Atomic", "_Bool", "_Complex", "_Generic", "_Imaginary", "_Noreturn", "_Static_assert",
    "_Thread_local", "typeof", "typeof_unqual", "bool", "true", "false", "constexpr", "nullptr", "_BitInt",
    "_Decimal32", "_Decimal64", "_Decimal128", "_Float16", "_Float32", "_Float64", "_Float128",
    "_Float32x", "_Float64x", "_Float128x", "alignas", "alignof", "static_assert", "thread_local"
}
TWO_CHAR = {"<=", ">=", "==", "!=", "&&", "||"}
SINGLE = set("(){};, +-*/%<>!=")
UNSUPPORTED_SINGLE = {"?", "&", "|", "^", "~", ":", "[", "]", "."}
UNSUPPORTED = {
    "++", "--", "+=", "-=", "*=", "/=", "%=", "<<", ">>", "&=", "|=", "^=",
    "->", "...", "##", "?", "&", "|", "^", "~", ":"
}

@dataclass(frozen=True)
class Token:
    kind: str
    value: str
    path: str
    line: int
    column: int
    end_line: int
    end_column: int

    def location(self):
        return Location(self.path, self.line, self.column)

class Lexer:
    def __init__(self, source, path):
        self.source = source
        self.path = str(path)
        self.index = 0
        self.line = 1
        self.column = 1
        self.line_has_item = False
        self.tokens = []

    def _peek(self, offset=0):
        pos = self.index + offset
        return self.source[pos] if pos < len(self.source) else ""

    def _advance(self):
        ch = self._peek()
        if not ch:
            return ""
        if ch == "\r" and self._peek(1) == "\n":
            self.index += 2
            self.line += 1
            self.column = 1
            self.line_has_item = False
            return "\r\n"
        self.index += 1
        if ch == "\n":
            self.line += 1
            self.column = 1
            self.line_has_item = False
        else:
            self.column += 1
        return ch

    def _error(self, code, message, line=None, column=None):
        loc = Location(self.path, line or self.line, column or self.column)
        raise CompilerError(Diagnostic(code, message, loc))

    def _emit(self, kind, value, start_line, start_col):
        self.tokens.append(Token(kind, value, self.path, start_line, start_col, self.line, self.column))
        self.line_has_item = True
        if len(self.tokens) > 4000:
            self._error("LIMIT_ERROR", "source exceeds the 4000-token limit", start_line, start_col)

    def _skip_line_comment(self):
        self._advance()
        self._advance()
        while self._peek() and self._peek() not in "\r\n":
            self._advance()

    def _skip_block_comment(self):
        start_line, start_col = self.line, self.column
        self._advance()
        self._advance()
        while self._peek():
            if self._peek() == "*" and self._peek(1) == "/":
                self._advance()
                self._advance()
                return
            self._advance()
        self._error("LEXICAL_ERROR", "unterminated block comment", start_line, start_col)

    def _scan_number(self):
        line, col = self.line, self.column
        start = self.index
        while self._peek() and (self._peek().isascii() and (self._peek().isalnum() or self._peek() in "._")):
            self._advance()
        raw = self.source[start:self.index]
        if raw.startswith("0") and raw != "0":
            self._error("UNSUPPORTED_FEATURE", f"unsupported integer literal {raw!r}; only canonical decimal literals are accepted", line, col)
        if not raw.isascii() or not raw.isdigit() or (len(raw) > 1 and raw[0] == "0"):
            self._error("UNSUPPORTED_FEATURE", f"unsupported or malformed numeric literal {raw!r}", line, col)
        if len(raw) > 10:
            self._error("UNSUPPORTED_FEATURE", "integer literal exceeds 2147483647", line, col)
        value = int(raw)
        if value > 2147483647:
            self._error("UNSUPPORTED_FEATURE", "integer literal exceeds 2147483647", line, col)
        self._emit("INT_LITERAL", raw, line, col)

    def _scan_identifier(self):
        line, col = self.line, self.column
        start = self.index
        self._advance()
        while self._peek() and (self._peek().isascii() and (self._peek().isalnum() or self._peek() == "_")):
            self._advance()
        value = self.source[start:self.index]
        if value in RESERVED and value not in KEYWORDS:
            self._error("UNSUPPORTED_FEATURE", f"reserved word {value!r} is outside C Minor", line, col)
        self._emit(value if value in KEYWORDS else "IDENT", value, line, col)

    def scan(self):
        if len(self.source.encode("utf-8")) > 32768:
            self._error("LIMIT_ERROR", "source exceeds the 32768-byte input limit", 1, 1)
        for line_number, line_text in enumerate(self.source.splitlines(), 1):
            if len(line_text) > 2048:
                self._error("LIMIT_ERROR", "source line exceeds 2048 characters", line_number, 2049)
        while self._peek():
            ch = self._peek()
            if ch in " \t\v\f":
                self._advance()
                continue
            if ch == "\r" and self._peek(1) == "\n":
                self._advance()
                continue
            if ch == "\n":
                self._advance()
                continue
            if ch == "\\" and (self._peek(1) == "\n" or (self._peek(1) == "\r" and self._peek(2) == "\n")):
                self._error("UNSUPPORTED_LINE_SPLICING", "backslash-newline line splicing is not supported")
            if ch == "/" and self._peek(1) == "/":
                self._skip_line_comment()
                continue
            if ch == "/" and self._peek(1) == "*":
                self._skip_block_comment()
                continue
            line, col = self.line, self.column
            if ch == "#" or (ch == "%" and self._peek(1) == ":"):
                is_directive = True
                if is_directive and not self.line_has_item:
                    spelling = "#" if ch == "#" else "%:"
                    self._error("UNSUPPORTED_PREPROCESSING_DIRECTIVE", f"preprocessing directive {spelling!r} is not supported", line, col)
                self._error("LEXICAL_ERROR", f"unexpected character {ch!r}", line, col)
            if ch.isascii() and (ch.isalpha() or ch == "_"):
                self._scan_identifier()
                continue
            if ch.isascii() and ch.isdigit():
                self._scan_number()
                continue
            pair = ch + self._peek(1)
            if pair in TWO_CHAR:
                self._advance()
                self._advance()
                self._emit(pair, pair, line, col)
                continue
            if pair in UNSUPPORTED:
                self._error("UNSUPPORTED_FEATURE", f"operator {pair!r} is outside C Minor", line, col)
            if ch in UNSUPPORTED_SINGLE:
                self._error("UNSUPPORTED_FEATURE", f"operator or delimiter {ch!r} is outside C Minor", line, col)
            if ch in SINGLE:
                self._advance()
                self._emit(ch, ch, line, col)
                continue
            if ch in "\"'":
                self._error("UNSUPPORTED_FEATURE", "string and character literals are outside C Minor", line, col)
            if not ch.isascii():
                self._error("LEXICAL_ERROR", "non-ASCII source characters are not supported", line, col)
            self._error("LEXICAL_ERROR", f"unknown character {ch!r}", line, col)
        self.tokens.append(Token("EOF", "", self.path, self.line, self.column, self.line, self.column))
        return self.tokens
