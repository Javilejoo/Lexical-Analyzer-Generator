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
            # ✅ Buscar la base completa entre paréntesis si la hay
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
                expanded_expression.append(f'{sub_expr}.{sub_expr}*')
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
        elif char == '\\':
            if i + 1 < len(expression):
                expanded_expression.append(f'\\{expression[i+1]}')
                i += 2
                continue
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
            if (expanded_expression and expanded_expression[-1] not in operadores and char not in operadores) or \
               (expanded_expression and expanded_expression[-1] in [')', '*'] and char not in operadores):
                expanded_expression.append('.')
            expanded_expression.append(char)

        i += 1

    return ''.join(expanded_expression).replace('()', '')  # r

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


def convert_infix_to_postfix(expresion):
    # Eliminar comillas simples manualmente (ej: 'a' → a)
    nueva_expresion = []
    i = 0
    n = len(expresion)
    
    while i < n:
        if expresion[i] == "'":
            # Buscar la siguiente comilla
            j = i + 1
            while j < n and expresion[j] != "'":
                j += 1
            if j < n:
                contenido = expresion[i+1:j]
                if len(contenido) == 1:
                    nueva_expresion.append(contenido)
                i = j
            else:
                nueva_expresion.append(expresion[i])
        else:
            nueva_expresion.append(expresion[i])
        i += 1
    
    expresion = ''.join(nueva_expresion)
    # Resto del procesamiento
    expresion = expresion.replace("\\n", "ĉ").replace("\\t", "ŵ") # r
    expanded_expression = expand_operators(expresion)
    expanded_expression = concatImplicita(expanded_expression)
    postfix = ShuntingYard(expanded_expression)
    return postfix.replace('ĉ', '\\n').replace('ŵ', '\\t') # r

if __name__ == '__main__':
    infix = r"(' '|\n|\t)"
    print('infix',infix)
    postfix = convert_infix_to_postfix(infix)
    print('postfix',postfix) 
    infix = "('a'|'c'|' ')"
    print('infix',infix)
    postfix = convert_infix_to_postfix(infix)
    print('postfix',postfix) 
    infix = "((A|B|a|b)(((0|1)|(A|B|a|b))*))#"
    print('infix',infix)
    postfix = convert_infix_to_postfix(infix)
    print('postfix',postfix) 

