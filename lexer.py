"""
Analizador léxico que lee un archivo de texto y genera tokens
basado en el AFD construido a partir de una expresión regular.
"""
import sys
from ERtoAFD import construir_afd
import estructuras
import shuntingyard as sy
from AFD_minimo import minimizar_AFD
from funciones import leerER
from nullableVisitor import NullableVisitor
from firstPosVisitor import FirstPosVisitor
from lastPosVisitor import LastPosVisitor
from followPosVisitor import FollowPosVisitor

class Token:
    def __init__(self, tipo, valor, linea, columna):
        self.tipo = tipo
        self.valor = valor
        self.linea = linea
        self.columna = columna
    
    def __str__(self):
        return f"Token({self.tipo}, '{self.valor}', línea={self.linea}, columna={self.columna})"

class Lexer:
    def __init__(self, afd, token_types):
        """
        Inicializa el analizador léxico con un AFD.
        
        Args:
            afd (dict): El autómata finito determinista.
            token_types (dict): Mapeo de patrones a tipos de tokens.
        """
        self.afd = afd
        self.token_types = token_types
        self.texto = ""
        self.posicion = 0
        self.linea = 1
        self.columna = 1
    
    def cargar_archivo(self, archivo):
        """Carga el contenido de un archivo de texto."""
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                self.texto = f.read()
            self.posicion = 0
            self.linea = 1
            self.columna = 1
            return True
        except Exception as e:
            print(f"Error al cargar el archivo: {e}")
            return False
    
    def cargar_texto(self, texto):
        """Carga un texto directamente en el analizador."""
        self.texto = texto
        self.posicion = 0
        self.linea = 1
        self.columna = 1
    
    def siguiente_token(self):
        """
        Encuentra y devuelve el siguiente token en el texto.
        
        Returns:
            Token: El token encontrado o None si se llega al final del texto.
        """
        # Ignorar espacios en blanco al inicio
        self._saltar_espacios()
        
        # Verificar si hemos llegado al final del texto
        if self.posicion >= len(self.texto):
            return None
        
        # Posición inicial del token
        inicio_token = self.posicion
        linea_token = self.linea
        columna_token = self.columna
        
        # Intentar reconocer el siguiente token
        mejor_longitud = 0
        mejor_tipo = None
        
        # Recorrer cada carácter a partir de la posición actual
        pos_actual = self.posicion
        estado_actual = self.afd['inicial']
        
        buffer = ""
        
        while pos_actual < len(self.texto):
            char = self.texto[pos_actual]
            
            # Verificar si el carácter pertenece al alfabeto del AFD
            if char not in self.afd['alfabeto']:
                break
            
            # Obtener transiciones para el estado actual
            transiciones = self.afd['transiciones'].get(estado_actual, {})
            
            # Verificar si hay una transición válida para el carácter actual
            if char in transiciones:
                buffer += char
                estado_actual = transiciones[char]
                pos_actual += 1
                
                # Si el estado actual es un estado de aceptación, actualizar el mejor token
                if estado_actual in self.afd['aceptacion']:
                    mejor_longitud = pos_actual - inicio_token
                    
                    # Determinar el tipo de token según el patrón
                    for patron, tipo in self.token_types.items():
                        # Aquí se simplifica la comparación del token, 
                        # idealmente se debería hacer una verificación más precisa
                        if buffer == patron:
                            mejor_tipo = tipo
                            break
                    
                    # Si no se ha identificado un tipo específico, usar un tipo genérico
                    if mejor_tipo is None:
                        if buffer.isdigit():
                            mejor_tipo = "NUMBER"
                        elif buffer.isalpha():
                            mejor_tipo = "IDENTIFIER"
                        else:
                            mejor_tipo = "SYMBOL"
            else:
                break
        
        # Si no se encontró ningún token válido, avanzar un carácter y reportar error
        if mejor_longitud == 0:
            token_error = Token("ERROR", self.texto[self.posicion], self.linea, self.columna)
            self._avanzar(1)
            return token_error
        
        # Crear el token con el tipo y valor encontrado
        valor_token = self.texto[inicio_token:inicio_token + mejor_longitud]
        token = Token(mejor_tipo, valor_token, linea_token, columna_token)
        
        # Actualizar la posición actual
        self._avanzar(mejor_longitud)
        
        return token
    
    def obtener_todos_tokens(self):
        """
        Obtiene todos los tokens del texto.
        
        Returns:
            list: Lista de todos los tokens encontrados.
        """
        tokens = []
        token = self.siguiente_token()
        
        while token is not None:
            tokens.append(token)
            token = self.siguiente_token()
        
        return tokens
    
    def _saltar_espacios(self):
        """Avanza la posición actual saltando espacios en blanco."""
        while self.posicion < len(self.texto) and self.texto[self.posicion].isspace():
            self._avanzar(1)
    
    def _avanzar(self, n):
        """
        Avanza n caracteres en el texto, actualizando línea y columna.
        
        Args:
            n (int): Número de caracteres a avanzar.
        """
        for i in range(n):
            if self.posicion < len(self.texto):
                if self.texto[self.posicion] == '\n':
                    self.linea += 1
                    self.columna = 1
                else:
                    self.columna += 1
                self.posicion += 1

def cargar_afd_desde_er(er_file="output/final_infix.txt"):
    """
    Carga la expresión regular desde un archivo y construye el AFD.
    
    Args:
        er_file (str): Ruta al archivo con la expresión regular.
    
    Returns:
        dict: El AFD minimizado construido.
    """
    # Leer la expresión regular desde el archivo
    expresion = leerER(er_file)
    
    # Aumentar la expresión con el símbolo de fin
    infix = expresion + '#'
    
    # Convertir a postfix
    postfix = sy.convert_infix_to_postfix(infix)
    
    # Construir el árbol de expresión
    root = estructuras.build_expression_tree(postfix)
    
    # Asignar IDs de posición
    def assign_pos_ids(node):
        counter = [1]
        def traverse(n):
            if n is None:
                return
            if n.value != 'ε':
                if n.left is None and n.right is None:
                    n.pos_id = counter[0]
                    counter[0] += 1
            traverse(n.left)
            traverse(n.right)
        traverse(root)
        return root
    assign_pos_ids(root)
    
    # Calcular Nullable, FirstPos, LastPos, FollowPos
    visitors = [
        NullableVisitor(),
        FirstPosVisitor(),
        LastPosVisitor(),
        FollowPosVisitor()
    ]
    for visitor in visitors:
        root.accept(visitor)
    
    followpos_table = visitors[3].get_followpos_table()
    
    # Construir el AFD a partir del árbol y la tabla followpos
    afd = construir_afd(root, followpos_table)
    
    # Minimizar el AFD
    afd_min = minimizar_AFD(afd)
    
    # Generar imágenes: árbol de expresión, AFD y AFD minimizado
    from graphviz_utils import generate_expression_tree_image
    from AFDGV import dibujar_AFD
    generate_expression_tree_image(root, "output/expression_tree")
    print("Árbol de expresión generado en output/expression_tree.png")
    dibujar_AFD(afd, "output/afd")
    print("AFD guardado como output/afd.png")
    dibujar_AFD(afd_min, "output/afd_min")
    print("AFD minimizado guardado como output/afd_min.png")
    
    return afd_min


def cargar_token_types(rules_file="output/info_current_yal.txt"):
    """
    Carga los tipos de tokens desde el archivo de reglas.
    
    Args:
        rules_file (str): Ruta al archivo con las reglas.
    
    Returns:
        dict: Mapeo de patrones a tipos de tokens.
    """
    token_types = {}
    with open(rules_file, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Extraer la sección de reglas
    reglas_section = False
    for linea in contenido.splitlines():
        if linea.strip() == "REGLAS ENCONTRADAS:":
            reglas_section = True
            continue
        
        if reglas_section and linea.strip() and not linea.startswith("trailer:"):
            # Procesar la línea de regla
            partes = linea.strip().split('{')
            if len(partes) > 1:
                patron = partes[0].strip()
                tipo_match = partes[1].strip().split('return')[1].strip().rstrip('}').strip()
                
                # Limpiar el patrón
                patron = patron.strip().lstrip('|').strip()
                
                # Si el patrón está entre comillas, quitar las comillas
                if patron.startswith("'") and patron.endswith("'"):
                    patron = patron[1:-1]
                
                token_types[patron] = tipo_match
    
    # Agregar manualmente algunas reglas comunes si no están presentes
    if 'ws' not in token_types and ' ' not in token_types:
        token_types[' '] = 'WHITESPACE'
        token_types['\t'] = 'WHITESPACE'
        token_types['\n'] = 'WHITESPACE'
    
    return token_types

def analizar_archivo(input_file, er_file="output/final_infix.txt", rules_file="output/info_current_yal.txt"):
    """
    Analiza un archivo de texto y muestra los tokens encontrados.
    
    Args:
        input_file (str): Ruta al archivo a analizar.
        er_file (str): Ruta al archivo con la expresión regular.
        rules_file (str): Ruta al archivo con las reglas.
    """
    # Cargar el AFD
    afd = cargar_afd_desde_er(er_file)
    
    # Cargar los tipos de tokens
    token_types = cargar_token_types(rules_file)
    
    # Crear el analizador léxico
    lexer = Lexer(afd, token_types)
    
    # Cargar el archivo a analizar
    if not lexer.cargar_archivo(input_file):
        print(f"No se pudo analizar el archivo: {input_file}")
        return
    
    # Obtener y mostrar todos los tokens
    tokens = lexer.obtener_todos_tokens()
    
    print(f"--- Análisis léxico del archivo: {input_file} ---")
    for token in tokens:
        print(token)
    print(f"Total de tokens encontrados: {len(tokens)}")

def main():
    if len(sys.argv) < 2:
        print("Uso: python lexer.py <archivo_a_analizar>")
        return
    
    input_file = sys.argv[1]
    analizar_archivo(input_file)

if __name__ == "__main__":
    main()