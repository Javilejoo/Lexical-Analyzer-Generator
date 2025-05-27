import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from yapar_parser import parse_yapar_file, augment_grammar, print_grammar
from first_follow import analyze_grammar_first_follow

def test_grammar_file(filename):
    """Prueba una gramática específica"""
    print(f"\n{'='*60}")
    print(f"ANALIZANDO: {filename}")
    print(f"{'='*60}")
    
    # Parsear la gramática
    grammar = parse_yapar_file(f"../resources/{filename}")
    if not grammar:
        print(f"Error: No se pudo parsear {filename}")
        return
    
    # Mostrar la gramática original
    print_grammar(grammar)
    
    # Aumentar la gramática para SLR
    augment_grammar(grammar)
    
    # Calcular FIRST y FOLLOW
    first_sets, follow_sets = analyze_grammar_first_follow(grammar)
    
    return grammar, first_sets, follow_sets

def main():
    """Función principal"""
    print("PRUEBA DE CONJUNTOS FIRST Y FOLLOW")
    print("Analizando gramáticas SLR de ejemplo...")
    
    # Lista de archivos de gramática a probar
    grammar_files = [
        'slr-1.yalp',
        'slr-2.yalp', 
        'slr-3.yalp',
        'slr-4.yalp'
    ]
    
    results = {}
    
    for filename in grammar_files:
        try:
            result = test_grammar_file(filename)
            if result:
                results[filename] = result
        except Exception as e:
            print(f"Error procesando {filename}: {e}")
    
    # Resumen final
    print(f"\n{'='*60}")
    print("RESUMEN DE ANÁLISIS")
    print(f"{'='*60}")
    
    for filename, (grammar, first_sets, follow_sets) in results.items():
        print(f"\n{filename}:")
        print(f"  - Terminales: {len(grammar.tokens)}")
        print(f"  - No-terminales: {len(grammar.non_terminals)}")
        print(f"  - Producciones: {len(grammar.production_list)}")
        print(f"  - Símbolo inicial: {grammar.start_symbol}")

if __name__ == "__main__":
    main() 