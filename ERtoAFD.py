'''
Algoritmo para transformar una ezpresion regular a un AFD directamente
1) aumentar la expresion regular con un simbolo de fin de expresion (#)
2) convertir la expresion regular a postfijo (shutingyard algorithm)
3) construir el arbol de expresion
4) asignar identificadores de posicion a los nodos hoja del arbol (simbolos no operadores)
5) calcular si un nodo es nullable
6) Calcular firstpos
7) Calcular lastpos
8) Calcular followpos
9) Construir el AFD
10) Simular el AFD
11) minimizar el AFD
'''
import shuntingyard as sy
import funciones as fun
import estructuras
import graphviz_utils as gv_utils
from nullableVisitor import NullableVisitor
from firstPosVisitor import FirstPosVisitor
from lastPosVisitor import LastPosVisitor
from followPosVisitor import FollowPosVisitor
from AFDGV import dibujar_AFD
from AFD_minimo import minimizar_AFD



def print_tree(node, level=0):
    """Imprime el árbol de expresión con identificadores de posición."""
    if node is not None:
        print_tree(node.right, level + 1)
        print(' ' * 4 * level + f'-> {node.value} (id={node.pos_id}) (nullable={node.nullable})')
        print_tree(node.left, level + 1)

def ERtoAFD(expresion):

    def aumentarER(expresion):
        return expresion + '#'

    postfix = sy.convert_infix_to_postfix(aumentarER(expresion))
    print(postfix)
    root = estructuras.build_expression_tree(postfix)

    def assign_pos_ids(root):
        counter = [1]  # Contador de posiciones para nodos hoja

        def traverse(node):
            if node is None:
                return
            if node.value != 'ε':
                if node.left is None and node.right is None:
                    node.pos_id = counter[0]
                    counter[0] += 1
            
                traverse(node.left)
                traverse(node.right)

        traverse(root)
        return root

    assign_pos_ids(root)
    visitorNull = NullableVisitor()
    root.accept(visitorNull)
    visitorFirstPos = FirstPosVisitor()
    root.accept(visitorFirstPos)
    visitorLastPos = LastPosVisitor()
    root.accept(visitorLastPos)
    visitorFollowPos = FollowPosVisitor()
    root.accept(visitorFollowPos)
    followpos_table = visitorFollowPos.get_followpos_table()

    
    print("Tabla de FollowPos:")
    for pos, follows in sorted(followpos_table.items()):
        print(f"Pos {pos}: {follows}")

    gv_utils.generate_expression_tree_image(root, "expression_tree")

    # Suponiendo que ya tienes el árbol con followpos calculado
    afd = construir_afd(root,followpos_table)
    dibujar_AFD(afd, "afd")

    # Imprimir resultados
    print("Estados:", afd["estados"])
    print("Alfabeto:", afd["alfabeto"])
    print("Estado inicial:", afd["inicial"])
    print("Estados de aceptación:", afd["aceptacion"])
    print("Transiciones:")
    for estado, trans in afd["transiciones"].items():
        print(f"{estado} -- {trans}")
    veces = input("¿Cuántas cadenas desea evaluar? ")
    veces = int(veces)
    for i in range(veces):
        cadena = input(f"Cadena {i+1}: ")
        if simular_afd(afd, cadena):
            print("La cadena es aceptada.")
        else:
            print("La cadena no es aceptada.")

    # Minimizar el AFD
    afd_min = minimizar_AFD(afd)
    dibujar_AFD(afd_min, "afd_min")

def construir_afd(root, followpos_table):
    # Obtener todos los símbolos del alfabeto (excluyendo ε y #)
    alfabeto = set()
    hojas = []
    
    # Función para recolectar símbolos y hojas
    def recolectar_hojas(node):
        if node:
            if node.left is None and node.right is None and node.value != 'ε':
                if node.value != '#':
                    alfabeto.add(node.value)
                hojas.append(node)
            recolectar_hojas(node.left)
            recolectar_hojas(node.right)
    
    recolectar_hojas(root)
    
    # Inicializar estructuras
    estados = {}  # { estado: {transiciones} }
    estado_inicial = frozenset(root.firstpos)
    por_procesar = [estado_inicial]
    procesados = set()
    aceptacion = set()
    
    # Marcar si un estado contiene la posición del símbolo final (#)
    pos_final = next(hoja.pos_id for hoja in hojas if hoja.value == '#')
    
    while por_procesar:
        estado_actual = por_procesar.pop(0)
        if estado_actual in procesados:
            continue
        procesados.add(estado_actual)
        
        # Verificar si es estado de aceptación
        if pos_final in estado_actual:
            aceptacion.add(estado_actual)
        
        # Calcular transiciones para cada símbolo
        transiciones = {}
        for simbolo in alfabeto:
            posiciones_simbolo = {hoja.pos_id for hoja in hojas if hoja.value == simbolo}
            U = set()
            
            # Unir followpos de las posiciones que coinciden con el símbolo
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

def simular_afd(afd, cadena):
    """
    Simula el comportamiento de un AFD para determinar si acepta una cadena.
    
    Args:
        afd (dict): Estructura del AFD con claves 'estados', 'alfabeto', 'transiciones', 'inicial', 'aceptacion'
        cadena (str): Cadena a evaluar
    
    Returns:
        bool: True si la cadena es aceptada, False en caso contrario
    """
    cadena = cadena.replace('\\t', '\t').replace('\\n', '\n').replace(' ', ' ')
    # Verificar símbolos no válidos
    for simbolo in cadena:
        if simbolo not in afd['alfabeto']:
            return False
    
    # Estado inicial
    estado_actual = afd['inicial']
    
    # Procesar cada símbolo de la cadena
    for simbolo in cadena:
        # Obtener transiciones desde el estado actual
        transiciones = afd['transiciones'].get(estado_actual, {})
        
        # Obtener próximo estado
        estado_actual = transiciones.get(simbolo, None)
        
        # Si no hay transición definida
        if estado_actual is None:
            return False
    
    # Verificar si el estado final es de aceptación
    return estado_actual in afd['aceptacion']
        

# Leer la expresión regular desde archivo
expresion = fun.leerER("output/infix_final.txt")

continuar = True
while continuar:
    # Preguntar al usuario si desea generar un AFD o un AFN
    opcion = input("¿Desea generar un AFD (1) o un AFN (2)? ")
    if opcion == "1":
        ERtoAFD(expresion)  # Tu función existente para generar el AFD
    else:
        print("Opción no válida.")
    continuar = input("¿Desea continuar? (s/n) ") == "s"


