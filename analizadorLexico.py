import re

def leer_yalex(archivo):
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()

    # Eliminar comentarios (* ... *)
    contenido = re.sub(r'\(\*.*?\*\)', '', contenido, flags=re.DOTALL)

    # Extraer header (primera ocurrencia de { ... })
    header_match = re.search(r'^\s*\{(.*?)\}', contenido, re.DOTALL)
    header = header_match.group(1).strip() if header_match else ""

    # Extraer trailer (última ocurrencia de { ... })
    trailer_match = re.findall(r'\{(.*?)\}', contenido, re.DOTALL)
    trailer = trailer_match[-1].strip() if trailer_match else ""

    # Extraer definiciones (let ident = regexp)
    definiciones = re.findall(r'let\s+(\w+)\s*=\s*(.+)', contenido)

    # Extraer reglas dentro de "rule gettoken ="
    reglas = []
    
    # Encuentra la sección de reglas
    rule_section_match = re.search(r'rule\s+gettoken\s*=(.*?)(?=\{\s*print)', contenido, re.DOTALL)
    
    if rule_section_match:
        rule_section = rule_section_match.group(1).strip()
        
        # Dividir por '|' pero teniendo cuidado con los paréntesis y otros caracteres
        rule_parts = []
        current_part = ""
        for line in rule_section.split('\n'):
            line = line.strip()
            if line.startswith('|'):
                if current_part:
                    rule_parts.append(current_part)
                current_part = line[1:].strip()
            else:
                current_part += " " + line.strip()
        
        if current_part:
            rule_parts.append(current_part)
        
        # Procesar cada parte
        for part in rule_parts:
            if not part.strip():
                continue
            
            # Buscar la acción entre llaves
            action_match = re.search(r'\{(.*?)\}', part, re.DOTALL)
            if action_match:
                action = action_match.group(1).strip()
                pattern = part[:action_match.start()].strip()
                reglas.append((pattern, action))

    return {
        "header": header,
        "trailer": trailer,
        "definiciones": definiciones,
        "reglas": reglas
    }

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