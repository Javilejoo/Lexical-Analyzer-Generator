import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yapar_parser2 import parse_yalp_file
from first_follow import compute_first_sets, compute_follow_sets

def adapt_grammar_format(grammar):
    """
    Adapta el formato de la gramática de yapar_parser2 para que sea compatible con first_follow.py
    """
    adapted_grammar = type('Grammar', (), {})
    
    # Configurar atributos necesarios
    adapted_grammar.tokens = grammar.terminals
    adapted_grammar.non_terminals = grammar.non_terminals
    adapted_grammar.productions = grammar.productions
    adapted_grammar.start_symbol = grammar.start_symbol
    
    return adapted_grammar

def test_grammar_file(filename):
    """Prueba una gramática específica usando yapar_parser2 y first_follow"""
    print(f"\n{'='*60}")
    print(f"ANALIZANDO: {filename}")
    print(f"{'='*60}")
    
    # Generar el path del archivo .yalp y el JSON resultante
    yalp_file = f"../resources/{filename}.yalp"
    json_file = f"../resources/{filename}.json"
    
    # Ejecutar el parser para generar el JSON
    try:
        grammar = parse_yalp_file(yalp_file)
        print(f"Gramática parseada correctamente desde {yalp_file}")
        
        # Mostrar la gramática en formato solicitado
        print(f"\nGrammar(")
        print(f"    terminals       = {grammar.terminals},")
        print(f"    non_terminals   = {grammar.non_terminals},")
        print(f"    productions     = {{")
        for nt, prods in grammar.productions.items():
            print(f"        '{nt}': {prods},")
        print(f"    }},")
        print(f"    start_symbol    = '{grammar.start_symbol}',")
        print(f"    ignored_tokens  = {grammar.ignored_tokens}")
        print(")\n")
    except Exception as e:
        print(f"Error al parsear {yalp_file}: {e}")
        return
    
    # Adaptar la gramática para first_follow.py
    adapted_grammar = adapt_grammar_format(grammar)
    
    # Calcular conjuntos FIRST
    first_sets = compute_first_sets(adapted_grammar)
    
    # Calcular conjuntos FOLLOW
    follow_sets = compute_follow_sets(adapted_grammar, first_sets)
    
    # Mostrar resultados
    print_first_follow_sets(grammar, first_sets, follow_sets)

def print_first_follow_sets(grammar, first_sets, follow_sets):
    """Imprime los conjuntos FIRST y FOLLOW en el formato solicitado"""
    print("\n=== CONJUNTOS FIRST ===\n")
    for non_terminal in grammar.non_terminals:
        if non_terminal in first_sets:
            first_str = ', '.join(sorted(first_sets[non_terminal]))
            print(f"First({non_terminal}) = {{{first_str}}}")
    
    print("\n=== CONJUNTOS FOLLOW ===\n")
    for non_terminal in grammar.non_terminals:
        if non_terminal in follow_sets:
            follow_str = ', '.join(sorted(follow_sets[non_terminal]))
            print(f"Follow({non_terminal}) = {{{follow_str}}}")

def main():
    """Función principal"""
    print("PRUEBA DE CONJUNTOS FIRST Y FOLLOW")
    print("Analizando gramáticas SLR de ejemplo...")
    
    # Lista de archivos de gramática a probar
    grammar_files = [
        'slr-1',
        'slr-2'
    ]
    
    for filename in grammar_files:
        try:
            test_grammar_file(filename)
        except Exception as e:
            print(f"Error procesando {filename}: {e}")

if __name__ == "__main__":
    main() 