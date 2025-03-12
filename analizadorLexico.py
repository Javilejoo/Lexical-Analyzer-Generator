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
    lineas = texto.split('\n')
    
    for linea in lineas:
        linea = linea.strip()
        if linea.startswith('let'):
            # Extraer el identificador y la expresión regular
            partes = linea[3:].strip().split('=', 1)
            if len(partes) == 2:
                ident = partes[0].strip()
                expr = partes[1].strip()
                definiciones.append((ident, expr))
    
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

# Prueba con el archivo yalex
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