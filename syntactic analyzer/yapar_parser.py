import sys
from collections import OrderedDict

class Grammar:
    """Clase para representar una gramática libre de contexto"""
    def __init__(self):
        self.tokens = []           # Lista de terminales
        self.non_terminals = []    # Lista de no-terminales
        self.productions = OrderedDict()  # Dict: {no_terminal: [reglas]}
        self.start_symbol = None   # Símbolo inicial
        self.ignored_tokens = []   # Tokens a ignorar
        self.production_list = []  # Lista numerada de producciones para reducciones

class Production:
    """Clase para representar una producción individual"""
    def __init__(self, left, right, number):
        self.left = left    # Lado izquierdo (no-terminal)
        self.right = right  # Lado derecho (lista de símbolos)
        self.number = number  # Número de producción
    
    def __repr__(self):
        return f"{self.number}: {self.left} → {' '.join(self.right)}"

class YaparLexer:
    """Lexer para tokenizar el archivo YAPar carácter por carácter"""
    def __init__(self, content):
        self.content = content
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        
    def current_char(self):
        """Retorna el carácter actual"""
        if self.position < len(self.content):
            return self.content[self.position]
        return None
    
    def peek_char(self, offset=1):
        """Mira el siguiente carácter sin avanzar"""
        pos = self.position + offset
        if pos < len(self.content):
            return self.content[pos]
        return None
    
    def advance(self):
        """Avanza al siguiente carácter"""
        if self.position < len(self.content):
            if self.content[self.position] == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            self.position += 1
    
    def skip_whitespace(self):
        """Salta espacios en blanco"""
        while self.current_char() and self.current_char() in ' \t\r':
            self.advance()
    
    def skip_comment(self):
        """Salta comentarios /* ... */"""
        if self.current_char() == '/' and self.peek_char() == '*':
            self.advance()  # Skip '/'
            self.advance()  # Skip '*'
            
            while self.current_char():
                if self.current_char() == '*' and self.peek_char() == '/':
                    self.advance()  # Skip '*'
                    self.advance()  # Skip '/'
                    return True
                self.advance()
        return False
    
    def read_identifier(self):
        """Lee un identificador o palabra clave"""
        start_pos = self.position
        
        # Primer carácter debe ser letra o _
        if not (self.current_char().isalpha() or self.current_char() == '_'):
            return None
            
        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            self.advance()
            
        return self.content[start_pos:self.position]
    
    def tokenize(self):
        """Tokeniza todo el contenido"""
        tokens = []
        
        while self.current_char():
            # Saltar espacios en blanco
            if self.current_char() in ' \t\r':
                self.skip_whitespace()
                continue
            
            # Saltar comentarios
            if self.current_char() == '/' and self.peek_char() == '*':
                self.skip_comment()
                continue
            
            # Nueva línea
            if self.current_char() == '\n':
                tokens.append(('NEWLINE', '\n', self.line, self.column))
                self.advance()
                continue
            
            # Porcentaje (para %token)
            if self.current_char() == '%':
                tokens.append(('PERCENT', '%', self.line, self.column))
                self.advance()
                continue
            
            # Dos puntos
            if self.current_char() == ':':
                tokens.append(('COLON', ':', self.line, self.column))
                self.advance()
                continue
            
            # Punto y coma
            if self.current_char() == ';':
                tokens.append(('SEMICOLON', ';', self.line, self.column))
                self.advance()
                continue
            
            # Pipe (|)
            if self.current_char() == '|':
                tokens.append(('PIPE', '|', self.line, self.column))
                self.advance()
                continue
            
            # Separador %%
            if self.current_char() == '%' and self.peek_char() == '%':
                tokens.append(('SEPARATOR', '%%', self.line, self.column))
                self.advance()
                self.advance()
                continue
            
            # Identificador o palabra clave
            if self.current_char().isalpha() or self.current_char() == '_':
                identifier = self.read_identifier()
                if identifier:
                    token_type = 'IDENTIFIER'
                    if identifier == 'token':
                        token_type = 'TOKEN_KW'
                    elif identifier == 'IGNORE':
                        token_type = 'IGNORE_KW'
                    tokens.append((token_type, identifier, self.line, self.column - len(identifier)))
                continue
            
            # Carácter no reconocido - avanzar
            self.advance()
        
        return tokens

class YaparParser:
    """Parser para archivos YAPar que procesa carácter por carácter"""
    def __init__(self, tokens):
        self.tokens = tokens
        self.position = 0
        self.grammar = Grammar()
        
    def current_token(self):
        """Retorna el token actual"""
        if self.position < len(self.tokens):
            return self.tokens[self.position]
        return None
    
    def peek_token(self, offset=1):
        """Mira el siguiente token sin avanzar"""
        pos = self.position + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return None
    
    def advance(self):
        """Avanza al siguiente token"""
        if self.position < len(self.tokens):
            self.position += 1
    
    def skip_newlines(self):
        """Salta tokens de nueva línea"""
        while self.current_token() and self.current_token()[0] == 'NEWLINE':
            self.advance()
    
    def parse_token_declarations(self):
        """Parsea las declaraciones de tokens"""
        while self.current_token():
            self.skip_newlines()
            
            # Buscar %token
            if self.current_token() and self.current_token()[0] == 'PERCENT':
                next_token = self.peek_token()
                if next_token and next_token[0] == 'TOKEN_KW':
                    self.advance()  # Skip %
                    self.advance()  # Skip token
                    
                    # Leer todos los tokens en la línea
                    while self.current_token() and self.current_token()[0] == 'IDENTIFIER':
                        token_name = self.current_token()[1]
                        self.grammar.tokens.append(token_name)
                        self.advance()
                    continue
            
            # Buscar IGNORE
            if self.current_token() and self.current_token()[0] == 'IGNORE_KW':
                self.advance()  # Skip IGNORE
                
                # Leer tokens a ignorar
                while self.current_token() and self.current_token()[0] == 'IDENTIFIER':
                    token_name = self.current_token()[1]
                    self.grammar.ignored_tokens.append(token_name)
                    self.advance()
                continue
            
            # Si encontramos %% o una producción, salir
            if self.current_token():
                if self.current_token()[0] == 'SEPARATOR':
                    self.advance()  # Skip %%
                    break
                # Si es un identificador seguido de ':', es una producción
                if self.current_token()[0] == 'IDENTIFIER' and self.peek_token() and self.peek_token()[0] == 'COLON':
                    break
            
            self.advance()
    
    def parse_production_rule(self):
        """Parsea una regla de producción individual"""
        symbols = []
        
        while self.current_token():
            token_type, value = self.current_token()[0], self.current_token()[1]
            
            # Si encontramos | o ;, terminamos esta regla
            if token_type in ['PIPE', 'SEMICOLON']:
                break
            
            # Si es nueva línea, saltar
            if token_type == 'NEWLINE':
                self.advance()
                continue
            
            # Si es un identificador, agregarlo a la regla
            if token_type == 'IDENTIFIER':
                symbols.append(value)
                self.advance()
            else:
                self.advance()
        
        return symbols
    
    def parse_productions(self):
        """Parsea todas las producciones"""
        while self.current_token():
            self.skip_newlines()
            
            # Buscar una producción (identificador seguido de :)
            if self.current_token() and self.current_token()[0] == 'IDENTIFIER':
                non_terminal = self.current_token()[1]
                self.advance()
                
                # Verificar que sigue ':'
                if self.current_token() and self.current_token()[0] == 'COLON':
                    self.advance()  # Skip :
                    
                    # Inicializar lista de reglas para este no-terminal
                    if non_terminal not in self.grammar.productions:
                        self.grammar.productions[non_terminal] = []
                    
                    # Parsear todas las alternativas
                    while True:
                        self.skip_newlines()
                        
                        # Parsear una regla
                        rule = self.parse_production_rule()
                        if rule:  # Solo agregar si no está vacía
                            self.grammar.productions[non_terminal].append(rule)
                        
                        # Verificar qué sigue
                        if self.current_token():
                            if self.current_token()[0] == 'PIPE':
                                self.advance()  # Skip |
                                continue
                            elif self.current_token()[0] == 'SEMICOLON':
                                self.advance()  # Skip ;
                                break
                        else:
                            break
            else:
                self.advance()
    
    def parse(self):
        """Parsea todo el archivo"""
        # Parsear declaraciones de tokens
        self.parse_token_declarations()
        
        # Parsear producciones
        self.parse_productions()
        
        # Identificar no-terminales
        self.identify_non_terminals()
        
        # Determinar símbolo inicial
        if self.grammar.productions:
            self.grammar.start_symbol = next(iter(self.grammar.productions))
        
        # Crear lista numerada de producciones
        self.create_production_list()
        
        return self.grammar
    
    def identify_non_terminals(self):
        """Identifica los no-terminales de la gramática"""
        self.grammar.non_terminals = list(self.grammar.productions.keys())
    
    def create_production_list(self):
        """Crea la lista numerada de producciones"""
        number = 0
        for non_terminal, rules in self.grammar.productions.items():
            for rule in rules:
                prod = Production(non_terminal, rule, number)
                self.grammar.production_list.append(prod)
                number += 1

def parse_yapar_file(filename):
    """Función principal para parsear un archivo YAPar"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Error: No se pudo encontrar el archivo '{filename}'")
        return None
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None
    
    # Tokenizar el contenido
    lexer = YaparLexer(content)
    tokens = lexer.tokenize()
    
    # Parsear los tokens
    parser = YaparParser(tokens)
    grammar = parser.parse()
    
    return grammar

def print_grammar(grammar):
    """Imprime la gramática de forma legible"""
    if not grammar:
        print("No se pudo parsear la gramática")
        return
    
    print("\n=== GRAMÁTICA PARSEADA ===")
    print(f"\nTokens (Terminales): {grammar.tokens}")
    print(f"Tokens ignorados: {grammar.ignored_tokens}")
    print(f"No-terminales: {grammar.non_terminals}")
    print(f"Símbolo inicial: {grammar.start_symbol}")
    
    print("\nProducciones:")
    for non_terminal, rules in grammar.productions.items():
        for i, rule in enumerate(rules):
            if i == 0:
                print(f"  {non_terminal} → {' '.join(rule)}")
            else:
                print(f"  {' ' * len(non_terminal)} | {' '.join(rule)}")
    
    print("\nProducciones numeradas (para tabla de parsing):")
    for prod in grammar.production_list:
        print(f"  {prod}")

def augment_grammar(grammar):
    """Aumenta la gramática agregando S' → S para el análisis SLR"""
    if not grammar or not grammar.start_symbol:
        return
    
    # Crear nuevo símbolo inicial
    new_start = grammar.start_symbol + "'"
    
    # Agregar nueva producción al inicio
    grammar.productions[new_start] = [[grammar.start_symbol]]
    grammar.productions.move_to_end(new_start, last=False)
    
    # Actualizar listas
    grammar.non_terminals.insert(0, new_start)
    grammar.start_symbol = new_start
    
    # Recrear lista de producciones numeradas
    grammar.production_list = []
    number = 0
    for non_terminal, rules in grammar.productions.items():
        for rule in rules:
            prod = Production(non_terminal, rule, number)
            grammar.production_list.append(prod)
            number += 1
    
    print(f"\nGramática aumentada con: {new_start} → {grammar.production_list[0].right[0]}")