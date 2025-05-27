import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yapar_parser import YaparLexer, YaparParser, Grammar, parse_yapar_file, augment_grammar

class TestYaparLexer(unittest.TestCase):
    """Pruebas unitarias para el lexer de YAPar"""
    
    def test_tokenize_simple(self):
        """Prueba tokenización básica"""
        content = "%token ID PLUS"
        lexer = YaparLexer(content)
        tokens = lexer.tokenize()
        
        expected_types = ['PERCENT', 'TOKEN_KW', 'IDENTIFIER', 'IDENTIFIER']
        actual_types = [token[0] for token in tokens]
        
        self.assertEqual(actual_types, expected_types)
        self.assertEqual(tokens[2][1], 'ID')
        self.assertEqual(tokens[3][1], 'PLUS')
    
    def test_tokenize_with_comments(self):
        """Prueba que los comentarios se ignoren correctamente"""
        content = """/* Este es un comentario */
%token ID
/* Otro comentario */ PLUS"""
        
        lexer = YaparLexer(content)
        tokens = lexer.tokenize()
        
        # Los comentarios no deben aparecer en los tokens
        token_values = [token[1] for token in tokens]
        self.assertNotIn('/*', token_values)
        self.assertNotIn('*/', token_values)
        self.assertIn('ID', token_values)
        self.assertIn('PLUS', token_values)
    
    def test_tokenize_productions(self):
        """Prueba tokenización de producciones"""
        content = """expression:
    term PLUS expression
  | term
;"""
        lexer = YaparLexer(content)
        tokens = lexer.tokenize()
        
        # Verificar que se tokenicen correctamente los símbolos
        token_types = [token[0] for token in tokens]
        self.assertIn('COLON', token_types)
        self.assertIn('PIPE', token_types)
        self.assertIn('SEMICOLON', token_types)
    
    def test_tokenize_separator(self):
        """Prueba tokenización del separador %%"""
        content = "%token ID\n%%\nexpression: ID ;"
        lexer = YaparLexer(content)
        tokens = lexer.tokenize()
        
        # Verificar que %% se tokenice como SEPARATOR
        token_types_values = [(token[0], token[1]) for token in tokens]
        self.assertIn(('SEPARATOR', '%%'), token_types_values)
    
    def test_line_column_tracking(self):
        """Prueba que se mantenga correctamente el tracking de línea y columna"""
        content = "%token ID\nexpression:\n  ID\n;"
        lexer = YaparLexer(content)
        tokens = lexer.tokenize()
        
        # Encontrar el token 'expression'
        expr_token = next((t for t in tokens if t[1] == 'expression'), None)
        self.assertIsNotNone(expr_token)
        self.assertEqual(expr_token[2], 2)  # Línea 2

class TestYaparParser(unittest.TestCase):
    """Pruebas unitarias para el parser de YAPar"""
    
    def test_parse_tokens(self):
        """Prueba parsing de declaraciones de tokens"""
        content = "%token ID NUMBER PLUS MINUS"
        lexer = YaparLexer(content)
        tokens = lexer.tokenize()
        parser = YaparParser(tokens)
        grammar = parser.parse()
        
        self.assertEqual(len(grammar.tokens), 4)
        self.assertIn('ID', grammar.tokens)
        self.assertIn('NUMBER', grammar.tokens)
        self.assertIn('PLUS', grammar.tokens)
        self.assertIn('MINUS', grammar.tokens)
    
    def test_parse_ignore(self):
        """Prueba parsing de declaraciones IGNORE"""
        content = """%token ID WS COMMENT
IGNORE WS COMMENT"""
        lexer = YaparLexer(content)
        tokens = lexer.tokenize()
        parser = YaparParser(tokens)
        grammar = parser.parse()
        
        self.assertEqual(len(grammar.ignored_tokens), 2)
        self.assertIn('WS', grammar.ignored_tokens)
        self.assertIn('COMMENT', grammar.ignored_tokens)
    
    def test_parse_simple_production(self):
        """Prueba parsing de una producción simple"""
        content = """expression: ID ;"""
        lexer = YaparLexer(content)
        tokens = lexer.tokenize()
        parser = YaparParser(tokens)
        grammar = parser.parse()
        
        self.assertIn('expression', grammar.productions)
        self.assertEqual(len(grammar.productions['expression']), 1)
        self.assertEqual(grammar.productions['expression'][0], ['ID'])
    
    def test_parse_multiple_alternatives(self):
        """Prueba parsing de producciones con múltiples alternativas"""
        content = """expression:
    expression PLUS term
  | expression MINUS term
  | term
;"""
        lexer = YaparLexer(content)
        tokens = lexer.tokenize()
        parser = YaparParser(tokens)
        grammar = parser.parse()
        
        self.assertEqual(len(grammar.productions['expression']), 3)
        self.assertEqual(grammar.productions['expression'][0], ['expression', 'PLUS', 'term'])
        self.assertEqual(grammar.productions['expression'][1], ['expression', 'MINUS', 'term'])
        self.assertEqual(grammar.productions['expression'][2], ['term'])
    
    def test_start_symbol_identification(self):
        """Prueba que se identifique correctamente el símbolo inicial"""
        content = """expression: term ;
term: ID ;"""
        lexer = YaparLexer(content)
        tokens = lexer.tokenize()
        parser = YaparParser(tokens)
        grammar = parser.parse()
        
        self.assertEqual(grammar.start_symbol, 'expression')
    
    def test_production_numbering(self):
        """Prueba que las producciones se numeren correctamente"""
        content = """expression:
    expression PLUS term
  | term
;
term:
    ID
;"""
        lexer = YaparLexer(content)
        tokens = lexer.tokenize()
        parser = YaparParser(tokens)
        grammar = parser.parse()
        
        self.assertEqual(len(grammar.production_list), 3)
        self.assertEqual(grammar.production_list[0].number, 0)
        self.assertEqual(grammar.production_list[1].number, 1)
        self.assertEqual(grammar.production_list[2].number, 2)

class TestGrammarAugmentation(unittest.TestCase):
    """Pruebas para la aumentación de gramática"""
    
    def test_augment_grammar(self):
        """Prueba que la gramática se aumente correctamente"""
        content = """expression: term ;
term: ID ;"""
        grammar = parse_yapar_file_from_string(content)
        
        original_start = grammar.start_symbol
        augment_grammar(grammar)
        
        # Verificar que se agregó el nuevo símbolo inicial
        self.assertEqual(grammar.start_symbol, original_start + "'")
        self.assertIn(grammar.start_symbol, grammar.productions)
        self.assertEqual(grammar.productions[grammar.start_symbol][0], [original_start])
        
        # Verificar que la producción aumentada sea la número 0
        self.assertEqual(grammar.production_list[0].left, grammar.start_symbol)

class TestIntegration(unittest.TestCase):
    """Pruebas de integración con archivos completos"""
    
    def setUp(self):
        """Configurar rutas de archivos de prueba"""
        self.test_dir = os.path.dirname(os.path.abspath(__file__))
        self.resources_dir = os.path.join(os.path.dirname(self.test_dir), 'resources')
        
    def test_parse_slr_files(self):
        """Prueba parsing de archivos SLR de ejemplo"""
        test_files = ['slr-1.yalp', 'slr-2.yalp', 'slr-3.yalp', 'slr-4.yalp']
        
        for filename in test_files:
            filepath = os.path.join(self.resources_dir, filename)
            if os.path.exists(filepath):
                with self.subTest(file=filename):
                    grammar = parse_yapar_file(filepath)
                    self.assertIsNotNone(grammar)
                    self.assertGreater(len(grammar.productions), 0)
                    self.assertIsNotNone(grammar.start_symbol)
    
    def test_parse_full_format(self):
        """Prueba parsing del formato completo con %%"""
        content = """/* Comentario inicial */
%token ID NUMBER
%token PLUS MINUS
IGNORE WS

%%

/* Producciones */
expression:
    expression PLUS term
  | expression MINUS term
  | term
;

term:
    NUMBER
  | ID
;"""
        
        # Crear archivo temporal
        temp_file = 'temp_test.yalp'
        with open(temp_file, 'w') as f:
            f.write(content)
        
        try:
            grammar = parse_yapar_file(temp_file)
            self.assertIsNotNone(grammar)
            self.assertEqual(len(grammar.tokens), 4)
            self.assertEqual(len(grammar.ignored_tokens), 1)
            self.assertEqual(len(grammar.productions), 2)
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_file):
                os.remove(temp_file)

def parse_yapar_file_from_string(content):
    """Función auxiliar para parsear desde string en lugar de archivo"""
    lexer = YaparLexer(content)
    tokens = lexer.tokenize()
    parser = YaparParser(tokens)
    return parser.parse()

def run_specific_test(test_name=None):
    """Ejecutar una prueba específica o todas"""
    if test_name:
        suite = unittest.TestLoader().loadTestsFromName(test_name)
    else:
        suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_name = sys.argv[1]
        success = run_specific_test(f'__main__.{test_name}')
    else:
        success = run_specific_test()
    
    sys.exit(0 if success else 1)