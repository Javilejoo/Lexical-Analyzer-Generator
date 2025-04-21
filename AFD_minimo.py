# Función para minimizar un AFD
def minimizar_AFD(afd, offset=0):
    estado_a_token_min = {}
    estados = set(afd["transiciones"].keys())
    aceptacion = set(afd["aceptacion"])
    no_aceptacion = estados - aceptacion

    particiones = [aceptacion, no_aceptacion]
    refinado = True

    while refinado:
        refinado = False
        nuevas_particiones = []

        for grupo in particiones:
            subgrupos = {}

            for estado in grupo:
                clave = tuple(sorted(
                    (simbolo, encontrar_particion(afd["transiciones"].get(estado, {}).get(simbolo), particiones))
                    for simbolo in afd["transiciones"].get(estado, {})
                ))
                if clave not in subgrupos:
                    subgrupos[clave] = set()
                subgrupos[clave].add(estado)

            nuevas_particiones.extend(subgrupos.values())
            if len(subgrupos) > 1:
                refinado = True

        particiones = nuevas_particiones

    # Construcción del nuevo AFD minimizado
    estado_mapeo = {frozenset(particion): f"q{offset + idx}" for idx, particion in enumerate(particiones)}
    alfabeto_original = afd.get("alfabeto", set())
    
    nuevo_afd = {
        "estados": set(estado_mapeo.values()),
        "transiciones": {},
        "inicial": estado_mapeo[frozenset(encontrar_particion(afd["inicial"], particiones))],
        "aceptacion": set(),
        "alfabeto": alfabeto_original
    }

    for particion in particiones:
        representativo = next(iter(particion))
        nuevo_estado = estado_mapeo[frozenset(particion)]

        if representativo in aceptacion:
            nuevo_afd["aceptacion"].add(nuevo_estado)

            token_type = afd.get("token_type_map", {}).get(representativo)
            if token_type:
                estado_a_token_min[nuevo_estado] = token_type
        nuevo_afd["transiciones"][nuevo_estado] = {}

        for simbolo, destino in afd["transiciones"].get(representativo, {}).items():
            nuevo_afd["transiciones"][nuevo_estado][simbolo] = estado_mapeo[
                frozenset(encontrar_particion(destino, particiones))
            ]

    return nuevo_afd, offset + len(particiones), estado_a_token_min

def encontrar_particion(estado, particiones):
    """Devuelve la partición (como frozenset) en la que se encuentra un estado."""
    for particion in particiones:
        if estado in particion:
            return frozenset(particion)  # ← Ahora devuelve un frozenset
    return frozenset()  # ← Evita errores devolviendo un frozenset vacío
