# Analizador Sintáctico SLR(1)

Un analizador sintáctico completo que implementa el algoritmo SLR(1) para gramáticas libres de contexto. Este analizador se integra con un analizador léxico para procesar código fuente completo.

## 🚀 Características

- **Parser SLR(1)** completo con construcción automática de tablas
- **Cálculo de conjuntos FIRST y FOLLOW**
- **Construcción de autómata LR(0)**
- **Detección automática de conflictos**
- **Integración con analizador léxico**
- **Análisis paso a paso detallado**
- **Soporte para múltiples gramáticas**

## 📁 Estructura del Proyecto

```
syntactic_analyzer/
├── README.md                    # Este archivo
├── syntax_analyzer.py           # Analizador principal (punto de entrada)
├── lr0_automaton.py            # Construcción del autómata LR(0)
├── slr_table.py                # Construcción de tabla SLR(1) y parser
├── yapar_parser.py             # Parser de gramáticas .yalp
├── first_follow.py             # Cálculo de conjuntos FIRST y FOLLOW
├── resources/                  # Gramáticas de ejemplo
│   ├── slr-1.yalp             # Gramática aritmética simple
│   ├── slr-2.yalp             # Gramática con paréntesis
│   ├── slr-3.yalp             # Gramática extendida
│   ├── slr-4.yalp             # Gramática compleja
│   └── tokens_output_2.txt    # Ejemplo de tokens del léxico
└── tests/                     # Scripts de prueba
    ├── test_first_follow.py   # Pruebas de FIRST/FOLLOW
    ├── test_lr0_automaton.py  # Pruebas del autómata
    └── test_slr_table.py      # Pruebas de la tabla SLR
```

## 🛠️ Instalación

### Requisitos
- Python 3.7 o superior
- No requiere librerías externas (solo biblioteca estándar)

### Configuración
```bash
# Clonar o descargar el proyecto
cd syntactic_analyzer

# Verificar que Python esté instalado
python3 --version
```

## 📖 Uso

### Uso Básico

El analizador sintáctico se ejecuta desde `syntax_analyzer.py` y requiere dos archivos:

1. **Archivo de gramática** (`.yalp`)
2. **Archivo de tokens** (salida del analizador léxico)

```bash
python3 syntax_analyzer.py <grammar.yalp> <tokens_file.txt>
```

### Ejemplo Completo

```bash
# Analizar tokens con la gramática aritmética simple
python3 syntax_analyzer.py resources/slr-1.yalp resources/tokens_output_2.txt
```

### Salida Esperada

```
Cargando gramática desde: resources/slr-1.yalp
✓ Analizador sintáctico cargado correctamente

Leyendo tokens desde: resources/tokens_output_2.txt
✓ Se leyeron 5 tokens
✓ Se mapearon 5 tokens para análisis sintáctico

============================================================
REPORTE DE ANÁLISIS SINTÁCTICO
============================================================

📊 ESTADÍSTICAS:
   Tokens léxicos leídos: 5
   Tokens para sintáctico: 5
   Pasos de análisis: 14

🎯 RESULTADO:
   ✅ ÉXITO: Análisis exitoso

🔍 TOKENS LÉXICOS (primeros 10):
    1. ID('x')
    2. PLUS('+')
    3. ID('y')
    4. TIMES('*')
    5. ID('z')

🔧 TOKENS SINTÁCTICOS:
   ID PLUS ID TIMES ID
```

## 📝 Formato de Archivos

### Archivo de Gramática (.yalp)

```yacc
%token ID PLUS TIMES LPAREN RPAREN

%%

expression:
    expression PLUS term
  | term
;

term:
    term TIMES factor
  | factor
;

factor:
    LPAREN expression RPAREN
  | ID
;
```

### Archivo de Tokens

Formato de salida del analizador léxico:
```
ID          'x'
PLUS        '+'
ID          'y'
TIMES       '*'
ID          'z'
```

## 🧪 Pruebas

### Ejecutar Todas las Pruebas

```bash
# Pruebas de FIRST y FOLLOW
cd tests
python3 test_first_follow.py

# Pruebas del autómata LR(0)
python3 test_lr0_automaton.py

# Pruebas de la tabla SLR(1)
python3 test_slr_table.py
```

### Probar Gramáticas Específicas

```bash
# Probar gramática aritmética simple
python3 syntax_analyzer.py resources/slr-1.yalp resources/tokens_output_2.txt

# Probar gramática con paréntesis
python3 syntax_analyzer.py resources/slr-2.yalp resources/tokens_output_2.txt
```

## 🔧 Configuración Avanzada

### Mapeo de Tokens

El analizador mapea automáticamente tokens del léxico al sintáctico. Para personalizar el mapeo, edita la función `map_token_name()` en `syntax_analyzer.py`:

```python
token_mapping = {
    'IDENTIFIER': 'ID',
    'INTEGER': 'NUMBER',
    'LEFT_PAREN': 'LPAREN',
    # Agregar más mapeos aquí
}
```

### Tokens Ignorados

Para ignorar tokens específicos (como whitespace), modifica `should_ignore_token()`:

```python
ignored_tokens = {
    'WS',           # Whitespace
    'COMMENT',      # Comentarios
    'NEWLINE',      # Saltos de línea
    # Agregar más tokens a ignorar
}
```

## 📊 Análisis Detallado

### Ver Conjuntos FIRST y FOLLOW

```bash
cd tests
python3 test_first_follow.py
```

### Ver Construcción del Autómata

```bash
cd tests
python3 test_lr0_automaton.py
```

### Ver Tabla SLR(1) Completa

```bash
cd tests
python3 test_slr_table.py
```
