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

def dibujar_AFN(afn, nombre_archivo):
    dot = graphviz.Digraph()
    
    # Configurar nodos
    for estado in afn['estados']:
        if estado == afn['inicial']:
            dot.node(str(estado), color='green', style='filled', fillcolor='lightgreen', shape='circle')
        elif estado in afn['aceptacion']:
            dot.node(str(estado), color='red', style='filled', fillcolor='#ffcccc', shape='doublecircle')
        else:
            dot.node(str(estado), shape='circle')
    
    # Configurar transiciones
    for estado_origen, transiciones in afn['transiciones'].items():
        for simbolo, destinos in transiciones.items():
            # Si 'destinos' no es iterable o es una cadena, convertirlo en un conjunto
            if not isinstance(destinos, (set, list)):
                destinos = {destinos}
            for estado_destino in destinos:
                dot.edge(str(estado_origen), str(estado_destino), label=simbolo)
    
    dot.render(nombre_archivo, format='png', cleanup=True)
    return dot
