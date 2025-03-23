def leerER(file):
    with open(file, 'r') as f:
        contenido = f.read()
    return contenido
    