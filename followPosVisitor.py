class FollowPosVisitor:
    def __init__(self):
        self.followpos_table = {}  # Diccionario para almacenar followpos

    def visit(self, node):
        """ Recorre el árbol para calcular followpos """
        if node is None:
            return

        # Inicializar followpos para cada nodo hoja
        if node.left is None and node.right is None:
            if node.pos_id is not None:
                self.followpos_table[node.pos_id] = set()
            return

        # Recorrer hijos primero (Recursión)
        if node.left:
            node.left.accept(self)
        if node.right:
            node.right.accept(self)

        
        if node.value == '.':  # Concatenación
            for i in node.left.lastpos:
                self.followpos_table[i] |= node.right.firstpos  # Agregar firstpos del hijo derecho

        elif node.value == '*':  # Cierre de Kleene
            for i in node.lastpos:
                self.followpos_table[i] |= node.firstpos  # Se conecta a su propio firstpos

    def get_followpos_table(self):
        """ Devuelve la tabla de followpos después de recorrer el árbol """
        return self.followpos_table
