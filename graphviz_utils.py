from graphviz import Digraph
from shuntingyard import *
from estructuras import *
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

# arbol de |*.AB|C|a|b|c|AB|C|a|b|c|01|2||*.|01|2|01|2|*.01|2|01|2|*..ε|.E'+''-'|ε|.01|2|01|2|*..ε|.|'+'|'-'|'*'|'/'|'('|')'|#.
infix = "(((' '|\t|\n))+|((A|B|C|a|b|c))(((A|B|C|a|b|c))|((0|1|2)))*|(((0|1|2))+)((((0|1|2))+))?('E'('+'|'-')?(((0|1|2))+))?|'+'|'-'|'*'|'/'|'('|')')#"
postfix = convert_infix_to_postfix(infix)
root = build_expression_tree(postfix)
generate_expression_tree_image(root, "output/expression_tree")