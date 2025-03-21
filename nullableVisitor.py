class NullableVisitor:
    def visit(self, node):
        """ Recursivamente calcula nullable en el árbol de expresión """
        if node is None:
            return False
        
        # Si es una hoja (símbolo terminal)
        if node.left is None and node.right is None:
            node.nullable = (node.value == 'ε')  # Solo ε es nullable
            return node.nullable

        # Visitar hijos primero (Recursión)
        if node.left:
            node.left.accept(self)
        if node.right:
            node.right.accept(self)

        # Aplicar reglas de `nullable`
        if node.value == '|':
            node.nullable = node.left.nullable or node.right.nullable
        elif node.value == '.':
            node.nullable = node.left.nullable and node.right.nullable
        elif node.value == '*':
            node.nullable = True
        else:
            node.nullable = False  # Cualquier otro símbolo no es nullable

        return node.nullable
