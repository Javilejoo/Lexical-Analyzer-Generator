import sys
import os
os.makedirs("output", exist_ok=True)

def leer_archivo_char_por_char(ruta_archivo):
    """Lee un archivo carácter por carácter y devuelve su contenido como string."""
    contenido = ""
    with open(ruta_archivo, 'r') as file:
        char = file.read(1)  # Lee un carácter a la vez
        while char:
            contenido += char
            char = file.read(1)
    return contenido

def yalex_parser(yalex):
    # Leer el archivo .yal carácter por carácter
    yalex_code = leer_archivo_char_por_char(yalex)
    
    # Eliminar comentarios
    yalex_code = delete_comments(yalex_code)
    
    # Extraer header
    header, yalex_code = extraer_header(yalex_code)
    
    # Extraer expresiones
    expresiones = extraer_expresiones_char_por_char(yalex_code)
    
    # Extraer reglas
    reglas = extraer_reglas_char_por_char(yalex_code)
    
    # Extraer trailer
    trailer, yalex_code = extraer_trailer_char_por_char(yalex_code)
    
    return header, expresiones, reglas, trailer

def delete_comments(yalex_code):
    """Elimina comentarios del código yalex. Los comentarios comienzan con (* y terminan con *)"""
    resultado = ""
    i = 0
    en_comentario = False
    
    while i < len(yalex_code):
        # Verifica si comienza un comentario
        if i < len(yalex_code) - 1 and yalex_code[i:i+2] == "(*":
            en_comentario = True
            i += 2
            continue
        
        # Verifica si termina un comentario
        if en_comentario and i < len(yalex_code) - 1 and yalex_code[i:i+2] == "*)":
            en_comentario = False
            i += 2
            continue
        
        # Si no estamos en un comentario, añade el carácter al resultado
        if not en_comentario:
            resultado += yalex_code[i]
        
        i += 1
    
    return resultado

def extraer_header(yalex_code):
    """Extrae el header solo si aparece antes de la primera 'let'."""
    header = ''
    pos_let = yalex_code.find('let')
    pos_llave = yalex_code.find('{')

    if pos_llave != -1 and (pos_let == -1 or pos_llave < pos_let):
        # Hay una llave antes del primer let: sí hay header
        start = pos_llave
        end = yalex_code.find('}', start)
        if end != -1:
            header = yalex_code[start+1:end].strip()
            yalex_code = yalex_code[:start] + yalex_code[end+1:]
            print("header:\n",header)
        else:
            print("No hay header")
    return header, yalex_code

def extraer_expresiones_char_por_char(yalex_code):
    """Extrae todas las definiciones 'let' antes de 'rule tokens =' procesando carácter por carácter."""
    expresiones = []
    pos_rule = yalex_code.find('rule tokens =')
    bloque_definiciones = yalex_code[:pos_rule] if pos_rule != -1 else yalex_code
    
    # Procesar carácter por carácter
    i = 0
    linea_actual = ""
    
    while i < len(bloque_definiciones):
        # Si encontramos un salto de línea, procesamos la línea actual
        if bloque_definiciones[i] == '\n':
            linea_actual = linea_actual.strip()
            if linea_actual.startswith('let'):
                expresiones.append(linea_actual)
            linea_actual = ""
        else:
            linea_actual += bloque_definiciones[i]
        
        i += 1
    
    # Procesar la última línea si queda alguna
    linea_actual = linea_actual.strip()
    if linea_actual.startswith('let'):
        expresiones.append(linea_actual)
    
    print("\nEXPRESIONES ENCONTRADAS:")
    for exp in expresiones:
        print(exp)
    
    return expresiones

def extraer_reglas_char_por_char(yalex_code):
    """Extrae las reglas completas después de 'rule tokens =' procesando carácter por carácter."""
    reglas = []
    pos_rule = yalex_code.find('rule tokens =')
    if pos_rule == -1:
        return []
    
    # Sacar la parte desde rule tokens
    bloque_reglas = yalex_code[pos_rule:]
    
    # Procesar carácter por carácter
    i = 0
    linea_actual = ""
    capturando = False
    
    while i < len(bloque_reglas):
        # Si encontramos un salto de línea, procesamos la línea actual
        if bloque_reglas[i] == '\n':
            linea_actual = linea_actual.strip()
            
            if 'rule tokens =' in linea_actual:
                capturando = True
            elif capturando and (linea_actual == '' or linea_actual.startswith('{')):
                capturando = False  # Terminar captura si encontramos línea vacía o inicio de trailer
            elif capturando:
                reglas.append(linea_actual)
                
            linea_actual = ""
        else:
            linea_actual += bloque_reglas[i]
        
        i += 1
    
    # Procesar la última línea si queda alguna
    linea_actual = linea_actual.strip()
    if capturando and linea_actual and not linea_actual.startswith('{'):
        reglas.append(linea_actual)
    
    print("\nREGLAS ENCONTRADAS:")
    for reg in reglas:
        print(reg)
    
    return reglas

def extraer_trailer_char_por_char(yalex_code):
    """Busca la última regla y extrae el trailer si existe después, procesando carácter por carácter."""
    trailer = ''
    
    # Buscar la sección de reglas
    pos_rule = yalex_code.find('rule tokens =')
    if pos_rule == -1:
        return '', yalex_code  # No hay reglas
    
    # Obtener todo el bloque de reglas
    reglas_bloque = yalex_code[pos_rule:]
    
    # Identificar la última regla que contiene { return ... }
    i = 0
    linea_actual = ""
    ultima_regla = ""
    
    while i < len(reglas_bloque):
        if reglas_bloque[i] == '\n':
            linea_actual = linea_actual.strip()
            if '{' in linea_actual and 'return' in linea_actual:
                ultima_regla = linea_actual
            linea_actual = ""
        else:
            linea_actual += reglas_bloque[i]
        
        i += 1
    
    # Procesar la última línea
    linea_actual = linea_actual.strip()
    if '{' in linea_actual and 'return' in linea_actual:
        ultima_regla = linea_actual
    
    if not ultima_regla:
        return '', yalex_code  # No encontró ninguna regla con acción
    
    # Buscar esa última regla en todo el yalex_code
    pos_ultima_regla = yalex_code.find(ultima_regla)
    if pos_ultima_regla == -1:
        return '', yalex_code
    
    posible_trailer = yalex_code[pos_ultima_regla + len(ultima_regla):].strip()
    start = posible_trailer.find('{')
    end = posible_trailer.find('}', start)
    
    if start != -1 and end != -1:
        trailer = posible_trailer[start + 1:end].strip()
        print("trailer:\n", trailer)
    else:
        print("No hay trailer")
    
    return trailer, yalex_code

#NOMBRE YALEX
if len(sys.argv) > 1:
    yalex = sys.argv[1]
else:
    yalex = 'output/yalexs/slr-5.yal'

# Llamamos a yalex_parser una sola vez y guardamos los resultados
header, expresiones, reglas, trailer = yalex_parser(yalex)

with open("output/info_current_yal.txt", "w", encoding="utf-8") as f:
    f.write("header:\n" + header + "\n\n")
    f.write("EXPRESIONES ENCONTRADAS:\n")
    for exp in expresiones:
        f.write(exp + "\n")
    f.write("\nREGLAS ENCONTRADAS:\n")
    for reg in reglas:
        f.write(reg + "\n")
    f.write("\ntrailer:\n" + trailer + "\n")


# despues de extraer yal.
def expand_definitions_recursivo(definiciones):
    """Expande todas las definiciones recursivamente."""
    expanded = {}

    def expand(nombre):
        if nombre in expanded:
            return expanded[nombre]
        expr = definiciones[nombre]
        resultado = ''
        i = 0
        while i < len(expr):
            # Detectar invocación a otro 'let'
            if expr[i].isalpha():
                token = ''
                while i < len(expr) and (expr[i].isalnum() or expr[i] == '_'):
                    token += expr[i]
                    i += 1
                if token in definiciones:
                    resultado += f'({expand(token)})'
                else:
                    resultado += token

            # Detectar literales entre comillas simples
            elif expr[i] == "'":
                i += 1
                literal = ''
                while i < len(expr) and expr[i] != "'":
                    literal += expr[i]
                    i += 1
                i += 1  # Saltar la comilla de cierre
                # Si el literal es alfabético se deja sin comillas (ejemplo: 'E' se convierte en E)
                # En caso contrario (como '+' o '-') se encierra en comillas
                if literal.isalpha():
                    resultado += literal
                else:
                    resultado += f"'{literal}'"

            # Detectar rangos
            elif expr[i] == '[':
                fin = expr.find(']', i)
                resultado += expand_range(expr[i:fin+1])
                i = fin + 1

            elif expr[i] == '_':
                resultado += expandir_guion_bajo_como_imprimibles()
                i += 1

            else:
                resultado += expr[i]
                i += 1
        expanded[nombre] = resultado
        return resultado

    for nombre in definiciones:
        expand(nombre)

    return expanded


def extraer_literal(cadena, indice):
    """
    Extrae un literal encerrado en comillas simples desde la posición 'indice' en 'cadena'.
    Interpreta secuencias de escape como \t y \n.
    Retorna el literal completo y la posición siguiente a la comilla de cierre.
    """
    literal = ''
    i = indice + 1  # Saltar la comilla inicial
    while i < len(cadena):
        if cadena[i] == '\\':  # Secuencia de escape
            i += 1
            if i < len(cadena):
                if cadena[i] == 't':
                    literal += '\\t'
                elif cadena[i] == 'n':
                    literal += '\\n'
                else:
                    literal += cadena[i]
                i += 1
        elif cadena[i] == "'":
            return literal, i + 1
        else:
            literal += cadena[i]
            i += 1
    raise ValueError("Literal entre comillas simples no cerrado correctamente.")

def extraer_literal_doble(cadena, indice):
    """
    Extrae un literal encerrado en comillas dobles desde la posición 'indice' en 'cadena'.
    Maneja secuencias de escape de forma similar.
    """
    literal = ''
    i = indice + 1  # Saltar la comilla doble inicial
    while i < len(cadena):
        if cadena[i] == '\\':
            i += 1
            if i < len(cadena):
                if cadena[i] == 't':
                    literal += '\t'
                elif cadena[i] == 'n':
                    literal += '\n'
                else:
                    literal += cadena[i]
                i += 1
        elif cadena[i] == '"':
            return literal, i + 1
        else:
            literal += cadena[i]
            i += 1
    raise ValueError("Literal entre comillas dobles no cerrado correctamente.")

def expandir_guion_bajo_como_imprimibles():
    def escapar(c):
        # Para Graphviz, necesitamos un enfoque diferente para caracteres problemáticos
        if c == "'":
            return "COMILLASIMPLE"  # Usamos un marcador temporal
        elif c == '"':
            return "COMILLADOBLE"  # Usamos un marcador temporal
        elif c == '\\':
            return "BACKSLASH"  # Usamos un marcador temporal
        elif c == '|':
            return "PIPE"  # Usamos un marcador temporal
        else:
            return c

    # Generamos la unión de caracteres sin los problemáticos
    chars = []
    for i in range(32, 127):
        char = chr(i)
        if char not in "'\\|":
            chars.append(f"'{char}'")
        elif char == "'":
            chars.append("'Q'")
        elif char == '\\':
            chars.append("'B'")
        elif char == '|':
            chars.append("'P'")
    
    return '(' + '|'.join(chars) + ')'

def expand_range(rango):
    # Procesa una cadena de rango, por ejemplo: ['+''-'] o ['0'-'2']
    elementos = []
    i = 0
    while i < len(rango):
        if rango[i] == "'":
            i += 1
            char = ''
            while i < len(rango) and rango[i] != "'":
                char += rango[i]
                i += 1
            elementos.append(char)
            i += 1  # Saltar la comilla final
        elif rango[i] == '"':  # Soporte para ["\s\t\n"] si lo necesitaras
            i += 1
            while i < len(rango) and rango[i] != '"':
                if rango[i] == '\\' and i + 1 < len(rango):
                    if rango[i+1] in ('t','n','s'):
                        if rango[i+1] == 't':
                            elementos.append('\\t')
                        elif rango[i+1] == 'n':
                            elementos.append('\\n')
                        elif rango[i+1] == 's':
                            elementos.append(' ')
                        i += 2
                    else:
                        elementos.append(rango[i])
                        i += 1
                else:
                    elementos.append(rango[i])
                    i += 1
            i += 1  # Saltar la comilla de cierre
        elif rango[i] == '-':
            # Maneja el rango, por ejemplo: 'A'-'Z'
            start = elementos.pop()
            i += 1  # Saltar el guion
            if i < len(rango) and rango[i] == "'":
                i += 1
                end = ''
                while i < len(rango) and rango[i] != "'":
                    end += rango[i]
                    i += 1
                i += 1  # cerrar '
                # Expandir rango
                for c in range(ord(start), ord(end) + 1):
                    elementos.append(chr(c))
        else:
            i += 1
    return '(' + '|'.join(map(escape_specials, elementos)) + ')'




def escape_specials(char):
    # Si es alfanumérico, lo dejamos sin comillas
    if char.isalnum():
        return char
    # En otro caso, se encierra en comillas simples
    return f"'{char}'"


    
def convertir_puntos_a_literal(expresion):
    """
    Recorre la expresión y convierte cada punto que no esté dentro de comillas 
    en "'.'" para que se trate como literal.
    """
    resultado = ""
    in_quote = False
    i = 0
    while i < len(expresion):
        ch = expresion[i]
        if ch == "'":
            # Alternar estado de literal
            resultado += ch
            in_quote = not in_quote
            i += 1
        else:
            # Si no estamos dentro de un literal y encontramos un punto, lo convertimos
            if not in_quote and ch == '.':
                resultado += "'.'"
                i += 1
            else:
                resultado += ch
                i += 1
    return resultado



def extraer_expresiones_del_txt(contenido):
    """
    Recibe el contenido del output.txt y regresa solo las líneas de 'let'
    """
    expresiones = []
    lines = contenido.splitlines()
    guardar = False
    for line in lines:
        if line.strip().startswith("EXPRESIONES ENCONTRADAS"):
            guardar = True
            continue
        if line.strip().startswith("REGLAS ENCONTRADAS") or line.strip().startswith("trailer:"):
            break
        if guardar and line.strip().startswith("let"):
            expresiones.append(line.strip())
    return expresiones

def extraer_reglas_del_txt(contenido):
    """
    Extrae solo las líneas de la sección 'REGLAS ENCONTRADAS' desde el .txt
    """
    reglas = []
    lines = contenido.splitlines()
    guardar = False
    for line in lines:
        if line.strip().startswith("REGLAS ENCONTRADAS"):
            guardar = True
            continue
        if line.strip().startswith("trailer:"):
            break  # Terminamos las reglas cuando empieza el trailer
        if guardar and line.strip() != '':
            reglas.append(line.strip())
    return reglas


def procesar_expresiones(expresiones):
    """
    Convierte las líneas 'let' en un diccionario {nombre: expresión}
    """
    definiciones = {}
    for exp in expresiones:
        _, resto = exp.split('let', 1)
        nombre, expr = resto.strip().split('=', 1) # s
        definiciones[nombre.strip()] = expr.strip()
    return definiciones

def apply_operator(expansion, operador):
    """Aplica +, *, ? evitando doble paréntesis"""
    if expansion.startswith('(') and expansion.endswith(')'):
        return f"{expansion}{operador}"
    else:
        return f"({expansion}){operador}"
    
def expand_printable_chars():
    """
    Genera una cadena que representa la unión de todos los caracteres imprimibles (ASCII 32 a 126),
    cada uno entre comillas simples, separados por '|', y todo entre paréntesis.
    Ejemplo: (' '|'!'|'"'|...|'~')
    """
    printable_chars = [chr(i) for i in range(32, 127)]
    union = '|'.join("'" + c + "'" for c in printable_chars)
    return '(' + union + ')'
    
def procesar_reglas(reglas, definiciones_expandidas):
    """Procesa las reglas y expande las referencias usando las definiciones."""
    reglas_procesadas = []
    for regla in reglas:
        # Si la regla contiene acción (indicada por '{' y 'return')
        if '{' in regla and 'return' in regla:
            patron = regla[:regla.find('{')].strip()
            token = regla[regla.find('return') + 6:].replace('}', '').strip()
        else:
            # Si no tiene acción, se toma la regla completa
            patron = regla.strip()
            token = patron  # Se asigna el propio patrón como token
        
        # Limpiar el patrón de posibles '|' y espacios adicionales
        patron_limpio = patron.strip().lstrip('|').strip()

        # Expandir el patrón si es una referencia a una definición
        if patron_limpio in definiciones_expandidas:
            patron_expandido = definiciones_expandidas[patron_limpio]
        elif patron_limpio.startswith("'") and patron_limpio.endswith("'"):
            patron_expandido = patron_limpio[1:-1]  # quitar comillas
        else:
            patron_expandido = patron_limpio  # dejarlo literal si no es definición

        # Agregar la regla procesada en formato: -> token = patrón_expandido
        reglas_procesadas.append(f"-> {token} = {patron_expandido}")

    return reglas_procesadas

def generar_expresion_infix(reglas_procesadas):
    """Genera la gran expresión infix final con anotación del token."""
    especiales = {'+', '-', '*', '/', '(', ')', '|', '?', ':', ';', '=', '<'}
    expresiones = []

    for regla in reglas_procesadas:
        if '=' in regla:
            token_part, expr = regla.split('=', 1)
            token = token_part.replace('->', '').strip()
            expr = expr.strip()
            # Revisar si la expresión es un literal especial y protegerlo
            if expr in especiales:
                expresiones.append(f"('{expr}')# --> {token}")
            else:
                expresiones.append(f"({expr})# --> {token}")

    return '\n'.join(expresiones)


def generar_final_infix_total(reglas_procesadas):

    reglas_expr = generar_expresion_infix(reglas_procesadas) 
    final_expr = f"{reglas_expr}"
    # Englobar toda la expresión entre paréntesis
    
    return final_expr

with open('output/info_current_yal.txt', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Extraer solo la sección de expresiones
expresiones = extraer_expresiones_del_txt(contenido)
# Convertir a diccionario de definiciones
definiciones = procesar_expresiones(expresiones)


# Expandir las definiciones de forma recursiva
expandidas = expand_definitions_recursivo(definiciones)

# Extraer las reglas (de la parte de REGLAS ENCONTRADAS del archivo)
reglas = extraer_reglas_del_txt(contenido)

# Procesar las reglas y expandir
reglas_procesadas = procesar_reglas(reglas, expandidas)

infix_final = generar_expresion_infix(reglas_procesadas)

# Guardar definiciones y reglas en el mismo archivo
with open('output/processed_definitions.txt', 'w', encoding='utf-8') as f:
    f.write("---- Processed Definitions ----\n")
    for nombre, expr in expandidas.items():
        f.write(f"  -> {nombre} = {expr}\n")

    f.write("\n---- Rules processed ----\n")
    for regla in reglas_procesadas:
        f.write(f"  {regla}\n")

    f.write("\n---- Infix final ----\n")
    f.write(infix_final)

with open('output/final_infix.txt', 'w', encoding='utf-8') as f:
    f.write(infix_final)

infix_final = generar_final_infix_total(reglas_procesadas)
infix_final = convertir_puntos_a_literal(infix_final)

with open('output/final_infix.txt', 'w', encoding='utf-8') as f:
    f.write(infix_final)