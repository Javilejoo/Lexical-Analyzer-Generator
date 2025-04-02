
class Node:
    def __init__(self, value=None, left=None, right=None, pos_id=None, tipo_token=None):
        self.value = value
        self.left = left
        self.right = right
        self.pos_id = pos_id  # Identificador de posición (para followpos)
        self.nullable = False
        self.firstpos = set()
        self.lastpos = set()
        self.tipo_token = None

    def __repr__(self):
        return f"Node({self.value}, id={self.pos_id}, nullable={self.nullable}, firstpos={self.firstpos}, lastpos={self.lastpos})"

    def accept(self, visitor):
        """ Permite que un visitante procese este nodo """
        visitor.visit(self)

class Stack:
    def __init__(self):
        self.stack = []

    def push(self, node):
        self.stack.append(node)

    def pop(self):
        if self.stack:
            return self.stack.pop()
        else:
            raise Exception("Stack is empty")

def tokenize_postfix(postfix_expr):
    """
    Tokeniza la expresión postfix de modo que:
      - Los literales entre comillas (ej: "'+'", "'*'", "'('", "')'") se agrupan como un único token.
      - Se agrupan secuencias de escape (por ejemplo, "\n", "\t").
      - El resto se tokeniza carácter a carácter, sin ignorar espacios, tabulaciones ni saltos de línea.
    """
    tokens = []
    i = 0
    while i < len(postfix_expr):
        if postfix_expr[i] == "'":
            # Se encontró el inicio de un literal
            j = i + 1
            literal = ""
            while j < len(postfix_expr) and postfix_expr[j] != "'":
                literal += postfix_expr[j]
                j += 1
            if j < len(postfix_expr):
                # Agregar el token literal completo (con comillas)
                tokens.append("'" + literal + "'")
                i = j + 1
            else:
                # En caso de comilla sin cerrar, se agrega tal cual
                tokens.append("'" + literal)
                i = j
        elif postfix_expr[i] == '\\' and (i + 1) < len(postfix_expr):
            # Agrupar secuencia de escape (por ejemplo, "\n" o "\t")
            tokens.append(postfix_expr[i] + postfix_expr[i+1])
            i += 2
        else:
            # Agregar cualquier carácter, incluidos espacios, tabulaciones y saltos
            tokens.append(postfix_expr[i])
            i += 1
    return tokens

def build_expression_tree(postfix_expr):
    """
    Construye el árbol AST a partir de la expresión postfix.
    
    Utiliza tokenize_postfix para agrupar correctamente los literales.
    Se asume que los operadores (sin comillas) son:
      - Operadores binarios: '|' , '.' y '+' (si se usa sin comillas)
      - Operadores unarios: '*' y '?'
    
    Si un token aparece entre comillas (por ejemplo, "'+'"), se extrae su contenido y se
    trata como operando literal.
    """
    stack = Stack()
    tokens = tokenize_postfix(postfix_expr)
    
    # Conjunto de operadores (sin comillas) para construir nodos internos
    operator_set = {'|', '.', '*', '+', '?'}
    
    for token in tokens:
        if token in operator_set:
            # Token es operador (sin comillas)
            if token in {'|', '.', '+'}:
                try:
                    right = stack.pop()
                    left = stack.pop()
                except Exception as e:
                    raise Exception(f"Error al procesar operador '{token}': la pila está vacía. Tokens: {tokens}") from e
                node = Node(token, left, right)
            elif token in {'*', '?'}:
                try:
                    operand = stack.pop()
                except Exception as e:
                    raise Exception(f"Error al procesar operador unario '{token}': la pila está vacía. Tokens: {tokens}") from e
                node = Node(token, operand, None)
            stack.push(node)
        else:
            # Si el token está entre comillas, se trata como literal
            if token.startswith("'") and token.endswith("'"):
                literal = token[1:-1]
                node = Node(literal)
            elif len(token) == 2 and token[0] == '\\':
                # Manejo de secuencias de escape
                escaped_char = token[1]
                if escaped_char == 'n':
                    node = Node('\n')
                elif escaped_char == 't':
                    node = Node('\t')
                else:
                    node = Node(escaped_char)
            else:
                # Cualquier otro token (incluidos espacios, tabulaciones, etc.) se toma tal cual
                node = Node(token)
            stack.push(node)
    
    if len(stack.stack) != 1:
        raise Exception(f"Error en la construcción del árbol: la pila debería tener un único elemento, pero tiene {len(stack.stack)}. Tokens procesados: {tokens}")
    return stack.pop()