def leerER(file):
    with open(file, 'r', encoding ='utf-8') as f:
        contenido = f.read()
    return contenido
    