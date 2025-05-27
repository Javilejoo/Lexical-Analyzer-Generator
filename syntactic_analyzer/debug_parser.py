#!/usr/bin/env python3
"""
Script de debug para el parser SLR
"""

from slr_table import analyze_slr_grammar

def debug_simple_case():
    """Debug del caso simple ID + ID"""
    print("=== DEBUG: ID + ID ===")
    
    # Construir tabla
    table, parser, _ = analyze_slr_grammar('resources/slr-1.yalp')
    
    # Verificar algunas entradas clave de la tabla
    print("\nEntradas clave de la tabla:")
    print(f"Estado 0, ID: {table.get_action(0, 'ID')}")
    print(f"Estado 5, PLUS: {table.get_action(5, 'PLUS')}")
    print(f"Estado 5, $: {table.get_action(5, '$')}")
    
    # Verificar transiciones GOTO
    print(f"Estado 0, factor: {table.get_goto(0, 'factor')}")
    print(f"Estado 0, term: {table.get_goto(0, 'term')}")
    print(f"Estado 0, expression: {table.get_goto(0, 'expression')}")
    
    # Simular manualmente el parsing
    print("\n=== Simulación manual ===")
    tokens = ['ID', '+', 'ID', '$']
    stack = [0]
    buffer = tokens[:]
    
    step = 1
    while buffer:
        current_state = stack[-1]
        current_token = buffer[0]
        action = table.get_action(current_state, current_token)
        
        print(f"Paso {step}: Estado {current_state}, Token '{current_token}' → {action}")
        
        if action.type.value == 'shift':
            stack.append(current_token)
            stack.append(action.value)
            buffer.pop(0)
            print(f"  Pila después de shift: {stack}")
        elif action.type.value == 'reduce':
            production = table.grammar.production_list[action.value]
            print(f"  Reducir por: {production}")
            
            # Quitar elementos de la pila
            symbols_to_remove = len(production.right)
            if symbols_to_remove > 0:
                for _ in range(symbols_to_remove * 2):
                    if len(stack) > 1:
                        stack.pop()
            
            # GOTO
            current_state = stack[-1]
            goto_state = table.get_goto(current_state, production.left)
            print(f"  GOTO({current_state}, {production.left}) = {goto_state}")
            
            stack.append(production.left)
            stack.append(goto_state)
            print(f"  Pila después de reduce: {stack}")
        elif action.type.value == 'accept':
            print("  ¡ACEPTADO!")
            break
        else:
            print(f"  ERROR: {action}")
            break
        
        step += 1
        if step > 20:  # Prevenir bucles
            print("  Demasiados pasos, parando...")
            break

if __name__ == "__main__":
    debug_simple_case() 