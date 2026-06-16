# Etapa 2 do pipeline: construção da AST a partir da parse tree do Lark.
import sys
from lark import ast_utils, Transformer

from tupi.syntatic import ast_nodes

# Tokens do Lark chegam como subclasses de str carregando o lexema bruto
# (ex.: o token NUMERO_INT contém o texto "42", não o inteiro 42). Estes
# callbacks coercem cada terminal para o tipo Python nativo correspondente
# antes que ele seja usado para preencher um campo de dataclass em ast_nodes.
class TupiTransformer(Transformer):
    def IDENT(self, token):
        return str(token)

    def NUMERO_INT(self, token):
        return int(token)

    def NUMERO_DEC(self, token):
        return float(token)

    def ESCAPED_STRING(self, token):
        # Remove as aspas do começo e do fim
        return str(token)[1:-1]

# ast_utils.create_transformer faz o "fio" entre gramática e AST: para cada
# regra/alias da gramática (ex.: "cmd_if", "-> fator_id"), procura em
# ast_nodes uma dataclass com o mesmo nome em CamelCase e a instancia
# preenchendo os campos posicionalmente com os filhos daquele nó da parse
# tree. Os métodos definidos acima em TupiTransformer rodam primeiro,
# convertendo os tokens-folha antes dessa montagem.
transformer = ast_utils.create_transformer(ast_nodes, TupiTransformer())
