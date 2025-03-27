"""
Generador completo de analizadores léxicos a partir de archivos YALex.

Este script integra todas las fases del proceso:
1. Procesa el archivo .yal para obtener la expresión regular
2. Genera el AFD a partir de la expresión regular
3. Crea un analizador léxico basado en el AFD generado
4. Provee funciones para analizar archivos de texto con el analizador generado

Uso:
    python generate_lexer.py <archivo.yal> [<archivo_a_analizar>]
"""

import os
import sys
import importlib
import subprocess
from lexer import Lexer, cargar_afd_desde_er, cargar_token_types

def verificar_requisitos():
    """Verifica si todos los módulos necesarios están disponibles."""
    modulos_requeridos = [
        "graphviz_utils", "estructuras", "shuntingyard", "funciones",
        "nullableVisitor", "firstPosVisitor", "lastPosVisitor", "followPosVisitor",
        "AFD_minimo", "AFDGV", "ERtoAFD"
    ]
    
    for modulo in modulos_requeridos:
        try:
            importlib.import_module(modulo)
        except ImportError:
            print(f"Error: No se encontró el módulo '{modulo}'.")
            print("Asegúrate de tener todos los archivos del proyecto en el directorio actual.")
            return False
    return True

def procesar_yal(archivo_yal):
    """
    Procesa el archivo .yal para obtener la expresión regular infix.
    
    Args:
        archivo_yal: Ruta al archivo .yal a procesar
    
    Returns:
        bool: True si el procesamiento fue exitoso, False en caso contrario
    """
    print(f"🔍 Procesando archivo YALex: {archivo_yal}")
    
    try:
        # Verificar si existe el archivo yalex_parser.py
        if os.path.exists("yalex_parser.py"):
            subprocess.run(["python", "yalex_parser.py", archivo_yal], check=True)
        else:
            # Intentar con parser_yal.py como alternativa
            subprocess.run(["python", "parser_yal.py", archivo_yal], check=True)
        
        # Verificar si se generó el archivo final_infix.txt
        if not os.path.exists("output/final_infix.txt"):
            print("❌ Error: No se generó el archivo final_infix.txt")
            return False
        
        print("✅ Archivo YALex procesado correctamente")
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al procesar el archivo YALex: {e}")
        return False

def construir_afd():
    """
    Construye el AFD a partir de la expresión regular infix.
    
    Returns:
        bool: True si la construcción fue exitosa, False en caso contrario
    """
    print("🔄 Construyendo el AFD a partir de la expresión regular")
    
    try:
        # Intentar importar y ejecutar la función principal de ERtoAFD.py
        import ERtoAFD
        ERtoAFD_module = sys.modules["ERtoAFD"]
        
        # Verificar si el módulo tiene una función principal
        if hasattr(ERtoAFD_module, "ERtoAFD"):
            # La función existe, pero no queremos ejecutarla completa
            # porque pide input al usuario. En su lugar, cargaremos el AFD directamente.
            print("✅ Módulo ERtoAFD importado correctamente")
            return True
        else:
            # Intentar ejecutar el script como un proceso independiente
            subprocess.run(["python", "ERtoAFD.py"], check=True)
            print("✅ AFD construido correctamente")
            return True
    
    except (ImportError, subprocess.CalledProcessError) as e:
        print(f"❌ Error al construir el AFD: {e}")
        return False

def generar_analizador():
    """
    Genera el analizador léxico basado en el AFD construido.
    
    Returns:
        tuple: (Lexer, dict) Un objeto Lexer y un diccionario de tipos de tokens,
               o (None, None) en caso de error
    """
    print("🔧 Generando el analizador léxico")
    
    try:
        # Cargar el AFD desde el archivo de expresión regular
        afd = cargar_afd_desde_er()
        
        # Cargar los tipos de tokens desde el archivo de reglas
        token_types = cargar_token_types()
        
        # Crear el analizador léxico
        lexer = Lexer(afd, token_types)
        
        print("✅ Analizador léxico generado correctamente")
        return lexer, token_types
    
    except Exception as e:
        print(f"❌ Error al generar el analizador léxico: {e}")
        return None, None

def analizar_archivo(lexer, archivo):
    """
    Analiza un archivo de texto con el analizador léxico generado.
    
    Args:
        lexer: Objeto Lexer para realizar el análisis
        archivo: Ruta al archivo a analizar
    
    Returns:
        list: Lista de tokens encontrados, o None en caso de error
    """
    print(f"📝 Analizando archivo: {archivo}")
    
    try:
        # Cargar el archivo a analizar
        if not lexer.cargar_archivo(archivo):
            print(f"❌ No se pudo abrir el archivo: {archivo}")
            return None
        
        # Obtener y mostrar todos los tokens
        tokens = lexer.obtener_todos_tokens()
        
        print(f"✅ Análisis completado: {len(tokens)} tokens encontrados")
        return tokens
    
    except Exception as e:
        print(f"❌ Error al analizar el archivo: {e}")
        return None

def mostrar_tokens(tokens):
    """Muestra los tokens en un formato legible."""
    print("\n📋 Tokens encontrados:")
    print("─" * 60)
    print(f"{'#':^5} {'TIPO':<15} {'VALOR':<20} {'LÍNEA':<5} {'COLUMNA':<5}")
    print("─" * 60)
    
    for i, token in enumerate(tokens):
        if token.tipo != "WHITESPACE":  # Opcional: filtrar espacios en blanco
            print(f"{i+1:^5} {token.tipo:<15} {repr(token.valor):<20} {token.linea:<5} {token.columna:<5}")
    
    print("─" * 60)
    
    # Generar un resumen de tipos de tokens
    tipos = {}
    for token in tokens:
        if token.tipo not in tipos:
            tipos[token.tipo] = 0
        tipos[token.tipo] += 1
    
    print("\n📊 Resumen por tipo de token:")
    for tipo, cantidad in tipos.items():
        print(f"  {tipo}: {cantidad}")

def main():
    """Función principal del generador de analizadores léxicos."""
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("Uso: python generate_lexer.py <archivo.yal> [<archivo_a_analizar>]")
        return
    
    # Verificar requisitos
    if not verificar_requisitos():
        return
    
    # Crear directorio de salida si no existe
    os.makedirs("output", exist_ok=True)
    
    # Obtener archivo .yal
    archivo_yal = sys.argv[1]
    
    # Procesar archivo .yal
    if not procesar_yal(archivo_yal):
        return
    
    # Construir AFD
    if not construir_afd():
        return
    
    # Generar analizador léxico
    lexer, token_types = generar_analizador()
    if lexer is None:
        return
    
    # Analizar archivo si se proporcionó
    if len(sys.argv) > 2:
        archivo_analizar = sys.argv[2]
        tokens = analizar_archivo(lexer, archivo_analizar)
        if tokens:
            mostrar_tokens(tokens)
    else:
        print("\n🔍 No se especificó un archivo para analizar.")
        print("Puedes usar el analizador léxico generado para analizar archivos de texto.")
        print("Ejemplo: python test_lexer.py")

if __name__ == "__main__":
    main()