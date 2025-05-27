#!/usr/bin/env python3
"""
Script de prueba para la tabla SLR(1) y el parser sintáctico.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from slr_table import analyze_slr_grammar, build_slr_table, SLRParser
from yapar_parser import parse_yapar_file, augment_grammar
from first_follow import analyze_grammar_first_follow
from lr0_automaton import build_lr0_automaton

def test_slr_table_construction():
    """Prueba la construcción de la tabla SLR(1)"""
    print("\n=== TEST: Construcción de Tabla SLR(1) ===")
    
    # Usar slr-1.yalp como ejemplo
    grammar = parse_yapar_file("../resources/slr-1.yalp")
    if not grammar:
        print("Error: No se pudo parsear slr-1.yalp")
        return False
    
    augment_grammar(grammar)
    
    # Calcular FIRST y FOLLOW
    first_sets, follow_sets = analyze_grammar_first_follow(grammar)
    
    # Construir autómata
    automaton = build_lr0_automaton(grammar)
    
    # Construir tabla
    table = build_slr_table(automaton, follow_sets)
    
    # Verificar que la tabla se construyó
    print(f"\nTabla construida:")
    print(f"  Entradas ACTION: {len(table.action_table)}")
    print(f"  Entradas GOTO: {len(table.goto_table)}")
    print(f"  Conflictos: {len(table.conflicts)}")
    
    # Mostrar algunas entradas de ejemplo
    print(f"\nAlgunas entradas ACTION:")
    count = 0
    for (state, terminal), action in table.action_table.items():
        if count < 5:
            print(f"  Estado {state}, '{terminal}' → {action}")
            count += 1
    
    print(f"\nAlgunas entradas GOTO:")
    count = 0
    for (state, nt), target in table.goto_table.items():
        if count < 5:
            print(f"  Estado {state}, '{nt}' → Estado {target}")
            count += 1
    
    return len(table.action_table) > 0

def test_simple_parsing():
    """Prueba el parsing de cadenas simples"""
    print("\n=== TEST: Parsing Simple ===")
    
    # Construir tabla para slr-1.yalp
    table, parser, _ = analyze_slr_grammar("../resources/slr-1.yalp")
    
    if not table or not parser:
        print("Error: No se pudo construir la tabla o parser")
        return False
    
    # Cadenas de prueba para la gramática de expresiones
    test_cases = [
        # Casos válidos
        (["ID"], True, "Expresión simple"),
        (["ID", "+", "ID"], True, "Suma simple"),
        (["ID", "*", "ID"], True, "Multiplicación simple"),
        (["(", "ID", ")"], True, "Expresión entre paréntesis"),
        (["ID", "+", "ID", "*", "ID"], True, "Expresión con precedencia"),
        
        # Casos inválidos
        (["+", "ID"], False, "Comienza con operador"),
        (["ID", "+"], False, "Termina con operador"),
        (["(", "ID"], False, "Paréntesis sin cerrar"),
        (["ID", ")", "("], False, "Paréntesis mal balanceados"),
    ]
    
    results = []
    
    for tokens, expected, description in test_cases:
        print(f"\n--- {description}: {' '.join(tokens)} ---")
        success, steps, message = parser.parse(tokens[:])
        
        result = {
            'tokens': tokens,
            'expected': expected,
            'actual': success,
            'correct': success == expected,
            'steps': len(steps),
            'description': description
        }
        results.append(result)
        
        status = "✓" if result['correct'] else "✗"
        print(f"{status} Esperado: {expected}, Obtenido: {success}")
    
    # Resumen
    correct = sum(1 for r in results if r['correct'])
    total = len(results)
    print(f"\nResultados: {correct}/{total} casos correctos")
    
    return correct == total

def test_table_display():
    """Prueba la visualización de la tabla"""
    print("\n=== TEST: Visualización de Tabla ===")
    
    # Construir tabla
    table, parser, _ = analyze_slr_grammar("../resources/slr-1.yalp")
    
    if not table:
        print("Error: No se pudo construir la tabla")
        return False
    
    # Mostrar la tabla
    table.print_table()
    
    # Mostrar conflictos si los hay
    table.print_conflicts()
    
    return True

def test_multiple_grammars():
    """Prueba con múltiples gramáticas"""
    print("\n=== TEST: Múltiples Gramáticas ===")
    
    grammars = [
        ("slr-1.yalp", [["ID"], ["ID", "+", "ID"]]),
        ("slr-2.yalp", [["NUMBER"], ["ID", "+", "NUMBER"]]),
        ("slr-3.yalp", [["NUMBER"], ["NUMBER", "+", "NUMBER"]])
    ]
    
    results = []
    
    for grammar_file, test_strings in grammars:
        print(f"\n--- Probando {grammar_file} ---")
        
        try:
            table, parser, _ = analyze_slr_grammar(f"../resources/{grammar_file}")
            
            if table and parser:
                # Probar una cadena simple
                success, steps, message = parser.parse(test_strings[0][:])
                
                results.append({
                    'grammar': grammar_file,
                    'success': True,
                    'conflicts': len(table.conflicts),
                    'parse_success': success
                })
                
                print(f"✓ Tabla construida, {len(table.conflicts)} conflictos")
                print(f"✓ Parsing de {test_strings[0]}: {success}")
            else:
                results.append({
                    'grammar': grammar_file,
                    'success': False,
                    'conflicts': 0,
                    'parse_success': False
                })
                print(f"✗ Error construyendo tabla")
                
        except Exception as e:
            print(f"✗ Error: {str(e)}")
            results.append({
                'grammar': grammar_file,
                'success': False,
                'conflicts': 0,
                'parse_success': False
            })
    
    # Resumen
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    print(f"\nGramáticas procesadas exitosamente: {successful}/{total}")
    
    return successful > 0

def test_error_handling():
    """Prueba el manejo de errores"""
    print("\n=== TEST: Manejo de Errores ===")
    
    table, parser, _ = analyze_slr_grammar("../resources/slr-1.yalp")
    
    if not table or not parser:
        print("Error: No se pudo construir tabla/parser")
        return False
    
    # Casos de error
    error_cases = [
        [],  # Cadena vacía
        ["INVALID_TOKEN"],  # Token inválido
        ["ID", "INVALID", "ID"],  # Token inválido en el medio
        ["(", "(", "ID", ")", ")"],  # Estructura válida pero no en la gramática
    ]
    
    for i, tokens in enumerate(error_cases, 1):
        print(f"\nCaso de error {i}: {tokens if tokens else '(vacío)'}")
        success, steps, message = parser.parse(tokens[:])
        
        if not success:
            print(f"✓ Error detectado correctamente: {message}")
        else:
            print(f"✗ Se esperaba error pero se aceptó la cadena")
            return False
    
    return True

def test_step_by_step():
    """Muestra el análisis paso a paso de una expresión"""
    print("\n=== TEST: Análisis Paso a Paso ===")
    
    table, parser, _ = analyze_slr_grammar("../resources/slr-1.yalp")
    
    if not table or not parser:
        return False
    
    # Analizar una expresión más compleja
    tokens = ["ID", "+", "ID", "*", "ID"]
    print(f"Analizando: {' '.join(tokens)}")
    
    success, steps, message = parser.parse(tokens)
    
    print(f"\nResultado: {message}")
    print(f"Total de pasos: {len(steps)}")
    
    return success

def main():
    """Función principal de pruebas"""
    print("PRUEBAS DE TABLA SLR(1) Y PARSER")
    print("="*50)
    
    tests = [
        ("Construcción de Tabla", test_slr_table_construction),
        ("Parsing Simple", test_simple_parsing),
        ("Visualización de Tabla", test_table_display),
        ("Múltiples Gramáticas", test_multiple_grammars),
        ("Manejo de Errores", test_error_handling),
        ("Análisis Paso a Paso", test_step_by_step),
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
        print(f"{test_name:<30} {status}")
    
    print(f"\nTotal: {passed}/{total} pruebas pasaron")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 