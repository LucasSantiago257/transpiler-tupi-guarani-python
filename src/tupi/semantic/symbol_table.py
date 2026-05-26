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

    def mark_initialized(self, name: str) -> None:
        symbol = self.resolve(name)
        symbol.is_initialized = True

    def check_initialization(self, name: str) -> None:
        symbol = self.resolve(name)
        if not symbol.is_initialized:
            raise SemanticError("Erro Semântico: A variável - " + name + " - não foi inicializada.")