"""
Implementación de los conjuntos FIRST y FOLLOW para gramáticas libres de contexto.
"""

def compute_first_sets(grammar):
    """
    Calcula los conjuntos FIRST para todos los símbolos de la gramática.
    
    Args:
        grammar: Objeto Grammar con las producciones
        
    Returns:
        dict: Diccionario con los conjuntos FIRST de cada símbolo
    """
    first_sets = {}
    
    # Inicializar conjuntos FIRST
    # Para terminales, FIRST(terminal) = {terminal}
    for terminal in grammar.tokens:
        first_sets[terminal] = {terminal}
    
    # Para no-terminales, inicializar como conjunto vacío
    for non_terminal in grammar.non_terminals:
        first_sets[non_terminal] = set()
    
    # Agregar epsilon como símbolo especial
    first_sets['ε'] = {'ε'}
    
    # Repetir hasta que no haya cambios
    changed = True
    while changed:
        changed = False
        
        # Para cada producción A → α
        for non_terminal, rules in grammar.productions.items():
            for rule in rules:
                # Si la regla está vacía, agregar ε
                if not rule:
                    if 'ε' not in first_sets[non_terminal]:
                        first_sets[non_terminal].add('ε')
                        changed = True
                    continue
                
                # Para cada símbolo en la regla
                for i, symbol in enumerate(rule):
                    # Si el símbolo no está en first_sets, es un error
                    if symbol not in first_sets:
                        # Asumir que es un terminal no declarado
                        first_sets[symbol] = {symbol}
                    
                    # Agregar FIRST(símbolo) - {ε} a FIRST(A)
                    symbol_first = first_sets[symbol] - {'ε'}
                    old_size = len(first_sets[non_terminal])
                    first_sets[non_terminal].update(symbol_first)
                    if len(first_sets[non_terminal]) > old_size:
                        changed = True
                    
                    # Si ε no está en FIRST(símbolo), parar
                    if 'ε' not in first_sets[symbol]:
                        break
                    
                    # Si llegamos al final y todos los símbolos derivan ε
                    if i == len(rule) - 1:
                        if 'ε' not in first_sets[non_terminal]:
                            first_sets[non_terminal].add('ε')
                            changed = True
    
    return first_sets

def compute_first_of_string(string, first_sets):
    """
    Calcula FIRST de una cadena de símbolos.
    
    Args:
        string: Lista de símbolos
        first_sets: Diccionario con conjuntos FIRST
        
    Returns:
        set: Conjunto FIRST de la cadena
    """
    if not string:
        return {'ε'}
    
    result = set()
    
    for i, symbol in enumerate(string):
        if symbol not in first_sets:
            # Asumir que es un terminal
            first_sets[symbol] = {symbol}
        
        # Agregar FIRST(símbolo) - {ε}
        symbol_first = first_sets[symbol] - {'ε'}
        result.update(symbol_first)
        
        # Si ε no está en FIRST(símbolo), parar
        if 'ε' not in first_sets[symbol]:
            break
        
        # Si llegamos al final y todos derivan ε
        if i == len(string) - 1:
            result.add('ε')
    
    return result

def compute_follow_sets(grammar, first_sets):
    """
    Calcula los conjuntos FOLLOW para todos los no-terminales de la gramática.
    
    Args:
        grammar: Objeto Grammar con las producciones
        first_sets: Diccionario con los conjuntos FIRST
        
    Returns:
        dict: Diccionario con los conjuntos FOLLOW de cada no-terminal
    """
    follow_sets = {}
    
    # Inicializar conjuntos FOLLOW para no-terminales
    for non_terminal in grammar.non_terminals:
        follow_sets[non_terminal] = set()
    
    # FOLLOW(S) contiene $ (símbolo de fin de entrada)
    if grammar.start_symbol:
        follow_sets[grammar.start_symbol].add('$')
    
    # Repetir hasta que no haya cambios
    changed = True
    while changed:
        changed = False
        
        # Para cada producción A → α
        for non_terminal, rules in grammar.productions.items():
            for rule in rules:
                # Para cada símbolo en la regla
                for i, symbol in enumerate(rule):
                    # Solo procesar no-terminales
                    if symbol in grammar.non_terminals:
                        # β es lo que sigue después del símbolo
                        beta = rule[i + 1:]
                        
                        # Calcular FIRST(β)
                        first_beta = compute_first_of_string(beta, first_sets)
                        
                        # Agregar FIRST(β) - {ε} a FOLLOW(símbolo)
                        first_beta_no_epsilon = first_beta - {'ε'}
                        old_size = len(follow_sets[symbol])
                        follow_sets[symbol].update(first_beta_no_epsilon)
                        if len(follow_sets[symbol]) > old_size:
                            changed = True
                        
                        # Si ε ∈ FIRST(β), agregar FOLLOW(A) a FOLLOW(símbolo)
                        if 'ε' in first_beta:
                            old_size = len(follow_sets[symbol])
                            follow_sets[symbol].update(follow_sets[non_terminal])
                            if len(follow_sets[symbol]) > old_size:
                                changed = True
    
    return follow_sets

def print_first_follow_sets(grammar, first_sets, follow_sets):
    """
    Imprime los conjuntos FIRST y FOLLOW de forma legible.
    
    Args:
        grammar: Objeto Grammar
        first_sets: Diccionario con conjuntos FIRST
        follow_sets: Diccionario con conjuntos FOLLOW
    """
    print("\n=== CONJUNTOS FIRST ===")
    
    # Imprimir FIRST de terminales
    print("\nTerminales:")
    for terminal in sorted(grammar.tokens):
        if terminal in first_sets:
            first_str = ', '.join(sorted(first_sets[terminal]))
            print(f"  FIRST({terminal}) = {{{first_str}}}")
    
    # Imprimir FIRST de no-terminales
    print("\nNo-terminales:")
    for non_terminal in grammar.non_terminals:
        if non_terminal in first_sets:
            first_str = ', '.join(sorted(first_sets[non_terminal]))
            print(f"  FIRST({non_terminal}) = {{{first_str}}}")
    
    print("\n=== CONJUNTOS FOLLOW ===")
    for non_terminal in grammar.non_terminals:
        if non_terminal in follow_sets:
            follow_str = ', '.join(sorted(follow_sets[non_terminal]))
            print(f"  FOLLOW({non_terminal}) = {{{follow_str}}}")

def analyze_grammar_first_follow(grammar):
    """
    Función principal para analizar una gramática y calcular FIRST y FOLLOW.
    
    Args:
        grammar: Objeto Grammar
        
    Returns:
        tuple: (first_sets, follow_sets)
    """
    print(f"\nAnalizando gramática con símbolo inicial: {grammar.start_symbol}")
    
    # Calcular conjuntos FIRST
    first_sets = compute_first_sets(grammar)
    
    # Calcular conjuntos FOLLOW
    follow_sets = compute_follow_sets(grammar, first_sets)
    
    # Imprimir resultados
    print_first_follow_sets(grammar, first_sets, follow_sets)
    
    return first_sets, follow_sets 