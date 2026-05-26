from dataclasses import dataclass
from typing import List, Optional, Union

from lark import ast_utils
from lark.tree import Meta

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
