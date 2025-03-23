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
        elif char == "'" and i + 2 < len(expression) and expression[i+2] == "'":
            expanded_expression.append(' ')
            i += 3
            continue
        else:
            if (expanded_expression and expanded_expression[-1] not in operadores and char not in operadores) or \
               (expanded_expression and expanded_expression[-1] in [')', '*'] and char not in operadores):
                expanded_expression.append('.')
            expanded_expression.append(char)

        i += 1

    return ''.join(expanded_expression).replace('()', '')


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
    expresion = expresion.replace("' '", ' ').replace("\\n", "ĉ").replace("\\t", "ŵ") 
    expanded_expression = expand_operators(expresion)
    postfix = ShuntingYard(expanded_expression)
    return postfix.replace('ĉ', '\\n').replace('ŵ', '\\t')

if __name__ == '__main__':
    infix = r"(' '|\n|\t)"
    print('infix',infix)
    postfix = convert_infix_to_postfix(infix)
    print('postfix',postfix) 
    infix = "(a|b|c)"
    print('infix',infix)
    postfix = convert_infix_to_postfix(infix)
    print('postfix',postfix) 

