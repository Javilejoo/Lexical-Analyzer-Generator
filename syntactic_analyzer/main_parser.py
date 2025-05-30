import os
import sys
import json
from collections import OrderedDict
import argparse

# Importar componentes necesarios del analizador sintáctico
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from yapar_parser2 import parse_yalp_file, parse_yalp_to_json

# Importar componentes de LR(0)
from lr0_automaton2 import (
    Grammar, Production, Item, State,
    load_grammar_from_json, augment_grammar, create_initial_items,
    closure, goto, build_lr0_automaton, print_items_set, export_to_graphviz
)

# Importar componentes de SLR
from slr_table import ActionType, Action, SLRTable, build_slr_table_for_lr0, print_table_ascii

# Función para calcular conjuntos FIRST
def calculate_first_sets(grammar):
    """Calcula los conjuntos FIRST para todos los símbolos de la gramática."""
    first = {}
    
    # Inicializar conjuntos FIRST vacíos para todos los símbolos
    for symbol in grammar.terminals | grammar.non_terminals:
        first[symbol] = set()
    
    # Regla 1: Si X es terminal, entonces FIRST(X) = {X}
    for terminal in grammar.terminals:
        first[terminal].add(terminal)
    
    # Continuar hasta que no haya más cambios
    while True:
        changes = False
        
        # Para cada producción A -> X1 X2 ... Xn
        for nt, productions in grammar.productions.items():
            for production in productions:
                # Si la producción es vacía (epsilon), añadir epsilon a FIRST(A)
                if not production:
                    if '' not in first[nt]:
                        first[nt].add('')
                        changes = True
                    continue
                
                # Analizar los símbolos de la producción
                k = 0
                add_epsilon = True
                while k < len(production) and add_epsilon:
                    symbol = production[k]
                    add_epsilon = False
                    
                    # Añadir FIRST(Xk) - {epsilon} a FIRST(A)
                    for sym in first.get(symbol, set()):
                        if sym != '' and sym not in first[nt]:
                            first[nt].add(sym)
                            changes = True
                    
                    # Si epsilon está en FIRST(Xk), continuar con el siguiente símbolo
                    if '' in first.get(symbol, set()):
                        add_epsilon = True
                    k += 1
                
                # Si todos los símbolos tienen epsilon en sus FIRST, añadir epsilon a FIRST(A)
                if add_epsilon and '' not in first[nt]:
                    first[nt].add('')
                    changes = True
        
        if not changes:
            break
    
    return first

# Función para calcular conjuntos FOLLOW
def calculate_follow_sets(grammar, first_sets):
    """Calcula los conjuntos FOLLOW para todos los no terminales de la gramática."""
    follow = {nt: set() for nt in grammar.non_terminals}
    
    # Regla 1: Añadir $ al FOLLOW del símbolo inicial
    follow[grammar.start_symbol].add('$')
    
    # Continuar hasta que no haya más cambios
    while True:
        changes = False
        
        # Para cada producción A -> X1 X2 ... Xn
        for nt, productions in grammar.productions.items():
            for production in productions:
                for i, symbol in enumerate(production):
                    # Si el símbolo es no terminal
                    if symbol in grammar.non_terminals:
                        # Si es el último símbolo, añadir FOLLOW(A) a FOLLOW(B)
                        if i == len(production) - 1:
                            for f in follow[nt]:
                                if f not in follow[symbol]:
                                    follow[symbol].add(f)
                                    changes = True
                        else:
                            # Calcular FIRST de la cadena beta = X_i+1 ... X_n
                            beta_first = set()
                            has_epsilon = True
                            for j in range(i + 1, len(production)):
                                next_sym = production[j]
                                # Añadir FIRST(next_sym) - {epsilon} a beta_first
                                for f in first_sets.get(next_sym, set()):
                                    if f != '' and f not in beta_first:
                                        beta_first.add(f)
                                
                                # Comprobar si epsilon está en FIRST(next_sym)
                                if '' not in first_sets.get(next_sym, set()):
                                    has_epsilon = False
                                    break
                            
                            # Añadir beta_first a FOLLOW(B)
                            for f in beta_first:
                                if f not in follow[symbol]:
                                    follow[symbol].add(f)
                                    changes = True
                            
                            # Si epsilon está en FIRST(beta), añadir FOLLOW(A) a FOLLOW(B)
                            if has_epsilon:
                                for f in follow[nt]:
                                    if f not in follow[symbol]:
                                        follow[symbol].add(f)
                                        changes = True
        
        if not changes:
            break
    
    return follow

# Función para mostrar una tabla de conjuntos
def print_sets_table(sets, title):
    """Imprime una tabla formateada para conjuntos FIRST o FOLLOW."""
    print(f"\n{title}:")
    print("=" * 60)
    for symbol, symbols_set in sorted(sets.items()):
        print(f"{symbol:15}: {{{', '.join(sorted(symbols_set))}}}") 

# Función principal
def main():
    # Configurar el parser de argumentos
    parser = argparse.ArgumentParser(description="Analizador sintáctico LR(0) integrado")
    parser.add_argument(
        "yalp_file", 
        nargs="?", 
        help="Archivo YALP con la definición de la gramática"
    )
    args = parser.parse_args()
    
    # Obtener el archivo YALP
    if args.yalp_file:
        yalp_file = args.yalp_file
    else:
        # Archivo de ejemplo por defecto
        yalp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "slr-1.yalp")
        print(f"Usando archivo de gramática por defecto: {yalp_file}")
    
    # Verificar si el archivo existe
    if not os.path.exists(yalp_file):
        print(f"Error: No se encuentra el archivo {yalp_file}")
        sys.exit(1)
    
    # Directorio para guardar el JSON generado
    resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
    os.makedirs(resources_dir, exist_ok=True)
    
    # Nombre del archivo JSON basado en el nombre del archivo YALP
    base_name = os.path.basename(yalp_file)
    file_name_without_ext = os.path.splitext(base_name)[0]
    json_file = os.path.join(resources_dir, f"{file_name_without_ext}.json")
    
    # Generar el JSON usando yapar_parser2
    print(f"\nGenerando JSON a partir de {yalp_file}...")
    grammar_obj = parse_yalp_file(yalp_file)
    json_content = parse_yalp_to_json(yalp_file, json_file)
    print(f"JSON generado en: {json_file}")
    
    # Cargar la gramática desde el JSON generado
    grammar = load_grammar_from_json(json_file)
    
    if not grammar:
        print("Error al cargar la gramática")
        sys.exit(1)
    
    # Mostrar tokens (terminales) de la gramática
    print("\n" + "=" * 80)
    print("TOKENS (TERMINALES)")
    print("=" * 80)
    print("Tokens:", ", ".join(sorted(grammar.terminals)))
    
    # Calcular y mostrar conjuntos FIRST
    first_sets = calculate_first_sets(grammar)
    print_sets_table(first_sets, "\n" + "=" * 80 + "\nCONJUNTOS FIRST" + "\n" + "=" * 80)
    
    # Calcular y mostrar conjuntos FOLLOW
    follow_sets = calculate_follow_sets(grammar, first_sets)
    print_sets_table(follow_sets, "\n" + "=" * 80 + "\nCONJUNTOS FOLLOW" + "\n" + "=" * 80)
    
    # Aumentar la gramática
    print("\n" + "=" * 80)
    print("GRAMÁTICA AUMENTADA")
    print("=" * 80)
    augment_grammar(grammar)
    
    # Crear los items iniciales
    initial_items = create_initial_items(grammar)
    
    # Mostrar los items iniciales antes de aplicar el cierre
    print("\n" + "=" * 80)
    print("ITEMS INICIALES (Antes del cierre)")
    print("=" * 80)
    print_items_set(initial_items, title="Items iniciales")
    
    # Construir el autómata LR(0) completo
    print("\n" + "=" * 80)
    print("CONSTRUYENDO AUTÓMATA LR(0)")
    print("=" * 80)
    
    states = build_lr0_automaton(grammar)
    
    # Generar visualización gráfica del autómata
    automaton_filename = os.path.join(resources_dir, f"{file_name_without_ext}_automaton")
    export_to_graphviz(states, filename=automaton_filename)
    
    # Mostrar cada estado con sus items
    print("\n" + "=" * 80)
    print(f"ESTADOS DEL AUTÓMATA LR(0) (Total: {len(states)} estados)")
    print("=" * 80)
    
    # Imprimir cada estado con sus items
    for state in states:
        print_items_set(state.items, title=f"ESTADO {state.number}")
        print("\n" + "-" * 60 + "\n")
    
    # Mostrar la tabla de transiciones
    print("\n" + "=" * 80)
    print("TABLA DE TRANSICIONES")
    print("=" * 80)
    print("Transiciones:")
    
    # Ordenar todos los símbolos (terminales y no terminales) para una presentación consistente
    all_symbols = sorted(grammar.terminals) + sorted(grammar.non_terminals)
    
    # Para cada estado, mostrar sus transiciones, usando 'd' en lugar de delta para evitar problemas de codificación
    for state in states:
        for symbol in all_symbols:
            if symbol in state.transitions:
                target_state = state.transitions[symbol]
                if symbol in grammar.terminals:
                    print(f"d(q{state.number}, '{symbol}') --> q{target_state}")
                else:
                    print(f"d(q{state.number}, {symbol}) --> q{target_state}")

    
    # Identificar estados de aceptación (aquellos con ítems completos donde la producción es la inicial)
    print("\n" + "=" * 80)
    print("ESTADO DE ACEPTACIÓN Y PRODUCCIÓN AUMENTADA")
    print("=" * 80)
    
    # Estado de aceptación
    accept_states = []
    for state in states:
        for item in state.items:
            # Si es un ítem completo y su producción es la inicial aumentada (0)
            if item.is_complete and item.production.number == 0:
                accept_states.append(state.number)
                break
    
    if accept_states:
        print(f"Estado de aceptación: q{accept_states[0]}")
    else:
        print("No se encontró estado de aceptación")
        
    # Mostrar producción aumentada
    if grammar.production_list and len(grammar.production_list) > 0:
        initial_production = grammar.production_list[0]
        print(f"Producción aumentada: {initial_production}")
        
        # Mostrar los ítems iniciales relacionados con la producción aumentada
        for item in initial_items:
            print(f"Item inicial: {item}")
    
    # Informar sobre la imagen del autómata generada
    print("\n" + "=" * 80)
    print("VISUALIZACIÓN DEL AUTÓMATA LR(0)")
    print("=" * 80)
    print(f"La imagen del autómata LR(0) se ha generado en: {automaton_filename}.png")
    
    # Construir y mostrar la tabla SLR
    print("\n" + "=" * 80)
    print("TABLA SLR(1)")
    print("=" * 80)
    
    # Usar nuestra implementación personalizada para construir la tabla SLR
    slr_table = build_slr_table_for_lr0(states, grammar, follow_sets)
    # Usar nuestra función personalizada para imprimir la tabla sin caracteres Unicode
    print_table_ascii(slr_table)

if __name__ == "__main__":
    main()