# Lexical-Analyzer-Generator
implementación de un generador de analizadores léxicos, el cual, tomando como entrada un archivo escrito en YALex, generará un analizador léxico que será capaz de reconocer los tokens especificados, o en su defecto, errores léxicos. 

# 📄 Proyecto: Generador de AFD desde archivo .yal

Este proyecto toma como entrada un archivo `.yal` (archivo tipo Yalex con definiciones y reglas de tokens) y genera:  
✅ Árboles de expresión  
✅ Tabla de followpos  
✅ AFD  
✅ AFD minimizado  

---

## 📂 Estructura del Proyecto

├── parser_yal.py # Parser que lee el archivo .yal y genera las expresiones regulares procesadas ├── ERtoAFD.py # Código que construye el árbol, calcula firstpos, lastpos, followpos y genera el AFD ├── output/ # Carpeta donde se guardan los árboles y gráficos generados (afd.png, afd_min.png, expression_tree.png) ├── archivo.yal # Archivo de entrada .yal con las definiciones y reglas ├── README.md # (Este archivo)

yaml
Copiar
Editar

---

## 🛠 Requisitos

- Python 3.8 o superior
- Librerías necesarias:
```bash
pip install graphviz
🚀 ¿Cómo ejecutar el proyecto?
1️⃣ Paso 1: Procesar el archivo .yal
Este paso lee las definiciones y reglas, y genera el archivo con la expresión regular infix expandida.

bash
Copiar
Editar
python parser_yal.py archivo.yal
📂 Salida esperada:

Un archivo output/final_infix.txt que contiene la expresión regular infix expandida y lista para procesar.

2️⃣ Paso 2: Construir el AFD y generar los árboles
Este paso toma la expresión expandida y genera:

El árbol de expresión

Tabla de followpos

AFD completo

AFD minimizado

Imágenes de los autómatas y el árbol en la carpeta output/

bash
Copiar
Editar
python ERtoAFD.py
📂 Salida esperada (carpeta output/):

expression_tree.png

afd.png

afd_min.png

Tabla de followpos impresa en consola

📈 Resultado
✅ Gráficos de los autómatas y el árbol
✅ AFD minimizado correctamente
✅ Simulación de cadenas sobre el AFD

📚 Nota
Asegúrate de que el .yal esté bien estructurado con las secciones:

php-template
Copiar
Editar
{header}
let <definiciones>
rule tokens =
    <reglas>
{trailer}
El parser expande correctamente los rangos y literales.

👨‍💻 Ejemplo de uso completo:
bash
Copiar
Editar
python parser_yal.py archivo.yal
python ERtoAFD.py
Luego revisa la carpeta output/ para ver el AFD y el árbol generado.

📩 Autor
Si tienes dudas o mejoras, ¡no dudes en contribuir o preguntar!

go
Copiar
Editar

✅ **Listo para copiar y pegar en tu `README.md`**  
✅ Incluye estructura de carpetas, comandos, ejemplos y secciones claras