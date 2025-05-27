import shuntingyard as sy
import funciones as fun
import estructuras
import graphviz_utils as gv_utils
import sys
import io
from nullableVisitor import NullableVisitor
from firstPosVisitor import FirstPosVisitor
from lastPosVisitor import LastPosVisitor
from followPosVisitor import FollowPosVisitor
from AFDGV import dibujar_AFD, dibujar_AFN
from AFD_minimo import minimizar_AFD
from subconjuntos import fromAFNToAFD

# Configurar la codificación de salida a UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Función para asignar pos_id de forma global usando un contador (offset)
def assign_pos_ids(root, counter=1):
    def traverse(node, counter):
        if node is None:
            return counter
        if node.value != 'ε' and node.left is None and node.right is None:
            node.pos_id = counter
            counter += 1
        counter = traverse(node.left, counter)
        counter = traverse(node.right, counter)
        return counter
    return traverse(root, counter)

def asignar_token_type_a_nodo_final(node, token_type):
    if node is None:
        return
    if node.left is None and node.right is None and node.value == '#':
        node.tipo_token = token_type
    asignar_token_type_a_nodo_final(node.left, token_type)
    asignar_token_type_a_nodo_final(node.right, token_type)

# Procesa una lista de expresiones (cada una es una regla en formato "(regla)#")
# y genera el AFD minimizado para cada regla, actualizando el contador global de pos_id.
def ERtoAFD_por_regla(lista_expresiones, pos_counter_inicial=1):
    afd_list = []
    pos_counter = pos_counter_inicial
    for expr in lista_expresiones:
        # Asegurarse de que la expresión tenga el símbolo final "#"
        corte = expr.rfind("#") + 1
        if corte == 0:
            continue
        core = expr[:corte - 1]
        expr_solo = f"({core})#"
       
        nombre_token = expr[corte:].replace("-->", "").strip()
        print("Procesando regla:", expr_solo.encode('utf-8').decode('utf-8'))
        # Convertir a postfix
        postfix = sy.convert_infix_to_postfix(expr_solo)
        print("Postfix:", postfix.encode('utf-8').decode('utf-8'))
        # Construir el árbol de expresión (AST)
        root = estructuras.build_expression_tree(postfix)
        asignar_token_type_a_nodo_final(root, nombre_token)
        
        # Asignar pos_id globalmente usando assign_pos_ids
        pos_counter = assign_pos_ids(root, pos_counter)
        
        # Calcular nullable, firstpos, lastpos y followpos
        visitors = [NullableVisitor(), FirstPosVisitor(), LastPosVisitor(), FollowPosVisitor()]
        for visitor in visitors:
            root.accept(visitor)
        followpos_table = visitors[3].get_followpos_table()
        
        # Generar imagen del árbol de expresión para esta regla
        gv_utils.generate_expression_tree_image(root, f"output/trees/expression_tree_rule_{pos_counter}.png")
        print("Árbol de expresión generado para regla.")
        
        # Construir el AFD a partir del árbol y la tabla followpos
        afd = construir_afd(root, followpos_table)
        afd["token_type_map"] = {}
        for estado in afd["aceptacion"]:
            afd["token_type_map"][estado] = nombre_token

        # Minimizar el AFD; minimizar_AFD devuelve (afd_min, nuevo_offset)
        afd_min, pos_counter, estado_a_token_min = minimizar_AFD(afd, pos_counter)
        #afd_min["token_type"] = nombre_token
        print(f"Estados de aceptación para token '{nombre_token}': {afd_min['aceptacion']}")
        # Dibujar el AFD minimizado
        dibujar_AFD(afd_min, f"output/afd/afd_min_rule_{pos_counter}", token_type=estado_a_token_min)
        afd_list.append((afd_min, nombre_token))
    return afd_list, pos_counter

# Función para construir el AFD (sin minimizar) a partir del AST y la tabla followpos
def construir_afd(root, followpos_table):
    alfabeto = set()
    hojas = []
    
    def recolectar_hojas(node):
        if node:
            if node.left is None and node.right is None and node.value != 'ε':
                if node.value != '#':
                    alfabeto.add(node.value)
                hojas.append(node)
            recolectar_hojas(node.left)
            recolectar_hojas(node.right)
    recolectar_hojas(root)
    
    estados = {}
    estado_inicial = frozenset(root.left.firstpos)  # Se asume que la raíz tiene hijo izquierdo con firstpos
    por_procesar = [estado_inicial]
    procesados = set()
    aceptacion = set()
    
    # Obtener el pos_id del símbolo final '#' (debe existir)
    pos_final = next(hoja.pos_id for hoja in hojas if hoja.value == '#')
    
    while por_procesar:
        estado_actual = por_procesar.pop(0)
        if estado_actual in procesados:
            continue
        procesados.add(estado_actual)
        
        if pos_final in estado_actual:
            aceptacion.add(estado_actual)
        
        transiciones = {}
        for simbolo in alfabeto:
            posiciones_simbolo = {hoja.pos_id for hoja in hojas if hoja.value == simbolo}
            U = set()
            for pos in estado_actual:
                if pos in posiciones_simbolo:
                    U.update(followpos_table.get(pos, set()))
            if U:
                U_frozen = frozenset(U)
                transiciones[simbolo] = U_frozen
                if U_frozen not in procesados:
                    por_procesar.append(U_frozen)
        estados[estado_actual] = transiciones
    
    return {
        "estados": list(procesados),
        "alfabeto": alfabeto,
        "transiciones": estados,
        "inicial": estado_inicial,
        "aceptacion": list(aceptacion)
    }

# Función simular_afd (para pruebas, se mantiene igual)
def simular_afd(afd, cadena):
    for simbolo in cadena:
        if simbolo not in afd['alfabeto']:
            return False
    estado_actual = afd['inicial']
    for simbolo in cadena:
        transiciones = afd['transiciones'].get(estado_actual, {})
        estado_actual = transiciones.get(simbolo, None)
        if estado_actual is None:
            return False
    return estado_actual in afd['aceptacion']

# Función para unir los AFDs individuales en un AFN global.
# Crea un nuevo estado inicial "S0" y agrega transiciones ε desde S0 a cada estado inicial individual.
def unir_afd_individuales(afd_list):
    estado_a_token = {}
    nuevo_inicial = "S0"
    afn_global = {
        "estados": {nuevo_inicial},
        "alfabeto": set(),
        "transiciones": {},
        "inicial": nuevo_inicial,
        "aceptacion": set()
    }
    epsilon = 'ε'
    afn_global["transiciones"][nuevo_inicial] = {epsilon: set()}
    
    for afd, token_name in afd_list:
        afn_global["estados"].update(afd["estados"])
        afn_global["alfabeto"].update(afd["alfabeto"])
        for estado, trans in afd["transiciones"].items():
            if estado in afn_global["transiciones"]:
                afn_global["transiciones"][estado].update(trans)
            else:
                afn_global["transiciones"][estado] = trans.copy()
        for estado_aceptacion in afd["aceptacion"]:
            estado_a_token[estado_aceptacion] = token_name
            afn_global["aceptacion"].add(estado_aceptacion)
        # Conectar S0 (nuevo_inicial) con el estado inicial de este AFD individual
        afn_global["transiciones"][nuevo_inicial][epsilon].add(afd["inicial"])
    
    return afn_global, estado_a_token

# Función para procesar las reglas desde un archivo txt (cada línea en formato "(regla)#")
def procesar_reglas_y_generar_afd(rules_txt_file):
    with open(rules_txt_file, "r", encoding="utf-8") as f:
        reglas = f.read().strip().splitlines()
    afd_list, ultimo_contador = ERtoAFD_por_regla(reglas, pos_counter_inicial=1)
    return afd_list, ultimo_contador


def convertir_afn_numerico(afn):
    mapping = {}
    new_transitions = {}
    counter = 0
    # Asignar un número a cada estado (se itera sobre los estados que aparecen en las transiciones)
    for estado in afn["transiciones"]:
        mapping[estado] = counter
        counter += 1
    # Convertir las transiciones
    for estado, trans in afn["transiciones"].items():
        new_estado = mapping[estado]
        new_transitions[new_estado] = {}
        for simbolo, targets in trans.items():
            # targets es un conjunto de estados (ej.: {"q20", "q60", ...})
            new_transitions[new_estado][simbolo] = {mapping[s] for s in targets}
    new_inicial = mapping[afn["inicial"]]
    new_accepted = {mapping[s] for s in afn["aceptacion"]}
    return {"transitions": new_transitions, "aceptacion": new_accepted, "inicial": new_inicial}, mapping

def normalizar_transiciones(afn):
    for estado, trans in afn["transiciones"].items():
        for simbolo, destino in trans.items():
            if not isinstance(destino, set):
                trans[simbolo] = {destino}
    return afn

def convertir_formato_afd(afd):
    """
    Convierte el formato de AFD devuelto por fromAFNToAFD al formato esperado por dibujar_AFD
    """
    estados = set()
    # Agregar todos los estados que aparecen en las transiciones
    for estado, transiciones in afd["transitions"].items():
        estados.add(estado)
        for _, destinos in transiciones.items():
            if isinstance(destinos, (set, frozenset)):
                estados.update(destinos)
            else:
                estados.add(destinos)
    
    # Asegurarnos de incluir el estado inicial y los estados de aceptación
    estados.add(afd["inicial"])
    
    # Fix: Asegurarnos de que aceptacion es una lista o conjunto para evitar errores
    aceptacion = afd.get("accepted", [])
    if aceptacion is None:
        aceptacion = []
    
    # Si accepted existe y no está vacío, agregarlo a estados
    if isinstance(aceptacion, (list, set, frozenset)):
        estados.update(aceptacion)
    else:
        estados.add(aceptacion)
    
    return {
        "estados": estados,
        "transiciones": afd["transitions"],
        "inicial": afd["inicial"],
        "aceptacion": aceptacion  # Usar la variable corregida
    }

def simular_codigo_con_tokens(afd, estado_a_token, archivo_entrada, archivo_salida):
    with open(archivo_entrada, "r", encoding="utf-8") as f:
        codigo = f.read()

    resultado = []
    i = 0
    while i < len(codigo):
        estado_actual = afd["inicial"]
        lexema = ""
        ultimo_token = None
        ultimo_pos = i
        estado_antes = estado_actual

        j = i
        while j < len(codigo):
            simbolo = codigo[j]

            transiciones = afd["transiciones"].get(estado_actual, {})
            siguiente_estado = transiciones.get(simbolo)

            if siguiente_estado is None:
                break

            estado_actual = siguiente_estado
            lexema += simbolo

            if estado_actual in afd["aceptacion"]:
                ultimo_token = afd.get("token_type_map", {}).get(estado_actual, "UNKNOWN")
                ultimo_pos = j + 1  # guarda el último punto válido

            j += 1

        if ultimo_token:
            resultado.append((codigo[i:ultimo_pos], ultimo_token))
            i = ultimo_pos
        else:
            resultado.append((codigo[i], "ERROR"))
            i += 1

    with open(archivo_salida, "w", encoding="utf-8") as f:
        for lexema, token in resultado:
            f.write(f"{token:<15} {lexema!r}\n")

    print(f"\nTokens escritos en {archivo_salida}")

# Bloque principal
if __name__ == "__main__":
    # Limpiar todos los folders output/afd, output/afn y output/trees
    import shutil
    shutil.rmtree("output/afd", ignore_errors=True)
    shutil.rmtree("output/afn", ignore_errors=True)
    shutil.rmtree("output/trees", ignore_errors=True)
    reglas_file = "output/final_infix.txt"
    afd_list, ultimo_estado = procesar_reglas_y_generar_afd(reglas_file)
    print("Se generaron", len(afd_list), "AFDs individuales.")
    print("El contador global de estados final es:", ultimo_estado)
    
    # Unir los AFDs en un AFN global
    afn_global, estado_a_token = unir_afd_individuales(afd_list)
    print("\nEstados de aceptación del AFN global:")
    print(afn_global["aceptacion"])

    print("\nSe generó el AFN global uniendo los AFDs individuales.")
    
    # Asegurar que el directorio output/afn existe
    import os
    os.makedirs("output/afn", exist_ok=True)
    
    # Visualizar el AFN global
    dibujar_AFN(afn_global, "output/afn/afn_global", estado_a_token)
    print("AFN global dibujado en output/afn/afn_global.png")
    
    # Normalizar las transiciones del AFN global
    afn_global = normalizar_transiciones(afn_global)
    
    # Convertir el AFN a formato numérico
    afn_numerico, mapping = convertir_afn_numerico(afn_global)
    print("\nAFN convertido a formato numérico para el algoritmo de subconjuntos.")
    
    # Convertir AFN a AFD usando el algoritmo de subconjuntos
    afd_final = fromAFNToAFD(afn_numerico)
    print("Los estados finales son:", afd_final["accepted"])
    print("\nSe generó el AFD final usando el algoritmo de subconjuntos.")
    
    # El AFD devuelto por fromAFNToAFD no tiene el formato esperado por dibujar_AFD,
    # por lo que primero necesitamos convertirlo
    afd_inicial_formato = {
        "estados": set(afd_final["transitions"].keys()),
        "transiciones": afd_final["transitions"],
        "inicial": afd_final["inicial"],
        "aceptacion": afd_final.get("accepted", [])
    }
    
    # Agregar todos los estados que aparecen en las transiciones
    for _, transiciones in afd_final["transitions"].items():
        for _, destinos in transiciones.items():
            if isinstance(destinos, (set, frozenset)):
               for s in destinos:
                    afd_inicial_formato["estados"].add(frozenset([s]) if isinstance(s, int) else s)
            else:
                afd_inicial_formato["estados"].add(frozenset([destinos]) if isinstance(destinos, int) else destinos)

    afd_inicial_formato["estados"] = {e for e in afd_inicial_formato["estados"] if isinstance(e, frozenset)}

    # Guardar versión inicial del AFD
    dibujar_AFD(afd_inicial_formato, "output/afd/afd_inicial_subconjuntos")
    
    # Si el AFD no tiene estados de aceptación, asignar los estados que contengan algún estado de aceptación del AFN
    if "accepted" in afd_final and (not afd_final["accepted"] or len(afd_final["accepted"]) == 0):
        print("AVISO: El AFD generado no tiene estados de aceptación. Intentando recuperarlos del AFN original.")
        # Identificar los estados del AFD que contengan estados de aceptación del AFN
        estados_afd_aceptacion = []
        for estado_afd in afd_final["transitions"].keys():
            # Si el estado del AFD (que es un conjunto de estados del AFN) contiene algún estado de aceptación del AFN
            if any(estado_afn in afn_numerico["aceptacion"] for estado_afn in estado_afd):
                estados_afd_aceptacion.append(estado_afd)
        
        # Asignar los estados de aceptación recuperados
        afd_final["accepted"] = estados_afd_aceptacion
        print(f"Se recuperaron {len(estados_afd_aceptacion)} estados de aceptación para el AFD.")
    
    # Convertir el formato del AFD para la visualización
    afd_final = convertir_formato_afd(afd_final)
    afd_final["estados"] = {e for e in afd_final["estados"] if isinstance(e, frozenset)}

    afd_final["transiciones"] = {
    k: v for k, v in afd_final["transiciones"].items() if isinstance(k, frozenset)}

    mapping_invertido = {v: k for k, v in mapping.items()}
    estado_final_con_token_nuevo = {}
    for estado in afd_final["aceptacion"]:
        if isinstance(estado, (set, frozenset)):
            for subestado in estado:
                nombre_original = mapping_invertido.get(subestado)
                if nombre_original in estado_a_token:
                    estado_final_con_token_nuevo[estado] = estado_a_token[nombre_original]
                    break
    
    afd_final["token_type_map"] = estado_final_con_token_nuevo
    print("\nVerificación de estados de aceptación y tokens en afd_final:")
    for estado in afd_final["aceptacion"]:
        token = estado_final_con_token_nuevo.get(estado, "NO TOKEN")
        print(f"Estado: {estado} -> Token: {token}")

    # Si tienes token_type_map asociado
    if "token_type_map" in afd_final:
        print("\nToken type por estado de aceptación:")
        for estado, token in afd_final["token_type_map"].items():
            print(f"  {estado} => {token}")

    # Generar visualización del AFD final después de la recuperación de estados
    dibujar_AFD(afd_final, "output/afd/afd_final_subconjuntos",  token_type=estado_final_con_token_nuevo)
    print("\nSe generó la visualización del AFD final en output/afd/afd_final_subconjuntos")
    simular_codigo_con_tokens(afd_final, estado_a_token, "output/tokens/random_data.txt", "output/tokens/tokens_output.txt")
    print("\nSimulación de código con tokens completada. Tokens escritos en output/tokens/tokens_output.txt")
    print("Fin del proceso.")