import graphviz

def dibujar_AFD(afd, filename="afd"):
    dot = graphviz.Digraph()
    dot.attr(rankdir='LR')  # Disposición de izquierda a derecha para mejor visualización
    
    # Crear un nodo invisible para la flecha de inicio
    dot.node("start", shape="none", label="", width="0", height="0")

    # Mapeo de estados a nombres simples (q0, q1, etc.)
    estado_a_nombre = {}
    for i, estado in enumerate(afd["estados"]):
        estado_a_nombre[estado] = f"q{i}"
    
    # Agregar estados
    for estado in afd["estados"]:
        color = "black"  
        shape = "circle"  
        
        # Comprobar si este estado es el inicial
        es_inicial = False
        if isinstance(estado, frozenset) and isinstance(afd["inicial"], frozenset):
            # Cuando ambos son frozenset, comparamos los contenidos
            es_inicial = estado == afd["inicial"]
        else:
            # Comparación directa para otros tipos
            es_inicial = estado == afd["inicial"]
            
        if es_inicial:
            color = "green"
        
        # Comprobar si este estado es de aceptación
        es_aceptacion = False
        if isinstance(afd["aceptacion"], (list, set, frozenset)):
            # Si aceptacion es una colección, verificamos si el estado está en ella
            for estado_aceptacion in afd["aceptacion"]:
                if isinstance(estado, frozenset) and isinstance(estado_aceptacion, frozenset):
                    # Cuando ambos son frozenset, comparamos contenidos
                    if estado == estado_aceptacion:
                        es_aceptacion = True
                        break
                else:
                    # Comparación directa para otros tipos
                    if estado == estado_aceptacion:
                        es_aceptacion = True
                        break
        else:
            # Si aceptacion no es una colección, comparamos directamente
            es_aceptacion = estado == afd["aceptacion"]
        
        if es_aceptacion:
            shape = "doublecircle"
            if not es_inicial:
                color = "red"
        
        # Obtener el nombre simplificado del estado
        nombre = estado_a_nombre[estado]
        
        # Crear el nodo con un label más descriptivo
        if isinstance(estado, frozenset):
            # Si el conjunto es pequeño (menos de 4 elementos), mostramos su contenido
            if len(estado) < 4:
                tooltip = f"{set(estado)}"
            else:
                # Para conjuntos grandes, solo mostramos la cantidad de elementos
                tooltip = f"Conjunto con {len(estado)} estados"
            dot.node(nombre, label=nombre, tooltip=tooltip, color=color, shape=shape)
        else:
            # Para estados simples (no conjuntos)
            dot.node(nombre, label=str(estado), color=color, shape=shape)

    # Indicar el estado inicial con una flecha etiquetada "start"
    inicial_nombre = estado_a_nombre[afd["inicial"]]
    dot.edge("start", inicial_nombre, label="start", fontsize="12", 
             tailport="e", headport="w", constraint="true")

    # Agregar transiciones
    for estado, transiciones in afd["transiciones"].items():
        # Verificar si el estado existe en el diccionario de mapeo
        if estado not in estado_a_nombre:
            continue
        
        origen_nombre = estado_a_nombre[estado]
        for simbolo, destino in transiciones.items():
            # Verificar si el destino existe en el diccionario de mapeo
            if destino not in estado_a_nombre:
                continue
                
            destino_nombre = estado_a_nombre[destino]
            # Crear etiqueta para la transición
            dot.edge(origen_nombre, destino_nombre, label=simbolo, fontsize="10")

    # Configurar el espaciado y diseño
    dot.attr(overlap="false", splines="true", nodesep="0.5")
    
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
