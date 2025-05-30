import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yapar_parser2 import parse_yalp_file
from lr0_automaton import (Item, State, LR0Automaton, print_item_details, print_state_details,
                          closure, goto, build_lr0_automaton, analyze_automaton, print_closure_steps,export_automaton_to_dot)

from collections import OrderedDict

# Crear una clase Production compatible con la versión anterior
class Production:
    def __init__(self, left, right, number):
        self.left = left    # Lado izquierdo (no-terminal)
        self.right = right  # Lado derecho (lista de símbolos)
        self.number = number  # Número de producción
    
    def __repr__(self):
        return f"{self.number}: {self.left} -> {' '.join(self.right)}"

# Función para convertir gramática de yapar_parser2 al formato esperado por LR0Automaton
def convert_grammar(grammar):
    result = type('Grammar', (), {})()
    result.tokens = list(grammar.terminals)
    result.non_terminals = list(grammar.non_terminals)
    result.productions = OrderedDict()
    result.start_symbol = grammar.start_symbol
    result.ignored_tokens = list(grammar.ignored_tokens)
    result.production_list = []
    
    # Convertir producciones
    number = 0
    for non_terminal, rules in grammar.productions.items():
        result.productions[non_terminal] = rules
        for rule in rules:
            prod = Production(non_terminal, rule, number)
            result.production_list.append(prod)
            number += 1
    
    return result

# Función para aumentar la gramática
def augment_grammar(grammar):
    """Aumenta la gramática agregando S' -> S para el análisis SLR"""
    if not grammar or not grammar.start_symbol:
        return
    
    # Crear nuevo símbolo inicial
    new_start = grammar.start_symbol + "'"
    
    # Agregar nueva producción al inicio
    grammar.productions[new_start] = [[grammar.start_symbol]]
    
    # Mover a la primera posición en el OrderedDict
    new_productions = OrderedDict()
    new_productions[new_start] = grammar.productions[new_start]
    for key, value in grammar.productions.items():
        if key != new_start:
            new_productions[key] = value
    grammar.productions = new_productions
    
    # Actualizar listas
    grammar.non_terminals.insert(0, new_start)
    grammar.start_symbol = new_start
    
    # Recrear lista de producciones numeradas
    grammar.production_list = []
    number = 0
    for non_terminal, rules in grammar.productions.items():
        for rule in rules:
            prod = Production(non_terminal, rule, number)
            grammar.production_list.append(prod)
            number += 1
    
    print(f"\nGramática aumentada con: {new_start} -> {grammar.production_list[0].right[0]}")

# Función para visualizar el autómata LR(0)
def visualize_lr0_automaton(automaton):
    print("\n=== Autómata LR(0) ===")
    
    for state_id, state in automaton.states.items():
        print(f"\nEstado {state_id}:")
        print_state_details(state)
        
        for symbol, next_state_id in state.transitions.items():
            print(f"  {symbol} -> Estado {next_state_id}")

def test_item_creation():
    """Prueba la creación y manipulación de ítems LR(0)"""
    print("\n=== TEST: Creación de Ítems ===")
    
    # Crear una producción de prueba
    prod = Production("E", ["E", "+", "T"], 0)
    
    # Crear ítems en diferentes posiciones
    item0 = Item(prod, 0)  # E → • E + T
    item1 = Item(prod, 1)  # E → E • + T
    item2 = Item(prod, 2)  # E → E + • T
    item3 = Item(prod, 3)  # E → E + T •
    
    items = [item0, item1, item2, item3]
    
    for item in items:
        print(f"\n{item}")
        print(f"  Siguiente símbolo: {item.next_symbol}")
        print(f"  ¿Completo?: {item.is_complete}")
        print(f"  ¿Kernel?: {item.is_kernel}")
    
    # Probar avance de ítem
    print("\n--- Probando avance de ítem ---")
    current = item0
    while not current.is_complete:
        print(f"{current}")
        current = current.advance()
    print(f"{current} (completo)")
    
    return True

def test_state_creation():
    """Prueba la creación y manipulación de estados"""
    print("\n=== TEST: Creación de Estados ===")
    
    # Crear producciones de prueba
    prod1 = Production("E'", ["E"], 0)
    prod2 = Production("E", ["E", "+", "T"], 1)
    prod3 = Production("E", ["T"], 2)
    
    # Crear ítems
    item1 = Item(prod1, 0)  # E' → • E
    item2 = Item(prod2, 0)  # E → • E + T
    item3 = Item(prod3, 0)  # E → • T
    
    # Crear estado
    items = {item1, item2, item3}
    state = State(items, 0)
    
    print(state)
    print(f"\nÍtems kernel: {len(state.kernel_items)}")
    for item in state.kernel_items:
        print(f"  {item}")
    
    print(f"\nSímbolos después del punto: {state.get_symbols_after_dot()}")
    
    # Agregar transiciones
    state.add_transition("E", 1)
    state.add_transition("T", 2)
    
    print(f"\nTransiciones: {state.transitions}")
    
    return True

def test_with_real_grammar():
    """Prueba las estructuras con una gramática real"""
    print("\n=== TEST: Gramática Real (slr-1.yalp) ===")
    
    # Parsear gramática
    grammar = parse_yalp_file("../resources/slr-1.yalp")
    if not grammar:
        print("Error: No se pudo parsear la gramática")
        return False
    
    # Aumentar gramática
    augment_grammar(grammar)
    
    # Crear autómata vacío
    automaton = LR0Automaton(grammar)
    
    print(f"\nGramática cargada:")
    print(f"  Símbolo inicial: {grammar.start_symbol}")
    print(f"  Producciones: {len(grammar.production_list)}")
    
    # Crear el ítem inicial
    initial_production = grammar.production_list[0]  # S' → S
    initial_item = Item(initial_production, 0)      # S' → • S
    
    print(f"\nÍtem inicial: {initial_item}")
    print_item_details(initial_item)
    
    # Crear estado inicial
    initial_items = {initial_item}
    state_id = automaton.add_state(initial_items)
    automaton.initial_state_id = state_id
    
    print(f"\nEstado inicial creado con ID: {state_id}")
    print_state_details(automaton.get_state(state_id))
    
    # Simular algunas transiciones
    print("\n--- Simulando transiciones ---")
    
    # Crear algunos ítems más para otro estado
    if len(grammar.production_list) > 1:
        prod = grammar.production_list[1]
        new_item = Item(prod, 1)  # Avanzar el punto
        new_state_id = automaton.add_state({new_item})
        
        # Agregar transición
        automaton.add_transition(state_id, grammar.start_symbol.replace("'", ""), new_state_id)
        
        print(f"Nueva transición: Estado {state_id} --{grammar.start_symbol.replace("'", "")}--> Estado {new_state_id}")
    
    # Imprimir autómata
    automaton.print_automaton()
    
    return True

def test_item_equality():
    """Prueba la igualdad y hash de ítems"""
    print("\n=== TEST: Igualdad de Ítems ===")
    
    prod1 = Production("E", ["E", "+", "T"], 0)
    prod2 = Production("E", ["E", "+", "T"], 0)  # Misma producción
    prod3 = Production("E", ["T"], 1)  # Diferente producción
    
    item1 = Item(prod1, 1)
    item2 = Item(prod2, 1)  # Debería ser igual a item1
    item3 = Item(prod1, 2)  # Diferente posición
    item4 = Item(prod3, 0)  # Diferente producción
    
    print(f"item1: {item1}")
    print(f"item2: {item2}")
    print(f"item3: {item3}")
    print(f"item4: {item4}")
    
    print(f"\nitem1 == item2: {item1 == item2} (esperado: True)")
    print(f"item1 == item3: {item1 == item3} (esperado: False)")
    print(f"item1 == item4: {item1 == item4} (esperado: False)")
    
    # Probar en un conjunto
    items_set = {item1, item2, item3, item4}
    print(f"\nÍtems únicos en conjunto: {len(items_set)} (esperado: 3)")
    
    return True

def test_closure_simple():
    """Prueba la función CLOSURE con un ejemplo simple"""
    print("\n=== TEST: CLOSURE Simple ===")
    
    # Crear una gramática simple
    from yapar_parser import Grammar, Production
    grammar = Grammar()
    
    # E' → E
    # E → E + T | T
    # T → id
    prod0 = Production("E'", ["E"], 0)
    prod1 = Production("E", ["E", "+", "T"], 1)
    prod2 = Production("E", ["T"], 2)
    prod3 = Production("T", ["id"], 3)
    
    grammar.productions = {
        "E'": [["E"]],
        "E": [["E", "+", "T"], ["T"]],
        "T": [["id"]]
    }
    grammar.production_list = [prod0, prod1, prod2, prod3]
    grammar.non_terminals = ["E'", "E", "T"]
    grammar.tokens = ["id", "+"]
    
    # Crear ítem inicial E' → •E
    initial_item = Item(prod0, 0)
    
    # Calcular closure
    print(f"Ítem inicial: {initial_item}")
    closure_items = closure({initial_item}, grammar)
    
    print(f"\nCLOSURE contiene {len(closure_items)} ítems:")
    for item in sorted(closure_items, key=str):
        print(f"  {item}")
    
    # Verificar que se agregaron los ítems esperados
    expected_items = [
        "E' → • E",
        "E → • E + T",
        "E → • T",
        "T → • id"
    ]
    
    actual_items = [str(item) for item in closure_items]
    
    print("\nVerificación:")
    all_found = True
    for expected in expected_items:
        found = any(expected in actual for actual in actual_items)
        print(f"  {expected}: {'✓' if found else '✗'}")
        if not found:
            all_found = False
    
    return all_found

def test_goto_function():
    """Prueba la función GOTO"""
    print("\n=== TEST: Función GOTO ===")
    
    # Usar la misma gramática simple
    from yapar_parser import Grammar, Production
    grammar = Grammar()
    
    # E → E + T | T
    # T → T * F | F
    # F → id
    prod0 = Production("E", ["E", "+", "T"], 0)
    prod1 = Production("E", ["T"], 1)
    prod2 = Production("T", ["T", "*", "F"], 2)
    prod3 = Production("T", ["F"], 3)
    prod4 = Production("F", ["id"], 4)
    
    grammar.productions = {
        "E": [["E", "+", "T"], ["T"]],
        "T": [["T", "*", "F"], ["F"]],
        "F": [["id"]]
    }
    grammar.production_list = [prod0, prod1, prod2, prod3, prod4]
    grammar.non_terminals = ["E", "T", "F"]
    grammar.tokens = ["id", "+", "*"]
    
    # Crear estado inicial con algunos ítems
    items = {
        Item(prod0, 0),  # E → • E + T
        Item(prod1, 0),  # E → • T
        Item(prod2, 0),  # T → • T * F
        Item(prod3, 0),  # T → • F
        Item(prod4, 0)   # F → • id
    }
    
    # Calcular closure del estado inicial
    initial_state = closure(items, grammar)
    
    print("Estado inicial:")
    for item in sorted(initial_state, key=str):
        print(f"  {item}")
    
    # Probar GOTO con diferentes símbolos
    symbols_to_test = ["E", "T", "F", "id"]
    
    for symbol in symbols_to_test:
        goto_result = goto(initial_state, symbol, grammar)
        print(f"\nGOTO(I0, {symbol}):")
        if goto_result:
            for item in sorted(goto_result, key=str):
                print(f"  {item}")
        else:
            print("  (vacío)")
    
    return True

def test_build_automaton_slr1():
    """Prueba la construcción completa del autómata con slr-1.yalp"""
    print("\n=== TEST: Construcción de Autómata (slr-1.yalp) ===")
    
    # Parsear y aumentar la gramática
    grammar = parse_yalp_file("../resources/slr-1.yalp")
    if not grammar:
        print("Error: No se pudo parsear slr-1.yalp")
        return False
    
    augment_grammar(grammar)
    
    print(f"Gramática: {len(grammar.production_list)} producciones")
    for prod in grammar.production_list:
        print(f"  {prod}")
    
    # Construir el autómata
    automaton = build_lr0_automaton(grammar)
    
    # Mostrar estadísticas
    stats = analyze_automaton(automaton)
    
    print(f"\nEstadísticas del autómata:")
    print(f"  Estados: {stats['num_states']}")
    print(f"  Transiciones: {stats['num_transitions']}")
    print(f"  Terminales usados: {stats['terminals_used']}")
    print(f"  No-terminales usados: {stats['non_terminals_used']}")
    print(f"  Estados shift: {stats['shift_states']}")
    print(f"  Estados reduce: {stats['reduce_states']}")
    print(f"  Estados shift/reduce: {stats['shift_reduce_states']}")
    
    # Mostrar algunos estados
    print("\nPrimeros 3 estados:")
    for i in range(min(3, len(automaton.states))):
        state = automaton.states[i]
        print(f"\nEstado {i}:")
        for item in sorted(state.items, key=str):
            print(f"  {item}")
        if state.transitions:
            print("  Transiciones:")
            for symbol, target in sorted(state.transitions.items()):
                print(f"    {symbol} → Estado {target}")
    
    return True

def test_closure_with_details():
    """Prueba CLOSURE mostrando los pasos detallados"""
    print("\n=== TEST: CLOSURE con Detalles ===")
    
    # Crear una gramática simple para ver los pasos
    from yapar_parser import Grammar, Production
    grammar = Grammar()
    
    # S → A B
    # A → a A | ε
    # B → b
    prod0 = Production("S", ["A", "B"], 0)
    prod1 = Production("A", ["a", "A"], 1)
    prod2 = Production("A", [], 2)  # A → ε
    prod3 = Production("B", ["b"], 3)
    
    grammar.productions = {
        "S": [["A", "B"]],
        "A": [["a", "A"], []],
        "B": [["b"]]
    }
    grammar.production_list = [prod0, prod1, prod2, prod3]
    grammar.non_terminals = ["S", "A", "B"]
    grammar.tokens = ["a", "b"]
    
    # Crear ítem inicial S → •A B
    initial_item = Item(prod0, 0)
    
    # Mostrar los pasos del closure
    closure_result = print_closure_steps({initial_item}, grammar)
    
    print(f"\nResultado final: {len(closure_result)} ítems")
    
    return True

def test_multiple_grammars():
    """Prueba con múltiples gramáticas SLR"""
    print("\n=== TEST: Múltiples Gramáticas ===")
    
    test_files = ['slr-1.yalp', 'slr-2.yalp', 'slr-3.yalp']
    results = []
    
    for filename in test_files:
        print(f"\n--- Probando {filename} ---")
        
        try:
            # Parsear y aumentar
            grammar = parse_yalp_file(f"../resources/{filename}")
            if not grammar:
                print(f"Error: No se pudo parsear {filename}")
                results.append((filename, False, "Parse error"))
                continue
            
            augment_grammar(grammar)
            
            # Construir autómata
            automaton = build_lr0_automaton(grammar)
            
            # Analizar
            stats = analyze_automaton(automaton)
            
            print(f"✓ Autómata construido: {stats['num_states']} estados, {stats['num_transitions']} transiciones")
            
            # Verificar que tiene al menos el estado inicial
            if automaton.initial_state_id is not None and len(automaton.states) > 0:
                results.append((filename, True, stats))
            else:
                results.append((filename, False, "No initial state"))
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            results.append((filename, False, str(e)))
    
    # Resumen
    print("\n--- Resumen ---")
    for filename, success, info in results:
        if success:
            print(f"✓ {filename}: {info['num_states']} estados")
        else:
            print(f"✗ {filename}: {info}")
    
    return all(success for _, success, _ in results)

def test_state_details():
    """Muestra detalles de estados específicos"""
    print("\n=== TEST: Detalles de Estados ===")
    
    # Usar una gramática simple
    grammar = parse_yalp_file("../resources/slr-1.yalp")
    if not grammar:
        return False
    
    augment_grammar(grammar)
    automaton = build_lr0_automaton(grammar)
    
    # Mostrar el estado que tiene reduce (generalmente uno de los últimos)
    print("\nBuscando estados con ítems completos (reduce)...")
    
    for state in automaton.states:
        complete_items = [item for item in state.items if item.is_complete]
        if complete_items:
            print(f"\nEstado {state.id} (tiene {len(complete_items)} ítems completos):")
            print("  Ítems completos:")
            for item in complete_items:
                print(f"    {item} [Reduce por producción #{item.production.number}]")
            
            print("  Todos los ítems del estado:")
            for item in sorted(state.items, key=str):
                marker = " [COMPLETO]" if item.is_complete else ""
                print(f"    {item}{marker}")
            
            break
    
    return True

def main_simple():
    """Función principal de pruebas"""
    print("PRUEBAS DE ESTRUCTURAS LR(0)")
    print("="*50)
    
    tests = [
        ("Creación de Ítems", test_item_creation),
        ("Creación de Estados", test_state_creation),
        ("Igualdad de Ítems", test_item_equality),
        ("Gramática Real", test_with_real_grammar)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\nEjecutando: {test_name}")
            success = test_func()
            results.append((test_name, success))
            print(f"\n{'✓' if success else '✗'} {test_name}: {'PASÓ' if success else 'FALLÓ'}")
        except Exception as e:
            print(f"\n✗ {test_name}: ERROR - {str(e)}")
            results.append((test_name, False))
            import traceback
            traceback.print_exc()
    
    # Resumen
    print("\n" + "="*50)
    print("RESUMEN DE PRUEBAS")
    print("="*50)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASÓ" if success else "✗ FALLÓ"
        print(f"{test_name:<30} {status}")
    
    print(f"\nTotal: {passed}/{total} pruebas pasaron")


def main_complex():
    """Función principal"""
    print("PRUEBAS DEL CONSTRUCTOR LR(0)")
    print("="*60)
    
    tests = [
        ("CLOSURE Simple", test_closure_simple),
        ("Función GOTO", test_goto_function),
        ("CLOSURE con Detalles", test_closure_with_details),
        ("Construcción Autómata SLR-1", test_build_automaton_slr1),
        ("Detalles de Estados", test_state_details),
        ("Múltiples Gramáticas", test_multiple_grammars)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Ejecutando: {test_name}")
        print('='*60)
        
        try:
            success = test_func()
            results.append((test_name, success))
            print(f"\n{'✓' if success else '✗'} {test_name}: {'PASÓ' if success else 'FALLÓ'}")
        except Exception as e:
            print(f"\n✗ {test_name}: ERROR - {str(e)}")
            results.append((test_name, False))
            import traceback
            traceback.print_exc()
    
    # Resumen final
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✓ PASÓ" if success else "✗ FALLÓ"
        print(f"{test_name:<35} {status}")
    

def test_visualize_automaton():
    """Muestra los Items LR(0), los estados y las transiciones del autómata en el formato solicitado"""
    print("\n" + "="*80)
    print("VISUALIZACIÓN DEL AUTÓMATA LR(0)")
    print("="*80)
    
    # Parsear gramática y crear autómata
    grammar_file = "../resources/slr-1.yalp"  # Puedes cambiar a otra gramática si lo deseas
    grammar_obj = parse_yalp_file(grammar_file)
    if not grammar_obj:
        print(f"Error: No se pudo parsear la gramática {grammar_file}")
        return False
    
    # Convertir y aumentar la gramática
    grammar = convert_grammar(grammar_obj)
    augment_grammar(grammar)
    
    # Construir el autómata LR(0)
    automaton = build_lr0_automaton(grammar)
    
    # Mostrar información detallada de los items
    print("\n" + "="*80)
    print("ITEMS LR(0)")
    print("="*80)
    
    all_items = set()
    for state in automaton.states:
        all_items.update(state.items)
    
    for item in sorted(all_items, key=str):
        print(item)
    
    # Mostrar información detallada de los estados
    print("\n" + "="*80)
    print("ESTADOS LR(0)")
    print("="*80)
    
    for state in automaton.states:
        print(f"\nESTADO {state.id}:")
        for item in sorted(state.items, key=str):
            print(f"  {item}")
    
    # Mostrar transiciones
    print("\n" + "="*80)
    print("TRANSICIONES (GOTO)")
    print("="*80)
    
    for state in automaton.states:
        for symbol, target in sorted(state.transitions.items()):
            print(f"delta (q{state.id}, '{symbol}') --> q{target}")
    
    return True

def visualize_lr0_automaton_with_graphviz():
    """Visualiza el autómata LR(0) usando Graphviz con alta calidad"""
    try:
        import graphviz
    except ImportError:
        print("Error: La biblioteca 'graphviz' no está instalada.")
        print("Instale con: pip install graphviz")
        return False
    
    print("\n" + "="*80)
    print("VISUALIZACIÓN GRÁFICA DEL AUTÓMATA LR(0) CON GRAPHVIZ (ALTA CALIDAD)")
    print("="*80)
    
    # Parsear gramática y crear autómata
    grammar_file = "../resources/slr-1.yalp"  # Puedes cambiar a otra gramática si lo deseas
    grammar_obj = parse_yalp_file(grammar_file)
    if not grammar_obj:
        print(f"Error: No se pudo parsear la gramática {grammar_file}")
        return False
    
    # Convertir y aumentar la gramática
    grammar = convert_grammar(grammar_obj)
    augment_grammar(grammar)
    
    # Construir el autómata LR(0)
    automaton = build_lr0_automaton(grammar)
    
    # Crear un grafo dirigido con Graphviz
    dot = graphviz.Digraph('LR0_Automaton', comment='Autómata LR(0)', format='png')
    
    # Configurar atributos del grafo para alta calidad
    dot.attr(rankdir='LR')
    dot.attr('graph', dpi='300', size='12,8')
    dot.attr('node', shape='box', style='rounded,filled', fillcolor='white', fontname='Arial', fontsize='10')
    dot.attr('edge', fontname='Arial', fontsize='9')
    
    # Agregar nodos (estados)
    for state in automaton.states:
        # Crear etiqueta para el nodo con los ítems del estado
        if state.id == automaton.initial_state_id:
            label = f"Estado {state.id} (Inicial)\n\n"
        else:
            label = f"Estado {state.id}\n\n"
        
        # Agrupar los ítems por símbolo no terminal (lado izquierdo)
        items_by_nt = {}
        for item in sorted(state.items, key=str):
            nt = item.left
            if nt not in items_by_nt:
                items_by_nt[nt] = []
            items_by_nt[nt].append(str(item))
        
        # Agregar ítems agrupados por no terminal a la etiqueta
        for nt, items_list in sorted(items_by_nt.items()):
            label += f"{nt}:\n"
            for item in items_list:
                label += f"  {item}\n"
            label += "\n"
        
        # Eliminar el último salto de línea extra
        if label.endswith("\n\n"):
            label = label[:-1]
        
        # Estilo del nodo
        node_attrs = {
            'label': label.strip()
        }
        
        # Resaltar el estado inicial
        if state.id == automaton.initial_state_id:
            node_attrs['style'] = 'filled'
            node_attrs['fillcolor'] = 'lightblue'
        
        
        # Agregar el nodo al grafo
        dot.node(f'q{state.id}', **node_attrs)
    
    # Agregar aristas (transiciones)
    for state in automaton.states:
        for symbol, target in sorted(state.transitions.items()):
            # Estilo especial para terminales y no terminales
            edge_attrs = {}
            if symbol in grammar.tokens:
                edge_attrs['color'] = 'blue'
                edge_attrs['fontcolor'] = 'blue'
                edge_attrs['label'] = f"'{symbol}'"
            else:
                edge_attrs['color'] = 'darkgreen'
                edge_attrs['fontcolor'] = 'darkgreen'
                edge_attrs['label'] = symbol
                
            dot.edge(f'q{state.id}', f'q{target}', **edge_attrs)
    
    # Guardar y renderizar el grafo con alta calidad
    output_file = "lr0_automaton_hq"
    dot.render(output_file, format='png', cleanup=True)
    
    print(f"\nGrafo del autómata LR(0) en alta calidad generado como: {output_file}.png")
    
    return True

if __name__ == "__main__":
    # Ejecutar el visualizador de autómata con representación textual
    test_visualize_automaton()
    
    # Ejecutar el visualizador con Graphviz
    visualize_lr0_automaton_with_graphviz()
    
    # Comentar o descomentar según lo que quieras probar
    # main_simple()
    # success = main_complex()
    # sys.exit(0 if success else 1)