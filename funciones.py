def leerER(file):
    with open(file, 'r') as f:
        contenido = f.read()
    return contenido
    


print(repr(leerER("output/infix_final.txt"))) 
