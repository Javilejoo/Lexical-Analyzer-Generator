"""
Interfaz entre el analizador léxico y sintáctico.
Este módulo maneja la lectura y procesamiento de tokens desde archivos de salida del analizador léxico.
"""

import os
import re
from typing import List
from dataclasses import dataclass


@dataclass
class LexicalToken:
    """Representa un token del analizador léxico"""
    token_type: str
    value: str
    line: int = 1
    column: int = 1
    
    def __repr__(self):
        return f"{self.token_type}('{self.value}')"


class TokenFileReader:
    """Lector de archivos de tokens del analizador léxico"""
    
    # Tokens que deben ser ignorados por el analizador sintáctico
    IGNORED_TOKENS = {
        'WS',           # Whitespace
        'WHITESPACE',   # Whitespace alternativo
        'COMMENT',      # Comentarios
        'NEWLINE',      # Saltos de línea
        'TAB',          # Tabulaciones
        'SPACE',        # Espacios
    }
    
    @staticmethod
    def read_tokens_from_file(tokens_file: str) -> List[str]:
        """
        Lee tokens desde un archivo de salida del analizador léxico.
        
        Args:
            tokens_file: Archivo con tokens en formato TOKEN_TYPE 'value'
            
        Returns:
            list: Lista de nombres de tokens (sin whitespace)
        """
        tokens = []
        
        try:
            with open(tokens_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parsear línea: TOKEN_TYPE      'value'
                    match = re.match(r'^(\w+)\s+\'(.*)\'$', line)
                    if match:
                        token_type = match.group(1)
                        value = match.group(2)
                        
                        # Filtrar tokens de whitespace
                        if token_type not in TokenFileReader.IGNORED_TOKENS:
                            tokens.append(token_type)
                    else:
                        print(f"Advertencia: No se pudo parsear línea {line_num}: {line}")
        
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {tokens_file}")
            return []
        except Exception as e:
            print(f"Error leyendo archivo de tokens: {e}")
            return []
        
        return tokens
    
    @staticmethod
    def read_detailed_tokens_from_file(tokens_file: str) -> List[LexicalToken]:
        """
        Lee tokens detallados desde un archivo de salida del analizador léxico.
        
        Args:
            tokens_file: Archivo con tokens en formato TOKEN_TYPE 'value'
            
        Returns:
            list: Lista de objetos LexicalToken
        """
        tokens = []
        
        try:
            with open(tokens_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parsear línea: TOKEN_TYPE      'value'
                    match = re.match(r'^(\w+)\s+\'(.*)\'$', line)
                    if match:
                        token_type = match.group(1)
                        value = match.group(2)
                        tokens.append(LexicalToken(token_type, value, line_num))
                    else:
                        print(f"Advertencia: No se pudo parsear línea {line_num}: {line}")
        
        except FileNotFoundError:
            print(f"Error: No se encontró el archivo {tokens_file}")
            return []
        except Exception as e:
            print(f"Error leyendo archivo de tokens: {e}")
            return []
        
        return tokens


class TokenMapper:
    """Mapea tokens del analizador léxico al formato esperado por el sintáctico"""
    
    # Mapeo entre tokens del léxico y tokens del sintáctico
    TOKEN_MAPPING = {
        # Tokens básicos
        'ID': 'ID',
        'NUMBER': 'NUMBER',
        'INTEGER': 'NUMBER',
        'IDENTIFIER': 'ID',
        
        # Operadores aritméticos
        'PLUS': 'PLUS',
        'MINUS': 'MINUS',
        'TIMES': 'TIMES',
        'DIV': 'DIV',
        'MULTIPLY': 'TIMES',
        'DIVIDE': 'DIV',
        'MULT': 'TIMES',
        
        # Paréntesis
        'LPAREN': 'LPAREN',
        'RPAREN': 'RPAREN',
        'LEFT_PAREN': 'LPAREN',
        'RIGHT_PAREN': 'RPAREN',
        '(': 'LPAREN',
        ')': 'RPAREN',
        
        # Operadores de comparación
        'LT': 'LT',
        'GT': 'GT',
        'EQ': 'EQ',
        'LE': 'LE',
        'GE': 'GE',
        'EQUAL': 'EQ',
        'LESS': 'LT',
        'GREATER': 'GT',
        
        # Otros
        'SEMICOLON': 'SEMICOLON',
        'ASSIGN': 'ASSIGNOP',
        'ASSIGNOP': 'ASSIGNOP',
        'COMMA': 'COMMA',
        'DOT': 'DOT',
    }
    
    @staticmethod
    def map_token_name(lexical_token_type: str) -> str:
        """
        Mapea el nombre de un token del léxico al nombre esperado por el sintáctico.
        
        Args:
            lexical_token_type: Nombre del token en el analizador léxico
            
        Returns:
            str: Nombre del token para el analizador sintáctico
        """
        # Buscar mapeo directo
        if lexical_token_type in TokenMapper.TOKEN_MAPPING:
            return TokenMapper.TOKEN_MAPPING[lexical_token_type]
        
        # Si no hay mapeo específico, usar el nombre original
        return lexical_token_type
    
    @staticmethod
    def filter_tokens_for_syntax(tokens: List[str]) -> List[str]:
        """
        Filtra y mapea una lista de tokens para el analizador sintáctico.
        
        Args:
            tokens: Lista de nombres de tokens del léxico
            
        Returns:
            list: Lista de tokens mapeados para el sintáctico
        """
        syntax_tokens = []
        
        for token in tokens:
            # Filtrar tokens ignorados
            if token not in TokenFileReader.IGNORED_TOKENS:
                mapped_token = TokenMapper.map_token_name(token)
                syntax_tokens.append(mapped_token)
        
        return syntax_tokens


class LexicalInterface:
    """Interfaz principal entre el analizador léxico y sintáctico"""
    
    def __init__(self):
        """Inicializa la interfaz léxica."""
        self.reader = TokenFileReader()
        self.mapper = TokenMapper()
    
    def load_tokens_from_file(self, tokens_file: str) -> List[str]:
        """
        Carga tokens desde un archivo específico.
        
        Args:
            tokens_file: Ruta al archivo de tokens
            
        Returns:
            list: Lista de tokens para el sintáctico
        """
        # Leer tokens del archivo
        raw_tokens = self.reader.read_tokens_from_file(tokens_file)
        
        if not raw_tokens:
            return []
        
        # Filtrar y mapear tokens
        syntax_tokens = self.mapper.filter_tokens_for_syntax(raw_tokens)
        
        return syntax_tokens
    
def main():
    """Función principal para pruebas del módulo"""
    import sys
    
    if len(sys.argv) != 2:
        print("Uso: python lexical_interface.py <archivo_tokens>")
        sys.exit(1)
    
    tokens_file = sys.argv[1]
    interface = LexicalInterface()
    
    # Cargar tokens desde archivo
    tokens = interface.load_tokens_from_file(tokens_file)
    if tokens:
        print(f"Tokens cargados: {tokens}")
        
        # Mostrar estadísticas
        stats = interface.get_token_statistics(tokens_file)
        print(f"\nEstadísticas:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("No se pudieron cargar tokens del archivo")


if __name__ == "__main__":
    main() 