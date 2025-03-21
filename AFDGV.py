import graphviz

def dibujar_AFD(afd, filename="afd"):
    dot = graphviz.Digraph()

    # Agregar estados
    for estado in afd["estados"]:
        color = "black"  
        shape = "circle"  
        
        if estado == afd["inicial"]:
            color = "green"
        
        if estado in afd["aceptacion"]:
            shape = "doublecircle"
            if estado != afd["inicial"]:
                color = "red"
        
        # Crear el nodo
        dot.node(str(estado), color=color, shape=shape)

    # Indicar el estado inicial con una flecha etiquetada "start"
    dot.node("start", shape="none", label="")  # Nodo invisible
    dot.edge("start", str(afd["inicial"]), label="start", fontsize="12")  # Flecha con etiqueta

    # Agregar transiciones
    for estado, transiciones in afd["transiciones"].items():
        for simbolo, destino in transiciones.items():
            dot.edge(str(estado), str(destino), label=simbolo)

    # Guardar el archivo y renderizarlo
    dot.render(filename, format="png", cleanup=True)
    print(f"AFD guardado como {filename}.png")