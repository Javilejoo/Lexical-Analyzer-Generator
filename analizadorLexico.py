def leer_yalex(archivo):
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Eliminar comentarios (* ... *)
    contenido = eliminar_comentarios(contenido)
    
    # Extraer header (primera ocurrencia de { ... })
    header, contenido = extraer_primera_seccion(contenido, '{', '}')
    
    # Extraer trailer (última ocurrencia de { ... })
    trailer = extraer_ultima_seccion(contenido, '{', '}')
    
    # Extraer definiciones (let ident = regexp)
    definiciones = extraer_definiciones(contenido)
    
    # Extraer reglas dentro de "rule gettoken ="
    reglas = extraer_reglas(contenido)
    
    return {
        "header": header,
        "trailer": trailer,
        "definiciones": definiciones,
        "reglas": reglas
    }

def eliminar_comentarios(texto):
    resultado = ""
    i = 0
    while i < len(texto):
        if i + 1 < len(texto) and texto[i:i+2] == "(*":
            # Buscar el cierre del comentario
            fin_comentario = texto.find("*)", i+2)
            if fin_comentario != -1:
                i = fin_comentario + 2
            else:
                # Si no hay cierre, avanzar
                i += 2
        else:
            resultado += texto[i]
            i += 1
    return resultado

def extraer_primera_seccion(texto, inicio, fin):
    i = texto.find(inicio)
    if i == -1:
        return "", texto
    
    nivel = 0
    j = i + 1
    while j < len(texto):
        if texto[j] == inicio:
            nivel += 1
        elif texto[j] == fin:
            if nivel == 0:
                # Extraer el contenido sin los delimitadores
                contenido = texto[i+1:j].strip()
                # Devolver el contenido y el resto del texto
                return contenido, texto[:i] + texto[j+1:]
            nivel -= 1
        j += 1
    
    return "", texto

def extraer_ultima_seccion(texto, inicio, fin):
    # Encontrar todas las secciones
    secciones = []
    i = 0
    while i < len(texto):
        if texto[i] == inicio:
            nivel = 0
            inicio_seccion = i
            i += 1
            while i < len(texto):
                if texto[i] == inicio:
                    nivel += 1
                elif texto[i] == fin:
                    if nivel == 0:
                        # Extraer la sección
                        contenido = texto[inicio_seccion+1:i].strip()
                        secciones.append(contenido)
                        break
                    nivel -= 1
                i += 1
        i += 1
    
    # Devolver la última sección o cadena vacía
    return secciones[-1] if secciones else ""

def extraer_definiciones(texto):
    definiciones = []
    for linea in texto.split('\n'):
        linea = linea.strip()
        if linea.startswith('let'):
            partes = linea[3:].split('=', 1)
            if len(partes) == 2:
                ident = partes[0].strip()
                expr = partes[1].split('(*')[0].strip()  # Ignorar comentarios
                if expr.startswith('[') and expr.endswith(']'):
                    elementos = parse_char_set(expr)
                    definiciones.append((ident, elementos))
    return definiciones

def extraer_reglas(texto):
    reglas = []
    
    # Buscar la sección de reglas
    inicio = texto.find('rule gettoken =')
    if inicio == -1:
        return reglas
    
    # Encontrar el final de la sección de reglas
    fin = texto.find('{', inicio)
    fin = texto.find('print', fin) if fin != -1 else len(texto)
    
    if fin == -1:
        return reglas
    
    # Extraer la sección de reglas
    seccion_reglas = texto[inicio:fin].strip()
    
    # Dividir por '|'
    rule_parts = []
    lineas = seccion_reglas.split('\n')
    current_part = ""
    
    for linea in lineas:
        linea = linea.strip()
        if not linea.startswith('rule') and linea:  # Ignorar la línea que contiene 'rule gettoken ='
            if linea.startswith('|'):
                if current_part:
                    rule_parts.append(current_part)
                current_part = linea[1:].strip()
            else:
                current_part += " " + linea.strip()
    
    if current_part:
        rule_parts.append(current_part)
    
    # Procesar cada parte
    for part in rule_parts:
        if not part.strip():
            continue
        
        # Buscar la acción entre llaves
        inicio_accion = -1
        fin_accion = -1
        nivel = 0
        
        for i in range(len(part)):
            if part[i] == '{':
                if nivel == 0:
                    inicio_accion = i
                nivel += 1
            elif part[i] == '}':
                nivel -= 1
                if nivel == 0:
                    fin_accion = i
                    break
        
        if inicio_accion != -1 and fin_accion != -1:
            action = part[inicio_accion+1:fin_accion].strip()
            pattern = part[:inicio_accion].strip()
            reglas.append((pattern, action))
    
    return reglas

def parse_char_set(expr):
    expr = expr.strip()[1:-1]
    elements = []
    i = 0
    n = len(expr)
    
    escape_map = {'t': '\t', 'n': '\n', 'r': '\r', "'": "'", '\\': '\\'}
    
    while i < n:
        if expr[i] == "'":
            i += 1
            char = ""
            while i < n and expr[i] != "'":
                if expr[i] == "\\":
                    i += 1
                    char += escape_map.get(expr[i], expr[i])
                else:
                    char += expr[i]
                i += 1
            i += 1
            if i < n and expr[i] == '-':
                i += 2
                end_char = ""
                while i < n and expr[i] != "'":
                    if expr[i] == "\\":
                        i += 1
                        end_char += escape_map.get(expr[i], expr[i])
                    else:
                        end_char += expr[i]
                    i += 1
                i += 1
                elements.append(('range', char, end_char))
            else:
                elements.append(('char', char))
        else:
            i += 1
    
    return elements

def expand_definitions(definiciones):
    expanded = {}
    for nombre, elementos in definiciones:
        tokens = []
        for elem in elementos:
            if elem[0] == "char":
                # Convertir caracteres especiales a secuencias de escape
                char = elem[1]
                if char == '\t':
                    tokens.append('\\t')
                elif char == '\n':
                    tokens.append('\\n')
                elif char == ' ':
                    tokens.append(' ')
                else:
                    tokens.append(char)
            elif elem[0] == "range":
                inicio, fin = elem[1], elem[2]
                tokens.append("|".join(chr(c) for c in range(ord(inicio), ord(fin) + 1)))
        expanded[nombre] = f"({'|'.join(tokens)})"
    return expanded

def clasificar_entrypoints(reglas):
    literales = []
    expresiones = []
    
    for patron, _ in reglas:  # Solo tomamos el patrón, ignoramos la acción
        patron = patron.strip()
        if patron.startswith("'") and patron.endswith("'"):
            literales.append(patron[1:-1])  # Quitar comillas
        else:
            expresiones.append(patron)
    
    return literales, expresiones

def expandir_reglas(reglas, definiciones_expandidas):
    expanded_rules = []
    for patron, accion in reglas:
        tokens = []
        current_token = []
        in_quote = False
        quote_char = None  # Tipo de comilla (' o ")

        # Tokenización del patrón
        for char in patron:
            if char in {'"', '\''}:
                if in_quote and char == quote_char:
                    # Fin de literal
                    tokens.append(f"'{''.join(current_token)}'")  # Forzar comillas simples
                    current_token = []
                    in_quote = False
                    quote_char = None
                else:
                    # Inicio de literal
                    in_quote = True
                    quote_char = char
            elif in_quote:
                current_token.append(char)
            elif char in ('+', '*', '?', '|', '(', ')'):
                if current_token:
                    tokens.append(''.join(current_token))
                    current_token = []
                tokens.append(char)
            elif char.isspace():
                if current_token:
                    tokens.append(''.join(current_token))
                    current_token = []
            else:
                current_token.append(char)

        if current_token:
            tokens.append(''.join(current_token))

        # Procesamiento de tokens
        expanded_tokens = []
        for token in tokens:
            if token.startswith("'") and token.endswith("'"):
                contenido = token[1:-1]
                if contenido in ('+', '-', '*', '/', '(', ')'):  # Operadores
                    expanded_tokens.append(f"('{contenido}')")  # Comillas simples
                else:  # Palabras reservadas
                    expanded_tokens.append(f"({contenido})")  # Sin comillas
            elif token in definiciones_expandidas:
                expanded_tokens.append(definiciones_expandidas[token])
            elif token in ('+', '*', '?'):
                if expanded_tokens:
                    base = expanded_tokens.pop()
                    expanded_tokens.append(f"{base}{token}")
            else:
                expanded_tokens.append(token)

        # Unir tokens
        expanded_pattern = ''.join(expanded_tokens)
        expanded_rules.append((expanded_pattern, accion))
    
    return expanded_rules

archivo_yal = "tokens.yal"
datos = leer_yalex(archivo_yal)

# Mostrar resultados
print("\nHEADER:\n", datos["header"])
print("\nDEFINICIONES:")
for k, v in datos["definiciones"]:
    print(f"{k} = {v}")
print("\nREGLAS:")
for patron, accion in datos["reglas"]:
    print(f"{patron} -> {accion}")
print("\nTRAILER:\n", datos["trailer"])



# Clasificar entrypoints
literales, expresiones = clasificar_entrypoints(datos["reglas"])
print("\nLITERALES:", literales)
print("\nEXPRESIONES:", expresiones)

# Después de leer los datos del archivo YAL
def_expandidas = expand_definitions(datos["definiciones"])
reglas_expandidas = expandir_reglas(datos["reglas"], def_expandidas)

# Mostrar reglas expandidas
print("\nREGLAS EXPANDIDAS:")
for patron, accion in reglas_expandidas:
    print(f"{patron} -> {accion}")


expresiones = []

# 1️⃣ Definiciones (ya vienen entre paréntesis)
expresiones.extend(def_expandidas.values())

# 2️⃣ Reglas expandidas
for patron, _ in reglas_expandidas:
    expresiones.append(patron)  # Ya están formateadas correctamente

# 3️⃣ Guardar
with open("expresion_infix.txt", "w", encoding="utf-8") as f:
    f.write(f"{'|'.join(expresiones)}\n")