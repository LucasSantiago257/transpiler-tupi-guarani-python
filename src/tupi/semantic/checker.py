from tupi.semantic.symbol_table import SymbolTable, SemanticError
import tupi.syntatic.ast_nodes as ast

class SemanticChecker:
    def __init__(self):
        self.symtable = SymbolTable()

    def check(self, tree):
        if hasattr(tree, 'data') and getattr(tree, 'data') == 'start':
            tree = tree.children[0]
        self.visit(tree)

    def visit(self, node: ast._Ast):
        method_name = f'visit_{node.__class__.__name__}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: ast._Ast):
        raise Exception(f"No visit_{node.__class__.__name__} method")

    def visit_Program(self, node: ast.Program):
        if node.decls:
            for decl in node.decls.decls:
                self.visit(decl)
        self.visit(node.bloco)

    def visit_Bloco(self, node: ast.Bloco):
        for cmd in node.cmds:
            self.visit(cmd)

    def visit_Decl(self, node: ast.Decl):
        tupi_type = "desconhecido"
        python_type = "desconhecido"

        if isinstance(node.tipo, ast.TipoInt):
            tupi_type, python_type = "papy", "int"
        elif isinstance(node.tipo, ast.TipoFloat):
            tupi_type, python_type = "papyvore", "float"
        elif isinstance(node.tipo, ast.TipoStr):
            tupi_type, python_type = "nee", "str"
        elif isinstance(node.tipo, ast.TipoBool):
            tupi_type, python_type = "anetepa", "bool"

        for ident in node.id_list.idents:
            self.symtable.define(ident, tupi_type, python_type)

    def visit_CmdAtrib(self, node: ast.CmdAtrib):
        symbol = self.symtable.resolve(node.ident)
        expr_type = self.visit(node.expr)

        if symbol.python_type == "float" and expr_type == "int":
            pass
        elif symbol.python_type != expr_type:
            raise SemanticError(f"Erro Semântico: Não é possível atribuir '{expr_type}' na variável '{node.ident}' do tipo '{symbol.python_type}'.")

    def visit_CmdLeitura(self, node: ast.CmdLeitura):
        self.symtable.resolve(node.ident)

    def visit_CmdEscrita(self, node: ast.CmdEscrita):
        self.visit(node.expr)

    def visit_CmdIf(self, node: ast.CmdIf):
        cond_type = self.visit(node.cond)
        if cond_type != "bool":
            raise SemanticError(f"Erro Semântico: A condição do 'ramo' deve ser booleana, mas recebeu '{cond_type}'.")
        self.visit(node.if_bloco)
        if node.else_bloco:
            self.visit(node.else_bloco)

    def visit_CmdWhile(self, node: ast.CmdWhile):
        cond_type = self.visit(node.cond)
        if cond_type != "bool":
            raise SemanticError(f"Erro Semântico: A condição do 'aja' deve ser booleana, mas recebeu '{cond_type}'.")
        self.visit(node.bloco)

    def visit_CmdDowhile(self, node: ast.CmdDowhile):
        cond_type = self.visit(node.cond)
        if cond_type != "bool":
            raise SemanticError(f"Erro Semântico: A condição do 'japo..aja' deve ser booleana, mas recebeu '{cond_type}'.")
        self.visit(node.bloco)

    def visit_CmdFor(self, node: ast.CmdFor):
        symbol = self.symtable.resolve(node.init.ident)
        init_type = self.visit(node.init.expr)
        if symbol.python_type != init_type and not (symbol.python_type == 'float' and init_type == 'int'):
            raise SemanticError(f"Erro Semântico: Atribuição inicial do laço for ('{node.init.ident}') tem tipo inválido.")

        cond_type = self.visit(node.cond)
        if cond_type != "bool":
            raise SemanticError(f"Erro Semântico: A condição do laço 'rupi' deve ser booleana.")

        symbol_step = self.symtable.resolve(node.step.ident)
        step_type = self.visit(node.step.expr)
        if symbol_step.python_type != step_type and not (symbol_step.python_type == 'float' and step_type == 'int'):
            raise SemanticError(f"Erro Semântico: Atribuição de passo do laço for ('{node.step.ident}') tem tipo inválido.")

        self.visit(node.bloco)

    def visit_Cond(self, node: ast.Cond) -> str:
        left_type = self.visit(node.left)
        right_type = self.visit(node.right)
        
        if isinstance(node.op, (ast.OpLt, ast.OpGt, ast.OpLe, ast.OpGe)):
            if left_type not in ('int', 'float') or right_type not in ('int', 'float'):
                raise SemanticError("Erro Semântico: Operadores relacionais (<, >, <=, >=) exigem tipos numéricos.")
        
        if isinstance(node.op, (ast.OpEq, ast.OpNe)):
            if left_type != right_type:
                if not (left_type in ('int', 'float') and right_type in ('int', 'float')):
                    raise SemanticError(f"Erro Semântico: Não é possível comparar '{left_type}' com '{right_type}'.")

        return "bool"

    def visit_Expr(self, node: ast.Expr) -> str:
        items = node.items
        current_type = self.visit(items[0])
        for i in range(1, len(items), 2):
            op = items[i]
            next_type = self.visit(items[i+1])
            current_type = self._check_arithmetic(current_type, next_type, op)
        return current_type

    def visit_Term(self, node: ast.Term) -> str:
        items = node.items
        current_type = self.visit(items[0])
        for i in range(1, len(items), 2):
            op = items[i]
            next_type = self.visit(items[i+1])
            current_type = self._check_arithmetic(current_type, next_type, op)
        return current_type

    def _check_arithmetic(self, left: str, right: str, op: ast._Ast) -> str:
        if left == 'str' and right == 'str':
            if isinstance(op, ast.OpAdd):
                return 'str'
            raise SemanticError("Erro Semântico: Apenas soma (+) é permitida para strings.")
        
        if left in ('str', 'bool') or right in ('str', 'bool'):
            raise SemanticError(f"Erro Semântico: Operação aritmética inválida entre '{left}' e '{right}'.")


        if isinstance(op, ast.OpDiv):
            if left == 'float' or right == 'float':
                return 'float'
            return 'int'

        if left == 'float' or right == 'float':
            return 'float'

        return 'int'

    def visit_FatorId(self, node: ast.FatorId) -> str:
        symbol = self.symtable.resolve(node.name)
        return symbol.python_type

    def visit_FatorInt(self, node: ast.FatorInt) -> str:
        return "int"

    def visit_FatorDec(self, node: ast.FatorDec) -> str:
        return "float"

    def visit_FatorStr(self, node: ast.FatorStr) -> str:
        return "str"

    def visit_FatorTrue(self, node: ast.FatorTrue) -> str:
        return "bool"

    def visit_FatorFalse(self, node: ast.FatorFalse) -> str:
        return "bool"

    def visit_FatorPar(self, node: ast.FatorPar) -> str:
        return self.visit(node.inner)
