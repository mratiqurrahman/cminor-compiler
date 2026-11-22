from dataclasses import dataclass
from pathlib import Path

@dataclass(frozen=True)
class Location:
    path: str
    line: int
    column: int

@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str
    location: Location
    severity: str = "error"
    related: Location | None = None
    related_message: str | None = None

class CompilerError(Exception):
    def __init__(self, diagnostic: Diagnostic):
        self.diagnostic = diagnostic
        super().__init__(diagnostic.message)

class CompilerErrors(Exception):
    def __init__(self, diagnostics):
        self.diagnostics = list(diagnostics)
        super().__init__(f"{len(self.diagnostics)} compiler diagnostics")

class DiagnosticBag:
    def __init__(self):
        self.items = []

    def add(self, code, message, location, related=None, related_message=None):
        self.items.append(Diagnostic(code, message, location, "error", related, related_message))

    def raise_first(self):
        if self.items:
            raise CompilerError(self.items[0])

def format_diagnostic(diagnostic):
    loc = diagnostic.location
    prefix = f"{loc.path}:{loc.line}:{loc.column}: {diagnostic.severity} {diagnostic.code}: {diagnostic.message}"
    if diagnostic.related:
        rel = diagnostic.related
        detail = diagnostic.related_message or "related declaration"
        prefix += f"\n{rel.path}:{rel.line}:{rel.column}: note: {detail}"
    return prefix

def location_from(path, line, column):
    return Location(str(Path(path)), line, column)
