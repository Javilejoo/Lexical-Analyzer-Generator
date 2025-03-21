from graphviz import Digraph

def generate_expression_tree_image(root, filename):
    dot = Digraph(format='png')

    def add_nodes_edges(node):
        if node:
            is_operator = node.value in {'|', '.', '*', '+'}  # Lista de operadores
            is_epsilon = node.value == 'ε'  # Símbolo epsilon
            if is_operator or is_epsilon:
                label = f"{node.value}\n(nullable={node.nullable}\n(firstpos={node.firstpos}\n(lastpos={node.lastpos})"
            else: 
                label = f"{node.value}\n(pos={node.pos_id})\n(nullable={node.nullable}\n(firstpos={node.firstpos}\n(lastpos={node.lastpos})"
            dot.node(str(id(node)), label=label)

            if node.left:
                dot.edge(str(id(node)), str(id(node.left)))
                add_nodes_edges(node.left)
            if node.right:
                dot.edge(str(id(node)), str(id(node.right)))
                add_nodes_edges(node.right)

    add_nodes_edges(root)
    dot.render(filename, format='png', cleanup=True)
