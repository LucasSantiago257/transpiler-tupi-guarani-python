# Apoio à etapa 3 (análise semântica, em checker.py). A mesma instância de
# SymbolTable é repassada à etapa 4 (emitter.py), que consulta python_type
# para decidir conversões de tipo na geração de código (ex.: monee -> int()
# vs float() vs input()).
from dataclasses import dataclass
from typing import Dict, Optional

@dataclass
class SymbolInfo:
    name: str
    tupi_type: str
    python_type: str
    is_initialized: bool = False

class SemanticError(Exception):
    pass

# Escopo único e plano: um só dict para todo o programa, sem pilha de
# escopos por bloco. Por isso a linguagem não tem shadowing — duas
# declarações com o mesmo nome colidem mesmo que estejam em blocos { }
# diferentes (ver docs/linguagem.md, regras semânticas da seção 3).
class SymbolTable:
    def __init__(self):
        self._symbols: Dict[str, SymbolInfo] = {}

    def define(self, name: str, tupi_type: str, python_type: str) -> None:
        if name in self._symbols:
            raise SemanticError("Erro Semântico: Já existe uma variável com o nome -" + name + " -")

        self._symbols[name] = SymbolInfo(
            name=name,
            tupi_type=tupi_type,
            python_type=python_type
        )

    def resolve(self, name: str) -> SymbolInfo:
        if name not in self._symbols:
            raise SemanticError("Erro Semântico: A variável - " + name + " - não foi declarada.")

        return self._symbols[name]

    # is_initialized/estes dois métodos existem para uma checagem de "uso
    # antes de inicializar" mais estrita do que a linguagem exige hoje (ver
    # seção 3 do docs/linguagem.md: só é obrigatório declarar antes de usar,
    # não inicializar). Não são chamados por SemanticChecker atualmente.
    def mark_initialized(self, name: str) -> None:
        symbol = self.resolve(name)
        symbol.is_initialized = True

    def check_initialization(self, name: str) -> None:
        symbol = self.resolve(name)
        if not symbol.is_initialized:
            raise SemanticError("Erro Semântico: A variável - " + name + " - não foi inicializada.")