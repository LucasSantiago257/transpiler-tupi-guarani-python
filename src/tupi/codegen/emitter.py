# Etapa 4 do pipeline: geração de código. Percorre a AST com o mesmo padrão
# de Visitor do checker (despacho por nome de classe) e emite Python como
# string. Usa a SymbolTable construída na etapa 3 (não revalida tipos —
# isso já foi garantido pelo checker) para decidir conversões concretas,
# como qual cast usar em cada leitura "monee".
import tupi.syntatic.ast_nodes as ast
from tupi.semantic.symbol_table import SymbolTable

class CodeGenerator:
    def __init__(self, symtable: SymbolTable):
        self.symtable = symtable
        self.indent_level = 1  # corpo de main() começa indentado em 1 nível
        self.code = []

    def _add_line(self, line: str):
        indent = "    " * self.indent_level
        self.code.append(indent + line)

    def generate(self, tree) -> str:
        # Mesmo desembrulho de Tree('start', [...]) feito em checker.py —
        # 'start' não tem dataclass correspondente em ast_nodes.
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

    # Despacho por nome de classe (visit_CmdIf, visit_FatorId, ...), igual
    # ao checker — mas aqui cada visit_* devolve um fragmento de código
    # Python (string) em vez de um tipo.
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
            # Aceita tanto o literal Python ('true') quanto a palavra Tupi
            # ('anete') ou '1', já que quem digita na entrada é o usuário
            # final do programa gerado, não necessariamente alguém que
            # conhece Python.
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
        # Python não tem do-while nativo: simula-se com "while True" e um
        # "break" condicional ao final do corpo, executando o bloco pelo
        # menos uma vez antes de testar a condição.
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
        # Contador inteiro canônico vira 'for v in range(...)'; o resto cai
        # na tradução genérica estilo-C (init; while cond: corpo; passo).
        range_line = self._try_for_range(node)
        if range_line is not None:
            self._add_line(range_line)
            self.indent_level += 1
            self.visit(node.bloco)
            if len(node.bloco.cmds) == 0:
                self._add_line("pass")
            self.indent_level -= 1
        else:
            self._emit_for_while(node)

    def _emit_for_while(self, node: ast.CmdFor):
        self.visit(node.init)
        cond_str = self.visit(node.cond)
        self._add_line(f"while {cond_str}:")

        self.indent_level += 1
        self.visit(node.bloco)
        if len(node.bloco.cmds) == 0:
            self._add_line("pass")
        step_rhs = self.visit(node.step.expr)
        self._add_line(f"{node.step.ident} = {step_rhs}")
        self.indent_level -= 1

    def _unwrap(self, node):
        """Desce por Expr/Term de item único até o fator interno."""
        while isinstance(node, (ast.Expr, ast.Term)) and len(node.items) == 1:
            node = node.items[0]
        return node

    def _try_for_range(self, node: ast.CmdFor):
        """Devolve a linha 'for v in range(...)' se o laço for um contador
        inteiro canônico; caso contrário devolve None (→ fallback while)."""
        v = node.init.ident
        if node.step.ident != v:
            return None
        if not (isinstance(self._unwrap(node.cond.left), ast.FatorId)
                and self._unwrap(node.cond.left).name == v):
            return None

        # passo na forma  v ± K  (Expr com exatamente 3 itens)
        step_expr = node.step.expr
        if not isinstance(step_expr, ast.Expr) or len(step_expr.items) != 3:
            return None
        t0, step_op, t1 = step_expr.items
        if not (isinstance(self._unwrap(t0), ast.FatorId) and self._unwrap(t0).name == v):
            return None
        if not isinstance(step_op, (ast.OpAdd, ast.OpSub)):
            return None

        # direção coerente com o operador relacional
        op = node.cond.op
        ascending = isinstance(op, (ast.OpLt, ast.OpLe))
        descending = isinstance(op, (ast.OpGt, ast.OpGe))
        if ascending and not isinstance(step_op, ast.OpAdd):
            return None
        if descending and not isinstance(step_op, ast.OpSub):
            return None
        if not (ascending or descending):
            return None  # ==, != não viram range

        # variável do laço inteira e limite não-flutuante
        if self.symtable.resolve(v).python_type != "int":
            return None
        bound_node = self._unwrap(node.cond.right)
        if isinstance(bound_node, ast.FatorDec):
            return None
        if (isinstance(bound_node, ast.FatorId)
                and self.symtable.resolve(bound_node.name).python_type == "float"):
            return None

        start = self.visit(node.init.expr)
        bound = self.visit(node.cond.right)

        # stop a partir do operador (dobra literais nos casos inclusivos)
        if isinstance(op, ast.OpLt):
            stop = bound
        elif isinstance(op, ast.OpLe):
            stop = str(bound_node.value + 1) if isinstance(bound_node, ast.FatorInt) else f"{bound} + 1"
        elif isinstance(op, ast.OpGt):
            stop = bound
        else:  # OpGe
            stop = str(bound_node.value - 1) if isinstance(bound_node, ast.FatorInt) else f"{bound} - 1"

        mag = self.visit(t1)
        mag_node = self._unwrap(t1)
        if ascending:
            if isinstance(mag_node, ast.FatorInt) and mag_node.value == 1:
                args = f"{start}, {stop}"
            else:
                args = f"{start}, {stop}, {mag}"
        else:  # decrescente → passo negativo
            neg = f"-{mag}" if isinstance(mag_node, (ast.FatorId, ast.FatorInt, ast.FatorDec)) else f"-({mag})"
            args = f"{start}, {stop}, {neg}"

        return f"for {v} in range({args}):"

    def visit_ForInit(self, node: ast.ForInit):
        rhs = self.visit(node.expr)
        self._add_line(f"{node.ident} = {rhs}")

    def visit_Cond(self, node: ast.Cond) -> str:
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = self.visit(node.op)
        return f"{left} {op} {right}"

    # Mesma lista plana [operando, operador, operando, ...] usada em
    # checker.py — aqui só remonta-se a expressão como texto Python, na
    # mesma ordem; a precedência já foi resolvida pela estrutura aninhada
    # da gramática (expr -> term -> fator), não precisa ser recalculada.
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
