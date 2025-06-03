"""
Implementacion del algoritmo de parsing LR
Este archivo implementa un analizador sintactico LR que muestra los pasos detallados
del proceso de analisis, incluyendo cada accion de shift/reduce y estado.
"""

import os
import sys
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Set, Any

# Importar componentes necesarios
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from slr_table import ActionType, Action, SLRTable, build_slr_table_for_lr0
from lr0_automaton2 import Grammar, Production, Item, State, build_lr0_automaton

class LRParser:
    """
    Analizador sintactico LR que muestra los pasos detallados del analisis.
    """
    def __init__(self, table: SLRTable, grammar: Grammar):
        """
        Inicializa el analizador con una tabla SLR y una gramatica.
        
        Args:
            table: Tabla SLR con las acciones y transiciones
            grammar: Gramatica del lenguaje a analizar
        """
        self.table = table
        self.grammar = grammar
        
    def parse(self, tokens: List[str], verbose: bool = True) -> Tuple[bool, str]:
        """
        Analiza una secuencia de tokens usando el algoritmo LR y muestra cada paso.
        
        Args:
            tokens: Lista de tokens a analizar
            verbose: Si es True, muestra cada paso del analisis
            
        Returns:
            Tuple[bool, str]: (exito, mensaje de resultado)
        """
        # Agregar simbolo de fin de entrada
        input_tokens = tokens.copy()
        if input_tokens[-1] != "$":
            input_tokens.append("$")
            
        # Pila: almacena estados y simbolos alternados, empezando con estado 0
        stack = [0]
        # Indice del token actual
        index = 0
        
        # Mostrar tokens de entrada
        if verbose:
            print("\n========== ANALISIS SINTACTICO LR ==========")
            #print("Tokens de entrada:", input_tokens[:-1])  # No mostrar $ en la salida
            print("="*45)
        
        # Bucle principal del algoritmo
        while True:
            current_state = stack[-1]
            current_token = input_tokens[index]
            
            # Obtener la accion para el estado y token actuales
            action = self.table.get_action(current_state, current_token)
            
            if verbose:
                # Mostrar estado actual y entrada restante
                #print(f"\n[Estado {current_state}] ", end="")
                pass
            
            # Procesar segun el tipo de accion
            if action.type == ActionType.SHIFT:
                # Accion de desplazamiento (shift)
                if verbose:
                    #print(f"ACCION s{action.value} con simbolo '{current_token}'")
                    #print(f"-> shift a estado {action.value}")
                    pass
                
                # Guardar el simbolo y nuevo estado en la pila
                stack.append(current_token)
                stack.append(action.value)
                
                # Avanzar al siguiente token
                index += 1
                
            elif action.type == ActionType.REDUCE:
                # Accion de reduccion (reduce)
                # En algunas implementaciones, los indices de las reglas de produccion
                # En una tabla SLR correctamente construida, el valor de la acción reduce (r#) debería
                # ser el número de producción exacto en la gramática
                
                # Buscar la producción por su número en la gramática
                production = None
                
                # Primero, buscar por número exacto de producción
                for prod in self.grammar.production_list:
                    if hasattr(prod, 'number') and prod.number == action.value:
                        production = prod
                        break
                
                # Si no se encontró, buscar por índice en la lista
                if production is None and action.value < len(self.grammar.production_list):
                    production = self.grammar.production_list[action.value]
                
                # Si aún no se encuentra, buscar por otros métodos
                if production is None:
                    for i, prod in enumerate(self.grammar.production_list):
                        # También buscar por índice implícito
                        if i == action.value:
                            production = prod
                            break
                        # O por algún atributo id si existe
                        elif hasattr(prod, 'id') and prod.id == action.value:
                            production = prod
                            break
                
                # Si todavía no se encontró, reportar error
                if production is None:
                    error_msg = f"Error: No se encontró producción para la acción r{action.value}"
                    if verbose:
                        print(f"ERROR: {error_msg}")
                    return False, error_msg
                
                if verbose:
                    #print(f"ACCION r{action.value} con produccion {production}")
                    #print(f"-> reduce por {production.left} -> {' '.join(production.right)}")
                    pass

                
                # Remover 2*len(right) elementos de la pila (simbolo y estado por cada simbolo)
                symbols_to_remove = len(production.right)
                if symbols_to_remove > 0:
                    stack = stack[:-(2*symbols_to_remove)]
                
                # Obtener el estado superior actual despues de la reduccion
                current_state = stack[-1]
                
                # Obtener el nuevo estado desde GOTO[estado, no-terminal]
                goto_state = self.table.get_goto(current_state, production.left)
                
                if goto_state is None:
                    error_msg = f"Error: No hay transicion GOTO desde estado {current_state} con {production.left}"
                    if verbose:
                        print(f"ERROR: {error_msg}")
                    return False, error_msg
                
                # Agregar el no-terminal y el nuevo estado a la pila
                stack.append(production.left)
                stack.append(goto_state)
                
                if verbose:
                    #print(f"-> GOTO({current_state}, {production.left}) = {goto_state}")
                    pass
                
            elif action.type == ActionType.ACCEPT:
                # Accion de aceptacion (accept)
                if verbose:
                    print(f"ACCION accept")
                    print("\n!Cadena aceptada por el analizador sintactico!")
                return True, "Cadena aceptada"
                
            elif action.type == ActionType.ERROR:
                # Error sintactico
                error_msg = f"Error sintactico en estado {current_state} con token '{current_token}'"
                if verbose:
                    print(f"ERROR: {error_msg}")
                return False, error_msg
            
            # Imprimir la pila actual
            if verbose:
                stack_str = ""
                for i, item in enumerate(stack):
                    if i % 2 == 0:  # Es un estado
                        stack_str += f"{item} "
                    else:  # Es un simbolo
                        stack_str += f"{item} "
                #print(f"tual: {stack_str}")
                
                # Mostrar los simbolos restantes
                remaining = " ".join(input_tokens[index:])
                #print(f"Entrada restante: {remaining}")

def parse_input(slr_table, grammar, input_tokens, verbose=True):
    """
    Analiza una cadena de entrada utilizando el parser LR.
    
    Args:
        slr_table: Tabla SLR con acciones y transiciones
        grammar: Gramatica del lenguaje
        input_tokens: Lista de tokens a analizar
        verbose: Si es True, muestra cada paso del analisis
        
    Returns:
        Tuple[bool, str]: (exito, mensaje de resultado)
    """
    parser = LRParser(slr_table, grammar)
    return parser.parse(input_tokens, verbose)

def run_test_parser(grammar, slr_table, input_tokens=None):
    """
    Ejecuta el analizador sintactico LR con un conjunto de tokens de prueba.
    
    Args:
        grammar: Gramatica del lenguaje
        slr_table: Tabla SLR con acciones y transiciones
        input_tokens: Lista de tokens a analizar (opcional)
        
    Returns:
        bool: True si la cadena es aceptada, False en caso contrario
    """
    # Si no se proporcionan tokens, usar el ejemplo predefinido
    if input_tokens is None:
        input_tokens = ['ID', 'PLUS', 'ID', 'TIMES', 'LPAREN', 'ID', 'PLUS', 'ID', 'RPAREN', '$']
    
    print("\n" + "="*80)
    print("PRUEBA DE ANALISIS SINTACTICO LR")
    print("="*80)
    
    #print(f"Tokens de entrada: {input_tokens}")
    
    # Ejecutar el analisis
    success, message = parse_input(slr_table, grammar, input_tokens)
    
    print("\nResultado:", "ACEPTADA" if success else "RECHAZADA")
    print("Mensaje:", message)
    
    return success

if __name__ == "__main__":
    # Este codigo se ejecuta si el script se ejecuta directamente
    from main_parser import main as main_parser
    
    # Ejemplo de uso:
    # 1. Parsear gramatica y generar tabla SLR usando main_parser
    # 2. Ejecutar prueba con tokens predefinidos
    
    # Tokens de prueba como se especifico
    tokens_inputs = ['ID', 'PLUS', 'ID', 'TIMES', 'LPAREN', 'ID', 'PLUS', 'ID', 'RPAREN', '$']
    
    print("\nEjecutando prueba de analisis sintactico LR con tokens predefinidos...")
    # Nota: Para ejecutar esta prueba, es necesario obtener primero la gramatica y tabla SLR
    # del analizador principal.
