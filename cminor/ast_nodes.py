from dataclasses import dataclass, field
from .diagnostics import Location

@dataclass
class Node:
    location: Location
    end_location: Location

@dataclass
class Program(Node):
    externals: list = field(default_factory=list)

@dataclass
class Parameter(Node):
    name: str | None

@dataclass
class Function(Node):
    return_type: str
    name: str
    parameters: list
    is_definition: bool
    body: object | None = None

@dataclass
class Block(Node):
    items: list = field(default_factory=list)

@dataclass
class VarDecl(Node):
    name: str
    initializer: object | None = None

@dataclass
class ExprStmt(Node):
    expression: object | None = None

@dataclass
class IfStmt(Node):
    condition: object
    then_branch: object
    else_branch: object | None = None

@dataclass
class WhileStmt(Node):
    condition: object
    body: object

@dataclass
class ForStmt(Node):
    initializer: object | None
    condition: object | None
    update: object | None
    body: object

@dataclass
class BreakStmt(Node):
    pass

@dataclass
class ContinueStmt(Node):
    pass

@dataclass
class ReturnStmt(Node):
    expression: object | None = None

@dataclass
class IntLiteral(Node):
    value: int

@dataclass
class Identifier(Node):
    name: str

@dataclass
class Parenthesized(Node):
    expression: object

@dataclass
class Unary(Node):
    operator: str
    operand: object

@dataclass
class Binary(Node):
    operator: str
    left: object
    right: object

@dataclass
class Assignment(Node):
    left: object
    right: object

@dataclass
class Call(Node):
    name: str
    arguments: list
