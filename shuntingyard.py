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
            if expanded_expression:
                base = expanded_expression.pop()
                expanded_expression.append(base)
                expanded_expression.append('.')
                expanded_expression.append(base)
                expanded_expression.append('*')
            else:
                raise ValueError("Error: '+' debe estar precedido por un operando.")

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
    expanded_expression = expand_operators(expresion)
    return ShuntingYard(expanded_expression)


if __name__ == '__main__':
# leer expresiones_modificadas.txt, y hacerle shuttingyard
    with open('expresiones_modificadas.txt') as file:
        expresiones = file.readlines()
        for expresion in expresiones:
            print(convert_infix_to_postfix(expresion.strip()))