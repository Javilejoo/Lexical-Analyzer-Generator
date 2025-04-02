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

# Procesa una lista de expresiones (cada una es una regla en formato "(regla)#")
# y genera el AFD minimizado para cada regla, actualizando el contador global de pos_id.
def ERtoAFD_por_regla(lista_expresiones, pos_counter_inicial=1):
    afd_list = []
    pos_counter = pos_counter_inicial
    for expr in lista_expresiones:
        # Asegurarse de que la expresión tenga el símbolo final "#"
        if not expr.endswith("#"):
            expr = expr + "#"
        print("Procesando regla:", expr.encode('utf-8').decode('utf-8'))
        # Convertir a postfix
        postfix = sy.convert_infix_to_postfix(expr)
        print("Postfix:", postfix.encode('utf-8').decode('utf-8'))
        # Construir el árbol de expresión (AST)
        root = estructuras.build_expression_tree(postfix)
        
        # Asignar pos_id globalmente usando assign_pos_ids
        pos_counter = assign_pos_ids(root, pos_counter)
        
        # Calcular nullable, firstpos, lastpos y followpos
        visitors = [NullableVisitor(), FirstPosVisitor(), LastPosVisitor(), FollowPosVisitor()]
        for visitor in visitors:
            root.accept(visitor)
        followpos_table = visitors[3].get_followpos_table()
        
        # (Opcional) Generar imagen del árbol de expresión para esta regla
        gv_utils.generate_expression_tree_image(root, f"output/trees/expression_tree_rule_{pos_counter}.png")
        print("Árbol de expresión generado para regla.")
        
        # Construir el AFD a partir del árbol y la tabla followpos
        afd = construir_afd(root, followpos_table)
        # Minimizar el AFD; minimizar_AFD devuelve (afd_min, nuevo_offset)
        afd_min, pos_counter = minimizar_AFD(afd, pos_counter)
        # Dibujar el AFD minimizado
        dibujar_AFD(afd_min, f"output/afd/afd_min_rule_{pos_counter}")
        afd_list.append(afd_min)
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
    
    for afd in afd_list:
        afn_global["estados"].update(afd["estados"])
        afn_global["alfabeto"].update(afd["alfabeto"])
        for estado, trans in afd["transiciones"].items():
            if estado in afn_global["transiciones"]:
                afn_global["transiciones"][estado].update(trans)
            else:
                afn_global["transiciones"][estado] = trans.copy()
        afn_global["aceptacion"].update(afd["aceptacion"])
        # Conectar S0 (nuevo_inicial) con el estado inicial de este AFD individual
        afn_global["transiciones"][nuevo_inicial][epsilon].add(afd["inicial"])
    
    return afn_global

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
    return {"transitions": new_transitions, "aceptacion": new_accepted, "inicial": new_inicial}

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

# Función para simular el AFD en un archivo de entrada y generar tokens
def simular_codigo_y_generar_tokens(afd_final, input_file_path, output_file_path):
    """
    Lee un archivo de entrada caracter por caracter y genera un archivo de salida con los tokens reconocidos.
    
    Args:
        afd_final: El AFD final generado (no se usa en esta versión simplificada)
        input_file_path: Ruta al archivo de entrada (code_example.txt)
        output_file_path: Ruta al archivo de salida para los tokens reconocidos
    """
    try:
        # Leer el archivo de entrada
        with open(input_file_path, 'r', encoding='utf-8') as input_file:
            input_text = input_file.read()
        
        print(f"\nProcesando el archivo: {input_file_path}")
        print(f"Contenido (primeros 50 caracteres): {input_text[:50]}...")
        
        # Inicializar variables para seguimiento de posición
        tokens = []
        lineno = 1
        column = 1
        token_id = 1
        
        # Procesar cada caracter
        for char in input_text:
            # Determinar el tipo de token
            if char.isalpha():
                token_type = "LETTER"
            elif char.isdigit():
                token_type = "NUMBER"
            elif char in ['+', '-', '*', '/', '(', ')', '{', '}', '[', ']', ';', ',', '.', '=', '<', '>', '!']:
                token_type = "SYMBOL"
            elif char.isspace():
                # Actualizar línea y columna para espacios en blanco
                if char == '\n':
                    lineno += 1
                    column = 0  # Se incrementará a 1 abajo
                token_type = "WHITESPACE"
            else:
                token_type = "OTHER"
            
            # Agregar token a la lista
            tokens.append({
                'id': token_id,
                'type': token_type,
                'value': char,
                'lineno': lineno,
                'column': column
            })
            
            # Incrementar contadores
            token_id += 1
            column += 1
        
        # Escribir los tokens al archivo de salida
        with open(output_file_path, 'w', encoding='utf-8') as output_file:
            output_file.write(f"  #   TIPO            VALOR                LÍNEA COLUMNA\n")
            output_file.write(f"------------------------------------------------------------\n")
            
            for token in tokens:
                # Ignorar espacios en blanco en la salida si se desea
                if token['type'] != "WHITESPACE":
                    output_file.write(f"  {token['id']:<3} {token['type']:<15} '{token['value']}'".ljust(35) + 
                                     f"{token['lineno']:<6} {token['column']:<6}\n")
        
        print(f"\nAnálisis completado. Se encontraron {len(tokens)} caracteres.")
        print(f"Resultados guardados en {output_file_path}")
        
    except Exception as e:
        print(f"Error durante el análisis: {str(e)}")
        import traceback
        traceback.print_exc()

# Bloque principal
if __name__ == "__main__":
    # Se asume que "output/final_infix.txt" contiene las reglas en el formato (regla)# (una regla por línea).
    reglas_file = "output/final_infix.txt"
    afd_list, ultimo_estado = procesar_reglas_y_generar_afd(reglas_file)
    print("Se generaron", len(afd_list), "AFDs individuales.")
    print("El contador global de estados final es:", ultimo_estado)
    
    # Unir los AFDs en un AFN global
    afn_global = unir_afd_individuales(afd_list)
    print("\nSe generó el AFN global uniendo los AFDs individuales.")
    
    # Normalizar las transiciones del AFN global
    afn_global = normalizar_transiciones(afn_global)
    
    # Convertir el AFN a formato numérico
    afn_numerico = convertir_afn_numerico(afn_global)
    print("\nAFN convertido a formato numérico para el algoritmo de subconjuntos.")
    
    # Convertir AFN a AFD usando el algoritmo de subconjuntos
    afd_final = fromAFNToAFD(afn_numerico)
    print("\nSe generó el AFD final usando el algoritmo de subconjuntos.")
    
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
    
    # Generar visualización del AFD final
    dibujar_AFD(afd_final, "output/afd/afd_final_subconjuntos")
    print("\nSe generó la visualización del AFD final en output/afd/afd_final_subconjuntos")
    
    # Simular el código de entrada y generar tokens
    input_file_path = "code_example.txt"
    output_file_path = "tokens_output.txt"
    print(f"\nSimulando el código en {input_file_path}...")
    simular_codigo_y_generar_tokens(afd_final, input_file_path, output_file_path)
