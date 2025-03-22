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

    # Identificar la última regla que contiene { return ... }
    ultima_regla = ''
    for linea in lineas:
        if '{' in linea and 'return' in linea:
            ultima_regla = linea.strip()

    if not ultima_regla:
        return '', yalex_code  # No encontró ninguna regla con acción

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







yalex = 'yalexs/slr-1.yal'
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
