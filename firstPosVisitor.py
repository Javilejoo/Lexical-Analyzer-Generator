class FirstPosVisitor:
    def visit(self, node):
        """ Calcula firstpos para el nodo recursivamente """
        if node is None:
            return set()
        
        # Si es una hoja, el firstpos es su propia posición si no es ε
        if node.left is None and node.right is None:
            node.firstpos = {node.pos_id} if node.value != 'ε' else set()
            return node.firstpos

        # Visitar hijos primero (Recursión)
        if node.left:
            node.left.accept(self)
        if node.right:
            node.right.accept(self)

        # Aplicar reglas de `firstpos`
        if node.value == '|':
            node.firstpos = node.left.firstpos | node.right.firstpos
        elif node.value == '.':
            if node.left.nullable:
                node.firstpos = node.left.firstpos | node.right.firstpos
            else:
                node.firstpos = node.left.firstpos
        elif node.value == '*':
            node.firstpos = node.left.firstpos
        else:
            node.firstpos = set()  # Cualquier otro nodo que no se haya considerado

        return node.firstpos
