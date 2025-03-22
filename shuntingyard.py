# ✅ Shunting Yard FINAL: Diferencia entre literal '+' y operador + correctamente

operadores = {'+', '?', '*', '|', '.', '(', ')'}

def get_precedence(operator):
    precedencia = {
        '|': 1,
        '.': 2,  
        '*': 3,
        '+': 1,
        '?': 1
    }
    return precedencia.get(operator, 0)

especiales = {'\\n', '\\t', '\\r', '\\s', '+', '-', '*', '/', '(', ')', '.', '?', ':', ';'}

# ✅ Tokenización diferenciando literales y operadores

def tokenize_expression(expression):
    """Tokeniza respetando secuencias como \n, literales y palabras"""
    tokens = []
    i = 0
    while i < len(expression):
        # Detectar literal protegido con ''
        if expression[i] == "'":
            i += 1
            literal = ''
            while i < len(expression) and expression[i] != "'":
                literal += expression[i]
                i += 1
            tokens.append(f"'{literal}'")
            i += 1
            continue

        # Detectar secuencias especiales como \n, \t
        if expression[i] == '\\' and i + 1 < len(expression):
            token = expression[i] + expression[i + 1]
            if token in especiales:
                tokens.append(token)
                i += 2
                continue

        # Detectar palabras o identificadores
        if expression[i].isalnum() or expression[i] == '_':
            token = ''
            while i < len(expression) and (expression[i].isalnum() or expression[i] == '_'):
                token += expression[i]
                i += 1
            tokens.append(token)
            continue

        # Detectar operadores y símbolos sueltos
        if expression[i] in operadores:
            tokens.append(expression[i])
            i += 1
            continue

        # Ignorar espacios
        if expression[i].isspace():
            i += 1
            continue

        # Cualquier otro carácter
        tokens.append(expression[i])
        i += 1

    return tokens


def expand_operators(expression):
    expanded_expression = []
    tokens = tokenize_expression(expression)
    i = 0

    while i < len(tokens):
        token = tokens[i]

        # Detectar operador '+' real, ignorar si es un literal
        if token == '+' and not (i > 0 and tokens[i-1].startswith("'")):
            if expanded_expression:
                base = expanded_expression.pop()
                expanded_expression.append(base)
                expanded_expression.append('.')
                expanded_expression.append(base)
                expanded_expression.append('*')
            else:
                raise ValueError("Error: '+' debe estar precedido por un operando.")

        elif token == '?' and not (i > 0 and tokens[i-1].startswith("'")):
            if expanded_expression:
                base = expanded_expression.pop()
                expanded_expression.append('(')
                expanded_expression.append(base)
                expanded_expression.append('|')
                expanded_expression.append('ε')
                expanded_expression.append(')')
            else:
                raise ValueError("Error: '?' debe estar precedido por un operando.")

        else:
            # Concatenación implícita
            if (expanded_expression and expanded_expression[-1] not in operadores and token not in operadores) or \
               (expanded_expression and expanded_expression[-1] in [')', '*'] and token not in operadores):
                expanded_expression.append('.')
            expanded_expression.append(token)

        i += 1

    return ''.join(expanded_expression).replace('()', '')


def ShuntingYard(expresion):
    stack = []
    output = []
    tokens = tokenize_expression(expresion)

    for token in tokens:
        if token in operadores:
            if token == '(':
                stack.append(token)
            elif token == ')':
                while stack and stack[-1] != '(':
                    output.append(stack.pop())
                stack.pop()
            else:
                while stack and get_precedence(stack[-1]) >= get_precedence(token):
                    output.append(stack.pop())
                stack.append(token)
        else:
            output.append(token)

    while stack:
        output.append(stack.pop())

    return ' '.join(output)


def convert_infix_to_postfix(expresion):
    expanded_expression = expand_operators(expresion)
    return ShuntingYard(expanded_expression)


# ✅ Ejemplo de prueba diferenciando literal '+' del operador +
if __name__ == "__main__":
    print("--- Prueba literal '+' ---")
    expresion = "'+'a"
    resultado = convert_infix_to_postfix(expresion)
    print("Postfix:", resultado)

    print("\n--- Prueba operador aaas+ ---")
    expresion = "\\n|j'+'"
    resultado = convert_infix_to_postfix(expresion)
    
    print("Postfix:", resultado)