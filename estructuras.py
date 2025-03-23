
class Node:
    def __init__(self, value=None, left=None, right=None, pos_id=None):
        self.value = value
        self.left = left
        self.right = right
        self.pos_id = pos_id  # Identificador de posición (para followpos)
        self.nullable = False
        self.firstpos = set()
        self.lastpos = set()

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

def build_expression_tree(postfix_expr):
    stack = Stack()
    
    # Tokenizar la expresión postfija manualmente
    tokens = []
    i = 0
    while i < len(postfix_expr):
        char = postfix_expr[i]
        if char == '\\' and (i + 1) < len(postfix_expr):
            tokens.append(char + postfix_expr[i+1])  # Agrupar '\' y el siguiente carácter
            i += 2
        else:
            tokens.append(char)
            i += 1
    
    # Construir el árbol con tokens correctos
    for token in tokens:
        if token in {'|', '.', '*'}:
            if token in {'|', '.'}:
                right = stack.pop()
                left = stack.pop()
                node = Node(token, left, right)
            else:
                operand = stack.pop()
                node = Node(token, operand, None)
        else:
            # Manejar caracteres escapados y espacios
            if len(token) == 2 and token[0] == '\\':
                escaped_char = token[1]
                if escaped_char == 'n':
                    node = Node('\n')
                elif escaped_char == 't':
                    node = Node('\t')
                else:
                    node = Node(escaped_char)
            elif token == ' ':
                node = Node(' ')
            else:
                node = Node(token)
        
        stack.push(node)
    
    return stack.pop()