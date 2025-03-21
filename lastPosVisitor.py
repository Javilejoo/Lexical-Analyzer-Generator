class LastPosVisitor:
    def visit(self, node):
        """ Calcula lastpos para el nodo recursivamente """
        if node is None:
            return set()
        
        # Si es una hoja, el lastpos es su propia posición si no es ε"""
        if node.left is None and node.right is None:
            node.lastpos = {node.pos_id} if node.value != 'ε' else set()
            return node.lastpos

        # Visitar hijos primero (Recursión)
        if node.left:
            node.left.accept(self)
        if node.right:
            node.right.accept(self)

        # Aplicar reglas de `lastpos`
        if node.value == '|':
            node.lastpos = node.left.lastpos | node.right.lastpos
        elif node.value == '.':
            if node.right.nullable:
                node.lastpos = node.left.lastpos | node.right.lastpos
            else:
                node.lastpos = node.right.lastpos
        elif node.value == '*':
            node.lastpos = node.left.lastpos
        else:
            node.lastpos = set()