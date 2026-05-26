import tupi.syntatic.ast_nodes as ast
from tupi.semantic.symbol_table import SymbolTable

class CodeGenerator:
    def __init__(self, symtable: SymbolTable):
        self.symtable = symtable
        self.indent_level = 1
        self.code = []

    def _add_line(self, line: str):
        indent = "    " * self.indent_level
        self.code.append(indent + line)

    def generate(self, tree) -> str:
        if hasattr(tree, 'data') and getattr(tree, 'data') == 'start':
            tree = tree.children[0]
            
        self.code = [
            "def main():"
        ]
        self.visit(tree)
        if len(self.code) == 1:
            self._add_line("pass")
            
        self.code.append("")
        self.code.append("if __name__ == '__main__':")
        self.code.append("    main()")
        return "\n".join(self.code)

    def visit(self, node: ast._Ast) -> str:
        method_name = f'visit_{node.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast._Ast):
        raise Exception(f"Gerador de código falhou: Nó {node.__class__.__name__} não implementado.")

    def visit_Program(self, node: ast.Program):
        if node.decls:
            for decl in node.decls.decls:
                self.visit(decl)
        self.visit(node.bloco)

    def visit_Bloco(self, node: ast.Bloco):
        for cmd in node.cmds:
            self.visit(cmd)

    def visit_Decl(self, node: ast.Decl):
        default_val = "0"
        py_type = "int"

        if isinstance(node.tipo, ast.TipoInt):
            py_type, default_val = "int", "0"
        elif isinstance(node.tipo, ast.TipoFloat):
            py_type, default_val = "float", "0.0"
        elif isinstance(node.tipo, ast.TipoStr):
            py_type, default_val = "str", '""'
        elif isinstance(node.tipo, ast.TipoBool):
            py_type, default_val = "bool", "False"

        for ident in node.id_list.idents:
            self._add_line(f"{ident}: {py_type} = {default_val}")

    def visit_CmdAtrib(self, node: ast.CmdAtrib):
        rhs = self.visit(node.expr)
        self._add_line(f"{node.ident} = {rhs}")

    def visit_CmdLeitura(self, node: ast.CmdLeitura):
        symbol = self.symtable.resolve(node.ident)
        
        if symbol.python_type == "int":
            self._add_line(f"{node.ident} = int(input())")
        elif symbol.python_type == "float":
            self._add_line(f"{node.ident} = float(input())")
        elif symbol.python_type == "bool":
            self._add_line(f"{node.ident} = input().strip().lower() in ('true', 'anete', '1')")
        else: # str
            self._add_line(f"{node.ident} = input()")

    def visit_CmdEscrita(self, node: ast.CmdEscrita):
        expr_str = self.visit(node.expr)
        self._add_line(f"print({expr_str})")

    def visit_CmdIf(self, node: ast.CmdIf):
        cond_str = self.visit(node.cond)
        self._add_line(f"if {cond_str}:")
        
        self.indent_level += 1
        self.visit(node.if_bloco)
        if len(node.if_bloco.cmds) == 0:
            self._add_line("pass")
        self.indent_level -= 1

        if node.else_bloco:
            self._add_line("else:")
            self.indent_level += 1
            self.visit(node.else_bloco)
            if len(node.else_bloco.cmds) == 0:
                self._add_line("pass")
            self.indent_level -= 1

    def visit_CmdWhile(self, node: ast.CmdWhile):
        cond_str = self.visit(node.cond)
        self._add_line(f"while {cond_str}:")
        
        self.indent_level += 1
        self.visit(node.bloco)
        if len(node.bloco.cmds) == 0:
            self._add_line("pass")
        self.indent_level -= 1

    def visit_CmdDowhile(self, node: ast.CmdDowhile):
        self._add_line("while True:")
        
        self.indent_level += 1
        self.visit(node.bloco)
        if len(node.bloco.cmds) == 0:
            self._add_line("pass")
            
        cond_str = self.visit(node.cond)
        self._add_line(f"if not ({cond_str}):")
        self.indent_level += 1
        self._add_line("break")
        self.indent_level -= 2

    def visit_CmdFor(self, node: ast.CmdFor):
        self.visit(node.init)
        cond_str = self.visit(node.cond)
        self._add_line(f"while {cond_str}:")
        
        self.indent_level += 1
        self.visit(node.bloco)
        step_rhs = self.visit(node.step.expr)
        self._add_line(f"{node.step.ident} = {step_rhs}")
        self.indent_level -= 1

    def visit_ForInit(self, node: ast.ForInit):
        rhs = self.visit(node.expr)
        self._add_line(f"{node.ident} = {rhs}")

    def visit_Cond(self, node: ast.Cond) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = self.visit(node.op)
        return f"{left} {op} {right}"

    def visit_Expr(self, node: ast.Expr) -> str:
        items = node.items
        parts = [self.visit(items[0])]
        for i in range(1, len(items), 2):
            op = self.visit(items[i])
            right = self.visit(items[i+1])
            parts.append(f"{op} {right}")
        return " ".join(parts)

    def visit_Term(self, node: ast.Term) -> str:
        items = node.items
        parts = [self.visit(items[0])]
        for i in range(1, len(items), 2):
            op = self.visit(items[i])
            right = self.visit(items[i+1])
            parts.append(f"{op} {right}")
        return " ".join(parts)

    def visit_OpAdd(self, node: ast.OpAdd) -> str: return "+"
    def visit_OpSub(self, node: ast.OpSub) -> str: return "-"
    def visit_OpMul(self, node: ast.OpMul) -> str: return "*"
    def visit_OpDiv(self, node: ast.OpDiv) -> str: return "/"
    def visit_OpLt(self, node: ast.OpLt) -> str: return "<"
    def visit_OpGt(self, node: ast.OpGt) -> str: return ">"
    def visit_OpLe(self, node: ast.OpLe) -> str: return "<="
    def visit_OpGe(self, node: ast.OpGe) -> str: return ">="
    def visit_OpEq(self, node: ast.OpEq) -> str: return "=="
    def visit_OpNe(self, node: ast.OpNe) -> str: return "!="

    def visit_FatorId(self, node: ast.FatorId) -> str:
        return node.name

    def visit_FatorInt(self, node: ast.FatorInt) -> str:
        return str(node.value)

    def visit_FatorDec(self, node: ast.FatorDec) -> str:
        return str(node.value)

    def visit_FatorStr(self, node: ast.FatorStr) -> str:
        return f'"{node.value}"'

    def visit_FatorTrue(self, node: ast.FatorTrue) -> str:
        return "True"

    def visit_FatorFalse(self, node: ast.FatorFalse) -> str:
        return "False"

    def visit_FatorPar(self, node: ast.FatorPar) -> str:
        inner = self.visit(node.inner)
        return f"({inner})"
