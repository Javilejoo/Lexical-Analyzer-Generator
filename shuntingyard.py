operadores = {'+', '?', '*', '|', '.', '(', ')', "'"}


def get_precedence(operator):
    precedencia = {
        '|': 2,
        '.': 3,  
        '*': 4,
        '+': 1,
        '?': 1
    }
    return precedencia.get(operator, 0)


def expand_operators(expression):
    expanded_expression = []
    i = 0

    while i < len(expression):
        char = expression[i]

        if char == '+':
            if expanded_expression and expanded_expression[-1] == ')':
                # Extraer la expresión entre paréntesis como base
                sub_expr = ''
                count = 0
                while expanded_expression:
                    token = expanded_expression.pop()
                    if token == ')':
                        count += 1
                    if token == '(':
                        count -= 1
                    sub_expr = token + sub_expr
                    if count == 0:
                        break
                expanded_expression.append(f'({sub_expr}.{sub_expr}*)')
        elif char == '?':
            if expanded_expression:
                base = expanded_expression.pop()
                expanded_expression.append('(')
                expanded_expression.append(base)
                expanded_expression.append('|')
                expanded_expression.append('ε')
                expanded_expression.append(')')
            else:
                raise ValueError("Error: '?' debe estar precedido por un operando.")
        #elif char == '\\':
         #   if i + 1 < len(expression):
          #      expanded_expression.append(f'\\{expression[i+1]}')
           #     i += 2
            #    continue
        elif char == "'":
            j = i + 1
            while j < len(expression) and expression[j] != "'":
                j += 1
            if j < len(expression):
                contenido = expression[i+1:j]
                if len(contenido) == 1:
                    expanded_expression.append(contenido)
                i = j
        else:
            if expanded_expression:
                prev = expanded_expression[-1]
                # Insertar el operador de concatenación ('.') si se cumple alguna de estas condiciones:
                # 1. Si el token previo no es un operador y el actual tampoco lo es.
                # 2. Si el token previo es ')' o '*' y el actual no es operador.
                # 3. Si el token previo es un literal mapeado (placeholder) y el actual es '('.
                if ((prev not in operadores and char not in operadores) or \
                    (prev in [')', '*'] and char not in operadores) or \
                    (prev in placeholder_to_literal and char == '(')):
                    expanded_expression.append('.')
            expanded_expression.append(char)
        
        i += 1

    return ''.join(expanded_expression).replace('()', '')

def concatImplicita(infix):
    resultado = []
    for i in range(len(infix)):
        if i > 0:
            prev = infix[i - 1]
            curr = infix[i]
            # Si el token previo es un operando, o es ')' o uno de los operadores de cierre
            # (por ejemplo, '*' o '+' o '?'), y el token actual es un operando, '(' o el marcador final '#',
            # se inserta el operador de concatenación.
            if ((prev.isalnum() or prev in [')', '*', '+', '?', '#']) and
                (curr.isalnum() or curr == '(' or curr == '#' )):
                resultado.append('.')
            resultado.append(curr)
        else:
            resultado.append(infix[i])
    return "".join(resultado)

def ShuntingYard(expresion):
    stack = []
    output = []
    for char in expresion:
        if char in operadores:
            if char == '(':
                stack.append(char)
            elif char == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                stack.pop()
            else:
                while stack and get_precedence(stack[-1]) >= get_precedence(char):
                    output.append(stack.pop())
                stack.append(char)
        else:
            output.append(char)

    while stack:
        output.append(stack.pop())

    return ''.join(output)

literal_to_placeholder = {
    "+": "\ue000",
    "-": "\ue001",
    "*": "\ue002",
    "/": "\ue003",
    "(": "\ue004",
    ")": "\ue005",
    ".": "\ue006",
    "|": "\ue007",
    "?": "\ue008",
    "\\'": "\ue00b",
    "\\": "\ue00c",
}
    
    
placeholder_to_literal = {v: k for k, v in literal_to_placeholder.items()}

def map_literal_tokens(expresion):
    """
    Recorre la expresión infix y reemplaza cada literal (del tipo: 'X' donde X es un solo carácter)
    por un placeholder único.
    """
    new_expr = ""
    i = 0
    while i < len(expresion):
        if expresion[i] == "'":
            # Caso especial: literal escapado como '\\''
            if i + 3 < len(expresion) and expresion[i+1] == '\\' and expresion[i+2] == "'" and expresion[i+3] == "'":
                char = "\\'"
                if char in literal_to_placeholder:
                    new_expr += literal_to_placeholder[char]
                else:
                    new_expr += "'" + char + "'"
                i += 4
                continue
            # Comprobar que es un literal de un solo caracter: debe tener la forma 'X'
            if i + 2 < len(expresion) and expresion[i+2] == "'":
                char = expresion[i+1]
                if char in literal_to_placeholder:
                    new_expr += literal_to_placeholder[char]
                else:
                    # Si no está mapeado, lo dejamos con sus comillas
                    new_expr += "'" + char + "'"
                i += 3
                continue
        new_expr += expresion[i]
        i += 1
    return new_expr

def restore_literal_tokens(expresion):
    """
    Recorre la expresión (por ejemplo, el resultado postfix) y reemplaza los placeholders
    por sus literales originales, mostrándolos con comillas simples.
    """
    new_expr = ""
    for ch in expresion:
        if ch in placeholder_to_literal:
            new_expr += "'" + placeholder_to_literal[ch] + "'"
        else:
            new_expr += ch
    return new_expr


def convert_infix_to_postfix(expresion):
    """
    Convierte la expresión infix a postfix.
    Se reemplazan secuencias especiales, se mapean los literales a placeholders,
    se aplican las funciones de expansión, concatenación implícita y Shunting Yard,
    y finalmente se restauran los literales.
    """
    # Reemplazar secuencias especiales para evitar interferencias (opcional)
    expresion = expresion.replace("\\n", "ĉ").replace("\\t", "ŵ")
    
    # Mapear los literales a placeholders
    mapped_expr = map_literal_tokens(expresion)
    
    # Aplicar la expansión de operadores y la concatenación implícita
    expanded_expression = expand_operators(mapped_expr)
    expanded_expression = concatImplicita(expanded_expression)
    
    # Aplicar el algoritmo de Shunting Yard (que trabaja a nivel de caracteres)
    postfix = ShuntingYard(expanded_expression)
    postfix = postfix.replace('ĉ', '\\n').replace('ŵ', '\\t')
    
    # Restaurar los literales a su forma original (con comillas)
    postfix = restore_literal_tokens(postfix)
    return postfix
