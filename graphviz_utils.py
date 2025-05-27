from graphviz import Digraph
from shuntingyard import *
import estructuras
from graphviz import Digraph

def generate_expression_tree_image(root, filename):
    dot = Digraph(format='png')

    def esc_val(v: str) -> str:
        # 1) Duplica barras
        s = v.replace("\\", "\\\\")
        # 2) Escapa comillas dobles
        s = s.replace('"', '\\"')
        # 3) Representa saltos de línea como '\n' literales
        s = s.replace("\n", "\\n")
        return s

    def add_nodes_edges(node):
        if not node:
            return

        raw = node.value or ""
        safe = esc_val(raw)

        # Monta tu label con safe; la librería de Python se encargará
        # de envolverlo entre comillas externas
        label = f"{safe}\\n(ε={node.nullable} f={node.firstpos} l={node.lastpos})"
        dot.node(str(id(node)), label=label)

        if node.left:
            dot.edge(str(id(node)), str(id(node.left)))
            add_nodes_edges(node.left)
        if node.right:
            dot.edge(str(id(node)), str(id(node.right)))
            add_nodes_edges(node.right)

    add_nodes_edges(root)
    dot.render(filename, cleanup=True)



