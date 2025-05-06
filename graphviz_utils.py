from graphviz import Digraph
from shuntingyard import *
import estructuras
def generate_expression_tree_image(root, filename):
    dot = Digraph(format='png')

    def add_nodes_edges(node):
        if node:
            is_operator = node.value in {'|', '.', '*', '+'}  # Lista de operadores
            is_epsilon = node.value == 'ε'  # Símbolo epsilon
            if is_operator or is_epsilon:
                label = f"{node.value}\n(nullable={node.nullable}\n(firstpos={node.firstpos}\n(lastpos={node.lastpos})"
            else: 
                if node.tipo_token:
                    label = f"{node.value}\nTOKEN: {node.tipo_token}\n(pos={node.pos_id})\n(nullable={node.nullable}\n(firstpos={node.firstpos}\n(lastpos={node.lastpos})"
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


infix = "(' '|'!'|'\"'|'#'|'$'|'%'|'&'|'\\''|'('|')'|'*'|'+'|','|'-'|'.'|'/'|'0'|'1'|'2'|'3'|'4'|'5'|'6'|'7'|'8'|'9'|':'|';'|'<'|'='|'>'|'?'|'@'|'A'|'B'|'C'|'D'|'E'|'F'|'G'|'H'|'I'|'J'|'K'|'L'|'M'|'N'|'O'|'P'|'Q'|'R'|'S'|'T'|'U'|'V'|'W'|'X'|'Y'|'Z'|'['|']'|'^'|'_'|'`'|'a'|'b'|'c'|'d'|'e'|'f'|'g'|'h'|'i'|'j'|'k'|'l'|'m'|'n'|'o'|'p'|'q'|'r'|'s'|'t'|'u'|'v'|'w'|'x'|'y'|'z'|'{'|'|'|'}'|'~')#"
print("📥 INFIX leído:")
print(infix)

    # Convertir infix a postfix
postfix = convert_infix_to_postfix(infix)
print("📤 POSTFIX generado:")
print(postfix)

    # Construir el árbol y graficarlo
root = estructuras.build_expression_tree(postfix)
generate_expression_tree_image(root, "output/trees/str_token_tree")

print("🌳 Árbol de expresión generado y guardado como 'output/trees/str_token_tree.png'")