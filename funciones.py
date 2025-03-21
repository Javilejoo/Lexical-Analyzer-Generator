def leerER(file):
    with open(file, "r", encoding='utf=8') as f:
        for line in f:
            print('La expresion regular es: ',line)
        return line