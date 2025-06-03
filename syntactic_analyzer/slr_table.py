"""
Implementación de la tabla SLR(1) y el parser sintáctico.
Este archivo combina la definición de la tabla SLR y las funciones para construirla.
Core de la solución sin funcionalidades extra.
"""

import os
import sys
from enum import Enum
from collections import defaultdict

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    print("Pandas no está instalado. Se usará formato de texto plano.")
    PANDAS_AVAILABLE = False

class ActionType(Enum):
    """Tipos de acciones en la tabla SLR"""
    SHIFT = "shift"
    REDUCE = "reduce"
    ACCEPT = "accept"
    ERROR = "error"

class Action:
    """Representa una acción en la tabla SLR"""
    def __init__(self, action_type, value=None):
        self.type = action_type
        self.value = value  # Estado para shift, número de producción para reduce
    
    def __repr__(self):
        if self.type == ActionType.SHIFT:
            return f"s{self.value}"
        elif self.type == ActionType.REDUCE:
            return f"r{self.value}"
        elif self.type == ActionType.ACCEPT:
            return "acc"
        else:
            return "err"
    
    def __str__(self):
        return self.__repr__()

class SLRTable:
    """
    Tabla SLR(1) que contiene las tablas ACTION y GOTO.
    """
    def __init__(self, automaton, grammar):
        self.automaton = automaton
        self.grammar = grammar
        self.action_table = {}  # {(state_id, terminal): Action}
        self.goto_table = {}    # {(state_id, non_terminal): state_id}
        self.conflicts = []     # Lista de conflictos detectados
        
    def set_action(self, state_id, terminal, action):
        """Establece una acción en la tabla ACTION"""
        key = (state_id, terminal)
        
        # Verificar conflictos
        if key in self.action_table:
            existing = self.action_table[key]
            if existing.type != action.type or existing.value != action.value:
                conflict = {
                    'state': state_id,
                    'terminal': terminal,
                    'existing': existing,
                    'new': action,
                    'type': self._classify_conflict(existing, action)
                }
                self.conflicts.append(conflict)
                return False
        
        self.action_table[key] = action
        return True
    
    def set_goto(self, state_id, non_terminal, target_state):
        """Establece una transición en la tabla GOTO"""
        self.goto_table[(state_id, non_terminal)] = target_state
    
    def get_action(self, state_id, terminal):
        """Obtiene la acción para un estado y terminal"""
        return self.action_table.get((state_id, terminal), Action(ActionType.ERROR))
    
    def get_goto(self, state_id, non_terminal):
        """Obtiene el estado destino para un estado y no-terminal"""
        return self.goto_table.get((state_id, non_terminal), None)
    
    def _classify_conflict(self, existing, new):
        """Clasifica el tipo de conflicto"""
        if existing.type == ActionType.SHIFT and new.type == ActionType.REDUCE:
            return "shift/reduce"
        elif existing.type == ActionType.REDUCE and new.type == ActionType.SHIFT:
            return "shift/reduce"
        elif existing.type == ActionType.REDUCE and new.type == ActionType.REDUCE:
            return "reduce/reduce"
        else:
            return "unknown"
    
    def has_conflicts(self):
        """Retorna True si hay conflictos en la tabla"""
        return len(self.conflicts) > 0
    
    def print_conflicts(self):
        """Imprime los conflictos encontrados"""
        if not self.conflicts:
            print("No hay conflictos en la tabla SLR(1)")
            return
        
        print(f"\n⚠️  CONFLICTOS ENCONTRADOS: {len(self.conflicts)}")
        for i, conflict in enumerate(self.conflicts, 1):
            print(f"\n{i}. Conflicto {conflict['type']} en Estado {conflict['state']}")
            print(f"   Terminal: {conflict['terminal']}")
            print(f"   Acción existente: {conflict['existing']}")
            print(f"   Nueva acción: {conflict['new']}")
    
    def print_table(self):
        """Imprime la tabla SLR de forma legible"""
        print("\n=== TABLA SLR(1) ===")
        
        # Obtener todos los terminales y no-terminales
        terminals = sorted(self.grammar.tokens) + ['$']
        non_terminals = sorted(self.grammar.non_terminals)
        
        if PANDAS_AVAILABLE:
            # Crear un DataFrame para la tabla ACTION
            action_data = []
            for state_id in range(len(self.automaton.states)):
                row = {'Estado': state_id}
                for terminal in terminals:
                    action = self.get_action(state_id, terminal)
                    if action.type != ActionType.ERROR:
                        row[terminal] = str(action)
                    else:
                        row[terminal] = ''
                action_data.append(row)
            
            # Crear un DataFrame para la tabla GOTO
            goto_data = []
            for state_id in range(len(self.automaton.states)):
                row = {'Estado': state_id}
                for nt in non_terminals:
                    goto_state = self.get_goto(state_id, nt)
                    if goto_state is not None:
                        row[nt] = goto_state
                    else:
                        row[nt] = ''
                goto_data.append(row)
            
            # Crear DataFrames
            action_df = pd.DataFrame(action_data)
            goto_df = pd.DataFrame(goto_data)
            
            # Mostrar tablas
            pd.set_option('display.max_columns', None)  # Mostrar todas las columnas
            pd.set_option('display.width', 1000)  # Ancho amplio para evitar wrapping
            
            print("\nTabla ACTION:")
            print(action_df.set_index('Estado'))
            
            print("\nTabla GOTO:")
            print(goto_df.set_index('Estado'))
        else:
            # Versión original si pandas no está disponible
            # Encabezado
            print(f"{'Estado':<8}", end="")
            for terminal in terminals:
                print(f"{terminal:<8}", end="")
            print("│", end="")
            for nt in non_terminals:
                print(f"{nt:<12}", end="")
            print()
            
            # Separador
            print("─" * (8 + len(terminals) * 8 + 1 + len(non_terminals) * 12))
            
            # Filas de la tabla
            for state_id in range(len(self.automaton.states)):
                print(f"{state_id:<8}", end="")
                
                # Tabla ACTION
                for terminal in terminals:
                    action = self.get_action(state_id, terminal)
                    if action.type != ActionType.ERROR:
                        print(f"{str(action):<8}", end="")
                    else:
                        print(f"{'·':<8}", end="")
                
                print("│", end="")
                
                # Tabla GOTO
                for nt in non_terminals:
                    goto_state = self.get_goto(state_id, nt)
                    if goto_state is not None:
                        print(f"{goto_state:<12}", end="")
                    else:
                        print(f"{'·':<12}", end="")
                print()

def build_slr_table(automaton, follow_sets):
    """
    Construye la tabla SLR(1) a partir del autómata LR(0) y los conjuntos FOLLOW.
    
    Args:
        automaton: LR0Automaton construido
        follow_sets: Diccionario con conjuntos FOLLOW
        
    Returns:
        SLRTable: Tabla SLR(1) construida
    """
    table = SLRTable(automaton, automaton.grammar)
    
    print(f"\nConstruyendo tabla SLR(1) para {len(automaton.states)} estados...")
    
    # Para cada estado en el autómata
    for state in automaton.states:
        state_id = state.id
        
        # 1. Procesar ítems para acciones SHIFT
        for item in state.items:
            if not item.is_complete and item.next_symbol in automaton.grammar.tokens:
                # Ítem A → α•aβ donde a es terminal
                terminal = item.next_symbol
                
                # Ignorar tokens de whitespace (WS)
                if terminal == 'WS':
                    continue
                    
                target_state = state.transitions.get(terminal)
                
                if target_state is not None:
                    action = Action(ActionType.SHIFT, target_state)
                    table.set_action(state_id, terminal, action)
        
        # 2. Procesar ítems completos para acciones REDUCE
        for item in state.items:
            if item.is_complete:
                # Ítem A → α•
                if item.production.number == 0:
                    # S' → S• - acción ACCEPT
                    action = Action(ActionType.ACCEPT)
                    table.set_action(state_id, '$', action)
                else:
                    # A → α• - acción REDUCE
                    left_symbol = item.left
                    if left_symbol in follow_sets:
                        for terminal in follow_sets[left_symbol]:
                            action = Action(ActionType.REDUCE, item.production.number)
                            table.set_action(state_id, terminal, action)
        
        # 3. Procesar transiciones para tabla GOTO
        for symbol, target_state in state.transitions.items():
            if symbol in automaton.grammar.non_terminals:
                table.set_goto(state_id, symbol, target_state)
    
    print(f"Tabla construida con {len(table.action_table)} entradas ACTION y {len(table.goto_table)} entradas GOTO")
    
    # Reportar conflictos
    if table.has_conflicts():
        table.print_conflicts()
    else:
        print("✓ No se encontraron conflictos")
    
    return table

def build_slr_table_for_lr0(states, grammar, follow_sets):
    """
    Construye la tabla SLR(1) a partir de los estados del autómata LR(0) y los conjuntos FOLLOW.
    
    Args:
        states: Lista de estados del autómata LR(0)
        grammar: Gramática utilizada
        follow_sets: Diccionario con conjuntos FOLLOW
        
    Returns:
        SLRTable: Tabla SLR(1) construida
    """
    # Crear un adaptador para la gramática
    class GrammarAdapter:
        def __init__(self, grammar):
            self.grammar = grammar
            self.tokens = grammar.terminals
            self.non_terminals = grammar.non_terminals
    
    # Crear un adaptador para el autómata
    class AutomatonAdapter:
        def __init__(self, states, grammar_adapter):
            self.states = states
            self.grammar = grammar_adapter
    
    # Adaptar la gramática y el autómata
    grammar_adapter = GrammarAdapter(grammar)
    automaton = AutomatonAdapter(states, grammar_adapter)
    
    # Crear la tabla SLR
    table = SLRTable(automaton, grammar_adapter)
    
    print(f"\nConstruyendo tabla SLR(1) para {len(states)} estados...")
    
    # Mapeo de estados por número para facilitar búsquedas
    state_map = {state.number: i for i, state in enumerate(states)}
    
    # Para cada estado en el autómata
    for i, state in enumerate(states):
        state_id = i  # Usar el índice como ID para la tabla SLR
        
        # 1. Procesar ítems para acciones SHIFT
        for item in state.items:
            if not item.is_complete and item.next_symbol in grammar.terminals:
                # Ítem A → α•aβ donde a es terminal
                terminal = item.next_symbol
                
                # Ignorar tokens de whitespace (WS)
                if terminal == 'WS':
                    continue
                    
                target_state_number = state.transitions.get(terminal)
                
                if target_state_number is not None:
                    # Mapear el número de estado a su índice en la lista
                    target_state_id = state_map[target_state_number]
                    action = Action(ActionType.SHIFT, target_state_id)
                    table.set_action(state_id, terminal, action)
        
        # 2. Procesar ítems completos para acciones REDUCE
        for item in state.items:
            if item.is_complete:
                # Ítem A → α•
                if item.production.number == 0:
                    # S' → S• - acción ACCEPT
                    action = Action(ActionType.ACCEPT)
                    table.set_action(state_id, '$', action)
                else:
                    # A → α• - acción REDUCE
                    left_symbol = item.left
                    if left_symbol in follow_sets:
                        for terminal in follow_sets[left_symbol]:
                            action = Action(ActionType.REDUCE, item.production.number)
                            table.set_action(state_id, terminal, action)
        
        # 3. Procesar transiciones para tabla GOTO (excluyendo la gramática aumentada)
        for symbol, target_state_number in state.transitions.items():
            # Solo incluir en GOTO los no terminales (incluyendo los de las reducciones)
            if symbol in grammar.non_terminals:
                # Mapear el número de estado a su índice en la lista
                target_state_id = state_map[target_state_number]
                table.set_goto(state_id, symbol, target_state_id)
                
        # 4. Asegurarse de que hay transiciones GOTO para todos los no terminales relevantes
        # Revisar las producciones para encontrar todos los posibles símbolos no terminales
        for prod in grammar.production_list:
            # Si este estado puede reducir por esta producción
            has_complete_item = any(
                item.is_complete and item.production.number == prod.number
                for item in state.items
            )
            if has_complete_item:
                # Necesitamos asegurar que hay una transición GOTO para el símbolo izquierdo
                left_symbol = prod.left
                
                # Verificamos todos los estados que podrían recibir este no terminal
                for next_state in states:
                    # Si hay algún ítem que espere este no terminal
                    for next_item in next_state.items:
                        if not next_item.is_complete and next_item.next_symbol == left_symbol:
                            # Debe existir una transición GOTO
                            next_state_id = state_map[next_state.number]
                            # Buscar la transición en el automaton
                            for dest_number in state.transitions.values():
                                dest_id = state_map[dest_number]
                                # Si hay transición, añadir a la tabla GOTO
                                if dest_id not in [table.get_goto(state_id, nt) for nt in grammar.non_terminals]:
                                    # Verificar que realmente este estado espera el símbolo
                                    should_add = any(
                                        not i.is_complete and i.next_symbol == left_symbol
                                        for i in states[dest_id].items
                                    )
                                    if should_add:
                                        table.set_goto(state_id, left_symbol, dest_id)
    
    print(f"Tabla construida con {len(table.action_table)} entradas ACTION y {len(table.goto_table)} entradas GOTO")
    
    # Reportar conflictos
    if table.has_conflicts():
        table.print_conflicts()
    else:
        print("[OK] No se encontraron conflictos")
    
    return table

def print_table_ascii(table):
    """Imprime la tabla SLR de forma legible usando solo caracteres ASCII"""
    print("\n=== TABLA SLR(1) ===")
    
    # Obtener todos los terminales y no-terminales (excluyendo el símbolo inicial aumentado para GOTO)
    terminals = sorted(table.grammar.tokens) + ['$']
    
    # Identificar el símbolo inicial aumentado para excluirlo
    augmented_symbol = None
    if hasattr(table.grammar, 'grammar') and hasattr(table.grammar.grammar, 'production_list'):
        # Si es un GrammarAdapter
        if len(table.grammar.grammar.production_list) > 0:
            augmented_prod = table.grammar.grammar.production_list[0]
            augmented_symbol = augmented_prod.left
    
    # Filtrar los no terminales para excluir el símbolo inicial aumentado
    non_terminals = []
    for nt in sorted(table.grammar.non_terminals):
        if nt != augmented_symbol:
            non_terminals.append(nt)
    
    if PANDAS_AVAILABLE:
        # Crear un DataFrame para la tabla ACTION
        action_data = []
        for state_id in range(len(table.automaton.states)):
            row = {'Estado': state_id}
            for terminal in terminals:
                action = table.get_action(state_id, terminal)
                if action.type != ActionType.ERROR:
                    row[terminal] = str(action)
                else:
                    row[terminal] = ''
            action_data.append(row)
        
        # Crear un DataFrame para la tabla GOTO
        goto_data = []
        for state_id in range(len(table.automaton.states)):
            row = {'Estado': state_id}
            for nt in non_terminals:
                goto_state = table.get_goto(state_id, nt)
                if goto_state is not None:
                    row[nt] = goto_state
                else:
                    row[nt] = ''
            goto_data.append(row)
        
        # Crear DataFrames
        action_df = pd.DataFrame(action_data)
        goto_df = pd.DataFrame(goto_data)
        
        # Mostrar tablas
        pd.set_option('display.max_columns', None)  # Mostrar todas las columnas
        pd.set_option('display.width', 1000)  # Ancho amplio para evitar wrapping
        
        print("\nTabla ACTION:")
        print(action_df.set_index('Estado'))
        
        print("\nTabla GOTO:")
        print(goto_df.set_index('Estado'))
    else:
        # Versión original con ASCII si pandas no está disponible
        # Encabezado
        print(f"{'':<8}", end="")
        for terminal in terminals:
            print(f"{terminal:<8}", end="")
        print("|", end="")
        for nt in non_terminals:
            print(f"{nt:<12}", end="")
        print()
        
        # Separador
        print("-" * (8 + len(terminals) * 8 + 1 + len(non_terminals) * 12))
        
        # Filas de la tabla
        for state_id in range(len(table.automaton.states)):
            print(f"{state_id:<8}", end="")
            
            # Tabla ACTION
            for terminal in terminals:
                action = table.get_action(state_id, terminal)
                if action.type != ActionType.ERROR:
                    print(f"{str(action):<8}", end="")
                else:
                    print(f"{'':<8}", end="")
            
            print("|", end="")
            
            # Tabla GOTO
            for nt in non_terminals:
                goto_state = table.get_goto(state_id, nt)
                if goto_state is not None:
                    print(f"{goto_state:<12}", end="")
                else:
                    print(f"{'':<12}", end="")
            print()

class SLRParser:
    """
    Parser SLR(1) que utiliza la tabla para analizar cadenas.
    """
    def __init__(self, table):
        self.table = table
        self.grammar = table.grammar

    def parse(self, tokens):
        """
        Analiza una cadena de tokens usando el algoritmo SLR(1).
        
        Args:
            tokens: Lista de tokens (strings)
            
        Returns:
            tuple: (success: bool, steps: list, error_msg: str)
        """
        # Agregar $ al final si no está
        if not tokens or tokens[-1] != '$':
            tokens = tokens + ['$']
        
        # Inicializar pila y buffer
        stack = [0]  # Pila de estados (comienza con estado 0)
        buffer = tokens[:]  # Buffer de entrada
        steps = []  # Pasos del análisis
        step_num = 0
        
        print(f"\nIniciando análisis SLR(1) de: {' '.join(tokens[:-1])}")
        print(f"{'Paso':<5} {'Pila':<15} {'Entrada':<15} {'Acción'}")
        print("─" * 50)
        
        while True:
            step_num += 1
            current_state = stack[-1]
            current_token = buffer[0] if buffer else '$'
            
            # Obtener acción de la tabla
            action = self.table.get_action(current_state, current_token)
            
            # Formatear estado actual para mostrar
            # Mostrar solo los estados para simplicidad en la visualización
            states_only = [str(stack[i]) for i in range(0, len(stack), 2) if i < len(stack)]
            stack_str = ' '.join(states_only)
            buffer_str = ' '.join(buffer)
            
            print(f"{step_num:<5} {stack_str:<15} {buffer_str:<15} {action}")
            
            step_info = {
                'step': step_num,
                'stack': stack[:],
                'buffer': buffer[:],
                'action': str(action)
            }
            steps.append(step_info)
            
            if action.type == ActionType.SHIFT:
                # Shift: mover token a la pila y cambiar de estado
                # En SLR, la pila alterna: estado, símbolo, estado, símbolo...
                stack.append(current_token)  # Agregar símbolo
                stack.append(action.value)   # Agregar nuevo estado
                buffer.pop(0)
                
            elif action.type == ActionType.REDUCE:
                # Reduce: aplicar producción
                production = self.grammar.production_list[action.value]
                
                # Quitar 2 * len(right) elementos de la pila (símbolo + estado por cada símbolo)
                symbols_to_remove = len(production.right)
                if symbols_to_remove > 0:
                    for _ in range(symbols_to_remove * 2):  # 2 elementos por símbolo
                        if len(stack) > 1:  # Mantener al menos el estado inicial
                            stack.pop()
                
                # Estado actual después de la reducción
                current_state = stack[-1]
                
                # Buscar transición GOTO
                goto_state = self.table.get_goto(current_state, production.left)
                if goto_state is None:
                    error_msg = f"Error: No hay transición GOTO desde estado {current_state} con {production.left}"
                    print(f"\n✗ {error_msg}")
                    return False, steps, error_msg
                
                # Agregar el no-terminal y el nuevo estado
                stack.append(production.left)  # Agregar no-terminal
                stack.append(goto_state)       # Agregar nuevo estado
                print(f"      Reducir por: {production}")
                
            elif action.type == ActionType.ACCEPT:
                # Accept: análisis exitoso
                print(f"\n✓ Cadena aceptada en {step_num} pasos")
                return True, steps, "Análisis exitoso"
                
            elif action.type == ActionType.ERROR:
                # Error: análisis fallido
                error_msg = f"Error de sintaxis en estado {current_state} con token '{current_token}'"
                print(f"\n✗ {error_msg}")
                return False, steps, error_msg
            
            # Prevenir bucles infinitos
            if step_num > 1000:
                error_msg = "Error: Demasiados pasos, posible bucle infinito"
                print(f"\n✗ {error_msg}")
                return False, steps, error_msg
        
        return False, steps, "Error desconocido"

def analyze_slr_grammar(grammar_file, test_strings=None):
    """
    Función principal para analizar una gramática y probar cadenas.
    
    Args:
        grammar_file: Ruta al archivo .yalp
        test_strings: Lista de cadenas a probar (opcional)
        
    Returns:
        tuple: (table, parser, results)
    """
    from yapar_parser import parse_yapar_file, augment_grammar
    from first_follow import analyze_grammar_first_follow
    from lr0_automaton import build_lr0_automaton
    
    # 1. Parsear y aumentar gramática
    print(f"Analizando gramática: {grammar_file}")
    grammar = parse_yapar_file(grammar_file)
    if not grammar:
        print("Error: No se pudo parsear la gramática")
        return None, None, None
    
    augment_grammar(grammar)
    
    # 2. Calcular FIRST y FOLLOW
    first_sets, follow_sets = analyze_grammar_first_follow(grammar)
    
    # 3. Construir autómata LR(0)
    automaton = build_lr0_automaton(grammar)
    
    # 4. Construir tabla SLR(1)
    table = build_slr_table(automaton, follow_sets)
    
    # 5. Crear parser
    parser = SLRParser(table)
    
    # 6. Probar cadenas si se proporcionan
    results = []
    if test_strings:
        print(f"\nProbando {len(test_strings)} cadenas:")
        for i, test_string in enumerate(test_strings, 1):
            print(f"\n--- Prueba {i}: {test_string} ---")
            tokens = test_string.split() if isinstance(test_string, str) else test_string
            success, steps, message = parser.parse(tokens)
            results.append({
                'input': test_string,
                'success': success,
                'steps': len(steps),
                'message': message
            })
    
    return table, parser, results