import shuntingyard as sy
import funciones as fun
import estructuras
import graphviz_utils as gv_utils
from nullableVisitor import NullableVisitor
from firstPosVisitor import FirstPosVisitor
from lastPosVisitor import LastPosVisitor
from followPosVisitor import FollowPosVisitor
from AFDGV import dibujar_AFD, dibujar_AFN
from AFD_minimo import minimizar_AFD

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
        print("Procesando regla:", expr)
        # Convertir a postfix
        postfix = sy.convert_infix_to_postfix(expr)
        print("Postfix:", postfix)
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

# Función para unir los AFD minimizados individuales en un AFN global.
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

# Bloque principal
if __name__ == "__main__":
    # Se asume que "output/final_infix.txt" contiene las reglas en el formato (regla)# (una regla por línea).
    reglas_file = "output/final_infix.txt"
    afd_list, ultimo_estado = procesar_reglas_y_generar_afd(reglas_file)
    print("Se generaron", len(afd_list), "AFDs individuales.")
    print("El contador global de estados final es:", ultimo_estado)
    
    # Unir los AFD individuales en un AFN global
    afn_global = unir_afd_individuales(afd_list)
    # Dibujar el AFN global con dibujar_AFN (definida en AFDGV.py)
    dibujar_AFN(afn_global, "output/afn/afn_global")
    
    print("AFN global generado:")
    print("Estados:", afn_global["estados"])
    print("Transiciones:", afn_global["transiciones"])
    print("Estado inicial:", afn_global["inicial"])
    print("Estados de aceptación:", afn_global["aceptacion"])
    
    # Opcional: aquí podrías convertir el AFN global a un AFD global mediante el algoritmo de subconjuntos y luego minimizarlo.
