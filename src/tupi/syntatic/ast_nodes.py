# Etapa 2 do pipeline: nós da AST (dataclasses), montados a partir da parse
# tree pelo transformer (syntatic/transformer.py via ast_utils.create_transformer).
#
# Convenção obrigatória: o nome de cada classe abaixo deve corresponder, em
# CamelCase, ao nome de uma regra ou alias ("-> nome") da gramática em
# grammar/tupi.lark (snake_case -> CamelCase). É essa correspondência de
# nomes que conecta os dois arquivos — não há registro explícito em lugar
# nenhum. Os campos do dataclass são preenchidos posicionalmente, na ordem
# dos filhos daquele nó na gramática.
from dataclasses import dataclass
from typing import List, Optional, Union

from lark import ast_utils
from lark.tree import Meta

# _Ast é a classe-base exigida pelo ast_utils do Lark: marca quais classes
# deste módulo são candidatas a nó de AST (as demais são ignoradas).
class _Ast(ast_utils.Ast): pass

class _Tipo(_Ast): pass
@dataclass
class TipoInt(_Tipo): pass
@dataclass
class TipoFloat(_Tipo): pass
@dataclass
class TipoStr(_Tipo): pass
@dataclass
class TipoBool(_Tipo): pass

# Base genérica para todos os tipos de expressões e fatores
class ExprBase(_Ast): pass

# ast_utils.AsList diz ao transformer para empacotar TODOS os filhos do nó
# numa única lista (em vez de campos posicionais fixos), pois um Expr/Term
# pode ter um número variável de operandos — ex.: "a + b - c" produz items =
# [a, OpAdd, b, OpSub, c]. checker.py e emitter.py percorrem essa lista de
# 2 em 2 (operando, operador, operando, ...).
@dataclass
class Expr(ExprBase, ast_utils.AsList):
    items: List[Union['_Ast']]

@dataclass
class Term(ExprBase, ast_utils.AsList):
    items: List[Union['_Ast']]

@dataclass
class FatorId(ExprBase): name: str
@dataclass
class FatorInt(ExprBase): value: int
@dataclass
class FatorDec(ExprBase): value: float
@dataclass
class FatorStr(ExprBase): value: str
@dataclass
class FatorTrue(ExprBase): pass
@dataclass
class FatorFalse(ExprBase): pass
@dataclass
class FatorPar(ExprBase): inner: ExprBase

@dataclass
class OpAdd(_Ast): pass
@dataclass
class OpSub(_Ast): pass
@dataclass
class OpMul(_Ast): pass
@dataclass
class OpDiv(_Ast): pass

@dataclass
class OpLt(_Ast): pass
@dataclass
class OpGt(_Ast): pass
@dataclass
class OpLe(_Ast): pass
@dataclass
class OpGe(_Ast): pass
@dataclass
class OpNe(_Ast): pass
@dataclass
class OpEq(_Ast): pass

@dataclass
class Cond(_Ast):
    left: ExprBase
    op: _Ast
    right: ExprBase

class Cmd(_Ast): pass

@dataclass
class CmdLeitura(Cmd):
    ident: str

@dataclass
class CmdEscrita(Cmd):
    expr: ExprBase

@dataclass
class CmdAtrib(Cmd):
    ident: str
    expr: ExprBase

@dataclass
class Bloco(_Ast, ast_utils.AsList):
    cmds: List[Cmd]

@dataclass
class CmdIf(Cmd):
    cond: Cond
    if_bloco: Bloco
    else_bloco: Optional[Bloco] = None

@dataclass
class CmdWhile(Cmd):
    cond: Cond
    bloco: Bloco

@dataclass
class CmdDowhile(Cmd):
    bloco: Bloco
    cond: Cond

@dataclass
class ForInit(_Ast):
    ident: str
    expr: ExprBase

@dataclass
class ForStep(_Ast):
    ident: str
    expr: ExprBase

@dataclass
class CmdFor(Cmd):
    init: ForInit
    cond: Cond
    step: ForStep
    bloco: Bloco

@dataclass
class IdList(_Ast, ast_utils.AsList):
    idents: List[str]

@dataclass
class Decl(_Ast):
    tipo: _Tipo
    id_list: IdList

@dataclass
class Decls(_Ast, ast_utils.AsList):
    decls: List[Decl]

@dataclass
class Program(_Ast):
    decls: Decls
    bloco: Bloco
