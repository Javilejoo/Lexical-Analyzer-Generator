import graphviz
def dibujar_AFD(afd, filename="afd", token_type=None):
    import graphviz
    dot = graphviz.Digraph()
    dot.attr(rankdir='LR')

    dot.node("start", shape="none", label="", width="0", height="0")

    estado_a_nombre = {}
    for i, estado in enumerate(afd["estados"]):
        estado_a_nombre[estado] = f"q{i}"

    for estado in afd["estados"]:
        color = "black"
        shape = "circle"

        es_inicial = estado == afd["inicial"] if not isinstance(estado, frozenset) else estado == afd["inicial"]
        if es_inicial:
            color = "green"

        es_aceptacion = any(
            estado == a or (
                isinstance(estado, frozenset) and isinstance(a, frozenset) and estado == a
            )
            for a in afd["aceptacion"]
        )

        if es_aceptacion:
            shape = "doublecircle"
            if not es_inicial:
                color = "red"

        nombre = estado_a_nombre[estado]

        # 🧠 Obtener el token del diccionario (puede ser None)
        token = ""
        if es_aceptacion and isinstance(token_type, dict):
            token = token_type.get(estado, "")
        elif es_aceptacion and isinstance(token_type, str):
            token = token_type  # para el caso de AFD individuales

        # 📌 Crear label
        if isinstance(estado, frozenset):
            tooltip = f"{set(estado)}" if len(estado) < 4 else f"Conjunto con {len(estado)} estados"
            label = f"{nombre}\\n{token}" if token else nombre
            dot.node(nombre, label=label, tooltip=tooltip, color=color, shape=shape)
        else:
            label = f"{nombre}\\n{token}" if token else str(nombre)
            dot.node(nombre, label=label, color=color, shape=shape)

    inicial_nombre = estado_a_nombre[afd["inicial"]]
    dot.edge("start", inicial_nombre, label="start", fontsize="12", tailport="e", headport="w", constraint="true")

    for estado, transiciones in afd["transiciones"].items():
        if estado not in estado_a_nombre:
            continue
        origen_nombre = estado_a_nombre[estado]
        for simbolo, destino in transiciones.items():
            if destino not in estado_a_nombre:
                continue
            destino_nombre = estado_a_nombre[destino]
            dot.edge(origen_nombre, destino_nombre, label=simbolo, fontsize="10")

    dot.attr(overlap="false", splines="true", nodesep="0.5")
    dot.render(filename, format="png", cleanup=True)
    print(f"AFD guardado como {filename}.png")



def dibujar_AFN(afn, nombre_archivo, estado_a_token=None):
    dot = graphviz.Digraph()
    
    # Configurar nodos
    for estado in afn['estados']:
        if estado == afn['inicial']:
            dot.node(str(estado), color='green', style='filled', fillcolor='lightgreen', shape='circle')
        elif estado in afn['aceptacion']:
            token = estado_a_token.get(estado, "") if estado_a_token else ""
            label = f"{estado}\\n{token}" if token else str(estado)
            dot.node(str(estado), label=label, color='red', style='filled', fillcolor='#ffcccc', shape='doublecircle')
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
