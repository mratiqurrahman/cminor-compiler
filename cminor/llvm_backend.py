from .ir import ModuleIR

class LLVMEmitter:
    def __init__(self, module):
        self.module = module
        self.lines = []
        self.terminated = False
        self.current_function = None
        self.branch_counter = 0

    def variable(self, identifier):
        return f"%v_{identifier}"

    def temporary(self, identifier):
        return f"%{identifier}"

    def emit(self, line):
        self.lines.append(f"  {line}")

    def fresh(self, prefix="c"):
        value = f"%{prefix}{self.branch_counter}"
        self.branch_counter += 1
        return value

    def emit_label(self, name):
        if not self.terminated:
            self.emit(f"br label %{name}")
        self.lines.append(f"{name}:")
        self.terminated = False

    def emit_instruction(self, instruction):
        op = instruction[0]
        if op == "param":
            return
        if op == "label":
            self.emit_label(instruction[1])
            return
        if op == "const":
            if not self.terminated:
                self.emit(f"{self.temporary(instruction[1])} = add i32 0, {instruction[2]}")
            return
        if op == "load":
            if not self.terminated:
                self.emit(f"{self.temporary(instruction[1])} = load i32, ptr {self.variable(instruction[2])}, align 4")
            return
        if op == "store":
            if not self.terminated:
                self.emit(f"store i32 {self.temporary(instruction[2])}, ptr {self.variable(instruction[1])}, align 4")
            return
        if op == "unary":
            if self.terminated:
                return
            target, operator, operand = instruction[1:]
            dest = self.temporary(target)
            value = self.temporary(operand)
            if operator == "+":
                self.emit(f"{dest} = add i32 0, {value}")
            elif operator == "-":
                self.emit(f"{dest} = sub i32 0, {value}")
            else:
                comparison = self.fresh()
                self.emit(f"{comparison} = icmp eq i32 {value}, 0")
                self.emit(f"{dest} = zext i1 {comparison} to i32")
            return
        if op == "binary":
            if self.terminated:
                return
            target, operator, left, right = instruction[1:]
            dest = self.temporary(target)
            a = self.temporary(left)
            b = self.temporary(right)
            arithmetic = {"+": "add", "-": "sub", "*": "mul", "/": "sdiv", "%": "srem"}
            comparisons = {"<": "slt", "<=": "sle", ">": "sgt", ">=": "sge", "==": "eq", "!=": "ne"}
            if operator in arithmetic:
                self.emit(f"{dest} = {arithmetic[operator]} i32 {a}, {b}")
            else:
                comparison = self.fresh()
                self.emit(f"{comparison} = icmp {comparisons[operator]} i32 {a}, {b}")
                self.emit(f"{dest} = zext i1 {comparison} to i32")
            return
        if op == "phi":
            if not self.terminated:
                target, first_value, first_label, second_value, second_label = instruction[1:]
                self.emit(f"{self.temporary(target)} = phi i32 [ {self.temporary(first_value)}, %{first_label} ], [ {self.temporary(second_value)}, %{second_label} ]")
            return
        if op == "call":
            if self.terminated:
                return
            target, name, arguments, return_type = instruction[1:]
            args = ", ".join(f"i32 {self.temporary(arg)}" for arg in arguments)
            if return_type == "void":
                self.emit(f"call void @{name}({args})")
            else:
                self.emit(f"{self.temporary(target)} = call i32 @{name}({args})")
            return
        if op == "jump":
            if not self.terminated:
                self.emit(f"br label %{instruction[1]}")
                self.terminated = True
            return
        if op == "branch":
            if not self.terminated:
                condition = self.fresh()
                self.emit(f"{condition} = icmp ne i32 {self.temporary(instruction[1])}, 0")
                self.emit(f"br i1 {condition}, label %{instruction[2]}, label %{instruction[3]}")
                self.terminated = True
            return
        if op == "return":
            if not self.terminated:
                self.emit(f"ret i32 {self.temporary(instruction[1])}")
                self.terminated = True
            return
        if op == "return_void":
            if not self.terminated:
                self.emit("ret void")
                self.terminated = True
            return
        raise RuntimeError(f"unknown student IR instruction {op}")

    def emit_function(self, function):
        self.current_function = function
        self.terminated = False
        self.branch_counter = 0
        params = ", ".join(f"i32 %arg{index}" for index, _ in enumerate(function.parameters))
        return_ir = "i32" if function.return_type == "int" else "void"
        self.lines.append(f"define {return_ir} @{function.name}({params}) {{")
        self.lines.append("entry:")
        for symbol in function.variables:
            self.emit(f"{self.variable(symbol.identifier)} = alloca i32, align 4")
        for index, symbol in enumerate(function.parameters):
            self.emit(f"store i32 %arg{index}, ptr {self.variable(symbol.identifier)}, align 4")
        for instruction in function.instructions:
            self.emit_instruction(instruction)
        if not self.terminated:
            if function.return_type == "void":
                self.emit("ret void")
            else:
                self.emit("unreachable")
        self.lines.append("}")
        self.lines.append("")

    def generate(self):
        self.lines = ['target triple = "x86_64-pc-linux-gnu"', ""]
        for function in self.module.functions:
            self.emit_function(function)
        return "\n".join(self.lines).rstrip() + "\n"

def emit_llvm(module):
    return LLVMEmitter(module).generate()
