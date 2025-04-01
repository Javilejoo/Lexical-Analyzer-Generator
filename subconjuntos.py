from graphviz import Digraph

# Alias para tipos (opcional)
AFDState = frozenset[int]
AFDTransitions = dict[AFDState, dict[str, AFDState]]

def fromAFNToAFD(afn):
    """
    Convierte un AFN (con claves 'transitions', 'inicial' y estados de aceptación
    en 'accepted' o 'aceptacion') a un AFD utilizando el algoritmo de subconjuntos.
    """
    afdTransitions: AFDTransitions = {}
    # Se calcula el cierre epsilon a partir del estado inicial
    closure, inputs = findClosure(afn, afn["inicial"], set())
    travelAFN(afn, frozenset(closure), frozenset(inputs), afdTransitions)

    accepted = []
    for state in afdTransitions:
        # Se considera de aceptación si el estado de aceptación (usamos la clave "accepted" o "aceptacion")
        if ("accepted" in afn and afn["accepted"] in state) or ("aceptacion" in afn and afn["aceptacion"] in state):
            accepted.append(state)
    # Se incluye también el estado inicial (closure calculado) en el AFD
    return newAFD(afdTransitions, accepted, frozenset(closure))

def travelAFN(afn: dict, closure: frozenset, inputs: frozenset, stateTransitions: AFDTransitions):
    """
    Recorre el AFN y calcula las transiciones para el AFD.
    Cada 'closure' es un frozenset de números de estado del AFN.
    """
    if closure in stateTransitions:
        return
    stateTransitions[closure] = {}
    for symbol in inputs:
        if symbol == "ε":  # Ignoramos las transiciones epsilon
            continue
        reach = set()
        reachInputs = set()
        for state in closure:
            state_trans = afn["transitions"].get(state, {})
            if symbol not in state_trans:
                continue
            for target in state_trans[symbol]:
                targetClosure, targetInputs = findClosure(afn, target, set())
                reach |= targetClosure
                reachInputs |= targetInputs
        reach = frozenset(reach)
        stateTransitions[closure][symbol] = reach
        travelAFN(afn, reach, frozenset(reachInputs), stateTransitions)

def findClosure(afn: dict, state: int, alreadyEvaluated: set) -> tuple[set, set]:
    """
    Encuentra el cierre epsilon de un estado en el AFN.
    
    Devuelve una tupla (closure, inputs) donde:
      - closure es el conjunto de estados alcanzables mediante transiciones ε
        (incluido el propio state)
      - inputs es el conjunto de símbolos (distintos de ε) que salen del cierre.
    """
    if state in alreadyEvaluated:
        return set(), set()
    alreadyEvaluated.add(state)
    original = afn["transitions"][state]
    closure = {state}
    inputs = set(original.keys())
    if "ε" in original:
        for next_state in original["ε"]:
            foundClosure, foundInputs = findClosure(afn, next_state, alreadyEvaluated)
            closure |= foundClosure
            inputs |= foundInputs
    return closure, inputs

def newAFD(transitions: AFDTransitions, accepted: list[AFDState], inicial: frozenset):
    """
    Crea y retorna un nuevo AFD dado el diccionario de transiciones, la lista
    de estados de aceptación y el estado inicial.
    """
    return {"transitions": transitions, "accepted": accepted, "inicial": inicial}

def generate_dfa_graph(afd, filename="afd_graph"):
    """Genera el grafo del AFD usando Graphviz, renombrando los estados como (por ejemplo, {q0, q1, ...})."""
    dot = Digraph()
    dot.attr(rankdir='LR')
    
    # Agregar nodos: se muestra el frozenset de estados que componen cada estado del AFD
    for state in afd["transitions"]:
        state_label = str(set(state))
        shape = "doublecircle" if state in afd["accepted"] else "circle"
        dot.node(state_label, shape=shape)
    
    # Agregar transiciones
    for state, transitions in afd["transitions"].items():
        state_label = str(set(state))
        for symbol, target in transitions.items():
            target_label = str(set(target))
            dot.edge(state_label, target_label, label=symbol)
    
    dot.render(filename, format="png", cleanup=True)

def afn_to_dict(nfa):
    """
    Función opcional para convertir un AFN (por ejemplo, generado con Thompson)
    a un diccionario con claves numéricas, útil para aplicar el algoritmo de subconjuntos.
    """
    transitions = {}
    state_id = {}
    counter = 0

    def assign_state_id(state):
        nonlocal counter
        if state not in state_id:
            state_id[state] = counter
            transitions[counter] = {}
            counter += 1
        return state_id[state]

    stack = [nfa.inicial]
    visited = set()

    while stack:
        state = stack.pop()
        assign_state_id(state)
        for symbol, next_states in nfa.transiciones.get(state, []):
            for next_state in next_states:
                assign_state_id(next_state)
                transitions[state_id[state]].setdefault(symbol, []).append(state_id[next_state])
                if next_state not in visited:
                    stack.append(next_state)
        visited.add(state)

    afn_dict = {
        "transitions": transitions,
        "accepted": state_id[nfa.aceptacion],
        "inicial": state_id[nfa.inicial],
        "estados": list(state_id.values())
    }
    return afn_dict

# Función para convertir un AFD (con claves en inglés) a español.
def convertir_afd_a_espanol(afd):
    """
    Convierte un AFD con claves en inglés (por ejemplo, "transitions", "accepted", "inicial")
    a un AFD con claves en español: "estados", "transiciones", "aceptacion", "inicial".
    Se asume que si la clave "inicial" no existe, se buscará "initial".
    """
    if "inicial" in afd:
        inicial = afd["inicial"]
    elif "initial" in afd:
        inicial = afd["initial"]
    else:
        raise KeyError("No se encontró la clave de estado inicial en el AFD")
    if "aceptacion" in afd:
        aceptacion = afd["aceptacion"]
    elif "accepted" in afd:
        aceptacion = afd["accepted"]
    else:
        aceptacion = set()
    return {
        "estados": set(afd["transitions"].keys()),
        "transiciones": afd["transitions"],
        "inicial": inicial,
        "aceptacion": set(aceptacion)
    }

