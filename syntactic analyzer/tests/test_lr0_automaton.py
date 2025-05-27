import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yapar_parser import parse_yapar_file, augment_grammar, Production
from lr0_automaton import Item, State, LR0Automaton, print_item_details, print_state_details

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
    grammar = parse_yapar_file("../resources/slr-1.yalp")
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

def main():
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

if __name__ == "__main__":
    main()