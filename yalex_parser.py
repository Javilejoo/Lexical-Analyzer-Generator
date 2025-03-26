def yalex_parser(yalex):
    #Read the .yal file
    with open(yalex, 'r') as file:
        yalex_code = file.read()
    #Delete comments
    yalex_code = delete_comments(yalex_code)
    #header
    header, yalex_code = extraer_header(yalex_code)
    #Expressions
    expresiones = extraer_expresiones(yalex_code)
    #Rules
    reglas = extraer_reglas(yalex_code)
    #Trailer
    trailer, yalex_code = extraer_trailer(yalex_code)

    return header, expresiones, reglas, trailer




def delete_comments(yalex_code):
    """Delete comments from the yalex code. comments begins with (* and ends with *)"""
    #Delete comments
    while '(*' in yalex_code:
        start = yalex_code.index('(*')
        end = yalex_code.index('*)') + 2
        yalex_code = yalex_code[:start] + yalex_code[end:]
    return yalex_code

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

def extraer_expresiones(yalex_code):
    """Extrae todas las definiciones 'let' antes de 'rule tokens ='."""
    expresiones = []
    pos_rule = yalex_code.find('rule tokens =')
    bloque_definiciones = yalex_code[:pos_rule] if pos_rule != -1 else yalex_code

    # Recorre cada línea
    for linea in bloque_definiciones.split('\n'):
        linea = linea.strip()
        if linea.startswith('let'):
            expresiones.append(linea)

    print("\nEXPRESIONES ENCONTRADAS:")
    for exp in expresiones:
        print(exp)

    return expresiones

def extraer_reglas(yalex_code):
    """Extrae las reglas completas después de 'rule tokens =' hasta que termina la sección."""
    reglas = []
    pos_rule = yalex_code.find('rule tokens =')
    if pos_rule == -1:
        return []

    # Sacar la parte desde rule tokens
    bloque_reglas = yalex_code[pos_rule:]
    lineas = bloque_reglas.split('\n')

    capturando = False
    for linea in lineas:
        if 'rule tokens =' in linea:
            capturando = True
            continue
        # Si encontramos un { solito o la siguiente sección, paramos
        if capturando and (linea.strip() == '' or linea.strip().startswith('{')):
            break
        if capturando:
            reglas.append(linea.strip())

    print("\nREGLAS ENCONTRADAS:")
    for reg in reglas:
        print(reg)

    return reglas

def extraer_trailer(yalex_code):
    """Busca la última regla y extrae el trailer si existe después."""
    trailer = ''

    #  Buscar la sección de reglas
    pos_rule = yalex_code.find('rule tokens =')
    if pos_rule == -1:
        return '', yalex_code  # No hay reglas

    #  Obtener todo el bloque de reglas
    reglas_bloque = yalex_code[pos_rule:]
    lineas = reglas_bloque.split('\n')

    # Identificar la ultima regla que contiene { return ... }
    ultima_regla = ''
    for linea in lineas:
        if '{' in linea and 'return' in linea:
            ultima_regla = linea.strip()

    if not ultima_regla:
        return '', yalex_code  # No encontro ninguna regla con acción

    #  Buscar esa última regla en todo el yalex_code
    pos_ultima_regla = yalex_code.find(ultima_regla)
    if pos_ultima_regla == -1:
        return '', yalex_code 

    posible_trailer = yalex_code[pos_ultima_regla + len(ultima_regla):].strip()
    start = posible_trailer.find('{')
    end = posible_trailer.find('}', start)

    if start != -1 and end != -1:
        trailer = posible_trailer[start + 1:end].strip()
        print("trailer:\n",trailer)
    else:
        print("No hay trailer")

    return trailer, yalex_code


#NOMBRE YALEX
yalex = 'yalexs/slr-3.yal'
yalex_parser(yalex)

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
                resultado += expand_printable_chars()
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
    """Genera la gran expresión infix final, protegiendo los literales especiales."""
    especiales = {'+', '-', '*', '/', '(', ')', '|', '?', ':', ';', '='}
    expresiones = []

    for regla in reglas_procesadas:
        if '=' in regla:
            _, expr = regla.split('=', 1)
            expr = expr.strip()
            # Revisar si la expresión es un literal especial y protegerlo
            if expr in especiales:
                expresiones.append(f"'{expr}'")
            else:
                expresiones.append(expr)

    # Unir todo con '|'
    return '|'.join(expresiones)

def generar_final_infix_total(reglas_procesadas, definiciones_expandidas):

    reglas_expr = generar_expresion_infix(reglas_procesadas) 
    final_expr = f"({reglas_expr})"
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

infix_final = generar_final_infix_total(reglas_procesadas, expandidas)
infix_final = convertir_puntos_a_literal(infix_final)

with open('output/final_infix.txt', 'w', encoding='utf-8') as f:
    f.write(infix_final)