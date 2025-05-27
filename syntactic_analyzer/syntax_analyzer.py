#!/usr/bin/env python3
"""
Analizador sintáctico integrado que conecta el analizador léxico con el sintáctico.
Este es el punto de integración entre ambas partes del proyecto.
"""

import sys
import os
import re

# Agregar paths para importar módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slr_table import analyze_slr_grammar, SLRParser

class LexicalToken:
    """Representa un token del analizador léxico"""
    def __init__(self, token_type, value, line=1, column=1):
        self.type = token_type
        self.value = value
        self.line = line
        self.column = column
    
    def __repr__(self):
        return f"{self.type}('{self.value}')"

class TokenParser:
    """Parser para leer tokens desde archivo de salida del analizador léxico"""
    
    @staticmethod
    def parse_tokens_file(filename):
        """
        Lee tokens desde un archivo con formato:
        TOKEN_TYPE      'value'
        """
        tokens = []
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
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
            print(f"Error: No se encontró el archivo {filename}")
            return []
        except Exception as e:
            print(f"Error leyendo archivo: {e}")
            return []
        
        return tokens

class SyntaxAnalyzer:
    """Analizador sintáctico integrado"""
    
    def __init__(self, grammar_file):
        """
        Inicializa el analizador sintáctico con una gramática.
        
        Args:
            grammar_file: Archivo .yalp con la gramática
        """
        print(f"Cargando gramática desde: {grammar_file}")
        self.table, self.parser, _ = analyze_slr_grammar(grammar_file)
        
        if not self.table or not self.parser:
            raise ValueError(f"No se pudo cargar la gramática desde {grammar_file}")
        
        print("✓ Analizador sintáctico cargado correctamente")
    
    def analyze_tokens_file(self, tokens_file):
        """
        Analiza tokens desde un archivo de salida del analizador léxico.
        
        Args:
            tokens_file: Archivo con tokens en formato TOKEN_TYPE 'value'
            
        Returns:
            dict: Resultado del análisis
        """
        print(f"\nLeyendo tokens desde: {tokens_file}")
        
        # 1. Leer tokens del archivo
        lexical_tokens = TokenParser.parse_tokens_file(tokens_file)
        
        if not lexical_tokens:
            return {
                'success': False,
                'error': 'No se pudieron leer tokens del archivo',
                'lexical_tokens': [],
                'syntax_tokens': [],
                'steps': []
            }
        
        print(f"✓ Se leyeron {len(lexical_tokens)} tokens")
        
        # 2. Filtrar y mapear tokens para el analizador sintáctico
        syntax_tokens = self.map_tokens_for_syntax(lexical_tokens)
        
        print(f"✓ Se mapearon {len(syntax_tokens)} tokens para análisis sintáctico")
        print(f"Tokens para sintáctico: {syntax_tokens}")
        
        # 3. Realizar análisis sintáctico
        success, steps, message = self.parser.parse(syntax_tokens)
        
        return {
            'success': success,
            'message': message,
            'lexical_tokens': lexical_tokens,
            'syntax_tokens': syntax_tokens,
            'steps': steps,
            'total_lexical_tokens': len(lexical_tokens),
            'total_syntax_tokens': len(syntax_tokens)
        }
    
    def map_tokens_for_syntax(self, lexical_tokens):
        """
        Mapea tokens del analizador léxico al formato esperado por el sintáctico.
        
        Args:
            lexical_tokens: Lista de LexicalToken del analizador léxico
            
        Returns:
            list: Lista de strings con nombres de tokens para el sintáctico
        """
        syntax_tokens = []
        
        for token in lexical_tokens:
            # Filtrar tokens que no necesita el analizador sintáctico
            if self.should_ignore_token(token):
                continue
            
            # Mapear nombre del token
            mapped_token = self.map_token_name(token.type)
            if mapped_token:
                syntax_tokens.append(mapped_token)
        
        return syntax_tokens
    
    def should_ignore_token(self, token):
        """
        Determina si un token debe ser ignorado por el analizador sintáctico.
        
        Args:
            token: LexicalToken
            
        Returns:
            bool: True si debe ignorarse
        """
        # Ignorar whitespace y otros tokens no significativos
        ignored_tokens = {
            'WS',           # Whitespace
            'WHITESPACE',   # Whitespace alternativo
            'COMMENT',      # Comentarios
            'NEWLINE',      # Saltos de línea
        }
        
        return token.type in ignored_tokens
    
    def map_token_name(self, lexical_token_type):
        """
        Mapea el nombre de un token del léxico al nombre esperado por el sintáctico.
        
        Args:
            lexical_token_type: Nombre del token en el analizador léxico
            
        Returns:
            str: Nombre del token para el analizador sintáctico, o None si no se mapea
        """
        # Mapeo entre tokens del léxico y tokens del sintáctico
        token_mapping = {
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
            
            # Otros
            'SEMICOLON': 'SEMICOLON',
            'ASSIGN': 'ASSIGNOP',
            'ASSIGNOP': 'ASSIGNOP',
        }
        
        # Buscar mapeo directo
        if lexical_token_type in token_mapping:
            return token_mapping[lexical_token_type]
        
        # Si no hay mapeo específico, usar el nombre original
        # (útil cuando los nombres coinciden)
        return lexical_token_type
    
    def print_analysis_report(self, result):
        """Imprime un reporte detallado del análisis"""
        print("\n" + "="*60)
        print("REPORTE DE ANÁLISIS SINTÁCTICO")
        print("="*60)
        
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   Tokens léxicos leídos: {result['total_lexical_tokens']}")
        print(f"   Tokens para sintáctico: {result['total_syntax_tokens']}")
        print(f"   Pasos de análisis: {len(result['steps'])}")
        
        print(f"\n🎯 RESULTADO:")
        if result['success']:
            print(f"   ✅ ÉXITO: {result['message']}")
        else:
            print(f"   ❌ ERROR: {result['message']}")
        
        print(f"\n🔍 TOKENS LÉXICOS (primeros 10):")
        for i, token in enumerate(result['lexical_tokens'][:10]):
            print(f"   {i+1:2d}. {token}")
        if len(result['lexical_tokens']) > 10:
            print(f"   ... y {len(result['lexical_tokens']) - 10} más")
        
        print(f"\n🔧 TOKENS SINTÁCTICOS:")
        if result['syntax_tokens']:
            tokens_str = ' '.join(result['syntax_tokens'])
            if len(tokens_str) > 80:
                tokens_str = tokens_str[:77] + "..."
            print(f"   {tokens_str}")
        else:
            print("   (ninguno)")

def main():
    """Función principal"""
    if len(sys.argv) != 3:
        print("Uso: python syntax_analyzer.py <grammar.yalp> <tokens_file.txt>")
        print("\nEjemplo:")
        print("  python syntax_analyzer.py resources/slr-1.yalp resources/tokens_output.txt")
        sys.exit(1)
    
    grammar_file = sys.argv[1]
    tokens_file = sys.argv[2]
    
    try:
        # Crear analizador sintáctico
        analyzer = SyntaxAnalyzer(grammar_file)
        
        # Analizar tokens
        result = analyzer.analyze_tokens_file(tokens_file)
        
        # Mostrar reporte
        analyzer.print_analysis_report(result)
        
        # Código de salida
        sys.exit(0 if result['success'] else 1)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()