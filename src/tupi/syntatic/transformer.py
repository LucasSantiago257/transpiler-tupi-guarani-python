import sys
from lark import ast_utils, Transformer

from tupi.syntatic import ast_nodes

# Definição do Transformer com o caso de uso
class TupiTransformer(Transformer):
    # Pegando valores dos tokens
    
    def IDENT(self, token):
        return str(token)
    
    def NUMERO_INT(self, token):
        return int(token)
        
    def NUMERO_DEC(self, token):
        return float(token)

    def ESCAPED_STRING(self, token):
        # Remove as aspas do começo e do fim
        return str(token)[1:-1]
        
    # Criação de objeto transformer do módulo.

transformer = ast_utils.create_transformer(ast_nodes, TupiTransformer())
