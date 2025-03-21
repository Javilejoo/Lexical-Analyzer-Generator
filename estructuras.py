
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
    
    for char in postfix_expr:
        if char in {'|', '.', '*'}:
            if char in {'|', '.'}:
                right = stack.pop()
                left = stack.pop()
                node = Node(char, left, right)
            else:
                operand = stack.pop()
                node = Node(char, operand, None)
        else:
            node = Node(char)
        
        stack.push(node)
    
    return stack.pop()

