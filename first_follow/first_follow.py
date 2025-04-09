def cal_first(s, productions, memo={}):
    if s in memo:
        return memo[s]

    first = set()

    for production in productions[s]:
        for i, symbol in enumerate(production):
            if symbol == 'ε':
                first.add('ε')
                break
            elif not symbol.isupper():  # Terminal
                first.add(symbol)
                break
            else:  # No terminal
                f = cal_first(symbol, productions, memo)
                first.update(f - {'ε'})
                if 'ε' not in f:
                    break
        else:
            # Si todos los símbolos en la producción derivan ε
            first.add('ε')

    memo[s] = first
    return first


def cal_follow(productions, first_dict):
    follow = {nt: set() for nt in productions}

    # Agregar $ al símbolo inicial
    start_symbol = list(productions.keys())[0]
    follow[start_symbol].add('$')

    updated = True
    while updated:
        updated = False
        for head, rules in productions.items():
            for rule in rules:
                for i, symbol in enumerate(rule):
                    if symbol in productions:  # solo no terminales
                        follow_before = follow[symbol].copy()

                        # Caso 1: símbolo seguido por otros
                        if i + 1 < len(rule):
                            next_sym = rule[i + 1]

                            # Si next es terminal
                            if next_sym not in productions:
                                follow[symbol].add(next_sym)
                            else:
                                first_of_next = first_dict[next_sym]
                                follow[symbol].update(first_of_next - {'ε'})

                                if 'ε' in first_of_next:
                                    follow[symbol].update(follow[head])
                        else:
                            # Caso 2: símbolo al final de producción
                            follow[symbol].update(follow[head])

                        if follow_before != follow[symbol]:
                            updated = True
    return follow



def parse_grammar(file_path):
    productions = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            left, right = line.split("->")
            left = left.strip()
            alternatives = right.split('|')
            rules = []
            for alt in alternatives:
                symbols = alt.strip().split()
                rules.append(symbols)
            productions[left] = rules
    return productions


def main():
    grammar_path = "first_follow/grammar.txt"
    productions = parse_grammar(grammar_path)

    first = {}
    for non_terminal in productions:
        first[non_terminal] = cal_first(non_terminal, productions)

    print("***** FIRST *****")
    for lhs, rhs in first.items():
        print(lhs, ":", rhs)

    follow = cal_follow(productions, first)

    print("\n***** FOLLOW *****")
    for lhs, rhs in follow.items():
        print(lhs, ":", rhs)


if __name__ == "__main__":
    main()