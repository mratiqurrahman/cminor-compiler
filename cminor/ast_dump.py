from dataclasses import fields, is_dataclass
from . import ast_nodes as A


def dump_ast(program):
    lines = ["AST"]

    def span(node):
        loc = node.location
        end = node.end_location
        return f"{loc.line}:{loc.column}-{end.line}:{end.column}"

    def visit(node, depth):
        pad = "  " * depth
        if isinstance(node, A.Program):
            lines.append(f"{pad}Program [{span(node)}]")
            for child in node.externals:
                visit(child, depth + 1)
        elif isinstance(node, A.Function):
            kind = "Definition" if node.is_definition else "Prototype"
            params = ", ".join("int" if p.name is None else f"int {p.name}" for p in node.parameters) or "void"
            lines.append(f"{pad}{kind} {node.return_type} {node.name}({params}) [{span(node)}]")
            if node.body:
                visit(node.body, depth + 1)
        elif isinstance(node, A.Block):
            lines.append(f"{pad}Block [{span(node)}]")
            for child in node.items:
                visit(child, depth + 1)
        elif isinstance(node, A.VarDecl):
            lines.append(f"{pad}VarDecl int {node.name} [{span(node)}]")
            if node.initializer:
                visit(node.initializer, depth + 1)
        elif isinstance(node, A.ExprStmt):
            lines.append(f"{pad}ExprStmt [{span(node)}]")
            if node.expression:
                visit(node.expression, depth + 1)
        elif isinstance(node, A.IfStmt):
            lines.append(f"{pad}If [{span(node)}]")
            visit(node.condition, depth + 1)
            visit(node.then_branch, depth + 1)
            if node.else_branch:
                visit(node.else_branch, depth + 1)
        elif isinstance(node, A.WhileStmt):
            lines.append(f"{pad}While [{span(node)}]")
            visit(node.condition, depth + 1)
            visit(node.body, depth + 1)
        elif isinstance(node, A.ForStmt):
            lines.append(f"{pad}For [{span(node)}]")
            if node.initializer:
                visit(node.initializer, depth + 1)
            if node.condition:
                visit(node.condition, depth + 1)
            if node.update:
                visit(node.update, depth + 1)
            visit(node.body, depth + 1)
        elif isinstance(node, A.BreakStmt):
            lines.append(f"{pad}Break [{span(node)}]")
        elif isinstance(node, A.ContinueStmt):
            lines.append(f"{pad}Continue [{span(node)}]")
        elif isinstance(node, A.ReturnStmt):
            lines.append(f"{pad}Return [{span(node)}]")
            if node.expression:
                visit(node.expression, depth + 1)
        elif isinstance(node, A.IntLiteral):
            lines.append(f"{pad}IntLiteral {node.value} [{span(node)}]")
        elif isinstance(node, A.Identifier):
            lines.append(f"{pad}Identifier {node.name} [{span(node)}]")
        elif isinstance(node, A.Parenthesized):
            lines.append(f"{pad}Parenthesized [{span(node)}]")
            visit(node.expression, depth + 1)
        elif isinstance(node, A.Unary):
            lines.append(f"{pad}Unary {node.operator} [{span(node)}]")
            visit(node.operand, depth + 1)
        elif isinstance(node, A.Binary):
            lines.append(f"{pad}Binary {node.operator} [{span(node)}]")
            visit(node.left, depth + 1)
            visit(node.right, depth + 1)
        elif isinstance(node, A.Assignment):
            lines.append(f"{pad}Assignment [{span(node)}]")
            visit(node.left, depth + 1)
            visit(node.right, depth + 1)
        elif isinstance(node, A.Call):
            lines.append(f"{pad}Call {node.name} [{span(node)}]")
            for argument in node.arguments:
                visit(argument, depth + 1)

    visit(program, 0)
    return "\n".join(lines) + "\n"
