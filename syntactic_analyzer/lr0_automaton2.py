import json
import os
import sys
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import List, Set, Dict, Optional, Any, Tuple

# Importar graphviz para generar visualización del autómata
try:
    from graphviz import Digraph
except ImportError:
    print("La biblioteca 'graphviz' no está instalada. Instale con: pip install graphviz")
    Digraph = None

# Importar yapar_parser2
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from yapar_parser2 import parse_yalp_file, parse_yalp_to_json


@dataclass
class Grammar:
    """Clase para representar una gramática libre de contexto"""
    terminals: Set[str] = field(default_factory=set)
    non_terminals: Set[str] = field(default_factory=set)
    productions: Dict[str, List[List[str]]] = field(default_factory=OrderedDict)
    start_symbol: str = None
    ignored_tokens: Set[str] = field(default_factory=set)
    production_list: List[Any] = field(default_factory=list)


@dataclass
class Production:
    """Clase para representar una producción individual"""
    left: str  # Lado izquierdo (no-terminal)
    right: List[str]  # Lado derecho (lista de símbolos)
    number: int  # Número de producción
    
    def __repr__(self) -> str:
        return f"{self.number}: {self.left} -> {' '.join(self.right)}"


@dataclass
class Item:
    """Representa un ítem LR(0) de la forma A -> α•β
    donde A es el lado izquierdo, α es lo que ya se ha visto,
    y β es lo que falta por ver.
    """
    production: Production
    dot_position: int = 0
    
    @property
    def left(self) -> str:
        """Retorna el lado izquierdo de la producción"""
        return self.production.left
    
    @property
    def right(self) -> List[str]:
        """Retorna el lado derecho de la producción"""
        return self.production.right
    
    @property
    def before_dot(self) -> List[str]:
        """Retorna los símbolos antes del punto"""
        return self.production.right[:self.dot_position]
    
    @property
    def after_dot(self) -> List[str]:
        """Retorna los símbolos después del punto"""
        return self.production.right[self.dot_position:]
    
    @property
    def next_symbol(self) -> Optional[str]:
        """Retorna el símbolo inmediatamente después del punto, o None si es ítem completo"""
        if self.dot_position < len(self.production.right):
            return self.production.right[self.dot_position]
        return None
    
    @property
    def is_complete(self) -> bool:
        """Retorna True si el punto está al final (ítem completo)"""
        return self.dot_position >= len(self.production.right)
    
    @property
    def is_kernel(self) -> bool:
        """Retorna True si es un ítem kernel (punto no al inicio o ítem inicial)"""
        return (self.production.number == 0 and self.dot_position == 0) or self.dot_position > 0
    
    def advance(self) -> 'Item':
        """Retorna un nuevo ítem con el punto avanzado una posición"""
        if self.is_complete:
            raise ValueError("No se puede avanzar un ítem completo")
        return Item(self.production, self.dot_position + 1)
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Item):
            return False
        return (self.production.number == other.production.number and 
                self.dot_position == other.dot_position)
    
    def __hash__(self) -> int:
        return hash((self.production.number, self.dot_position))
    
    def __repr__(self) -> str:
        before = ' '.join(self.before_dot)
        after = ' '.join(self.after_dot)
        
        if before and after:
            return f"{self.left} -> {before} . {after}"
        elif before:
            return f"{self.left} -> {before} ."
        elif after:
            return f"{self.left} -> . {after}"
        else:
            return f"{self.left} -> ."


def load_grammar_from_json(json_file: str) -> Grammar:
    """Carga una gramática desde un archivo JSON generado por yapar_parser2"""
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        grammar = Grammar()
        grammar.terminals = set(data['terminals'])
        grammar.non_terminals = set(data['non_terminals'])
        grammar.productions = OrderedDict()
        for nt, rules in data['productions'].items():
            grammar.productions[nt] = rules
        grammar.start_symbol = data['start_symbol']
        grammar.ignored_tokens = set(data.get('ignored_tokens', []))
        
        # Crear la lista numerada de producciones
        grammar.production_list = []
        number = 0
        for nt, rules in grammar.productions.items():
            for rule in rules:
                prod = Production(nt, rule, number)
                grammar.production_list.append(prod)
                number += 1
        
        print(f"Gramática cargada desde {json_file}:")
        print(f"  Terminales: {len(grammar.terminals)}")
        print(f"  No terminales: {len(grammar.non_terminals)}")
        print(f"  Producciones: {len(grammar.production_list)}")
        print(f"  Símbolo inicial: {grammar.start_symbol}")
        
        return grammar
    except Exception as e:
        print(f"Error al cargar la gramática desde {json_file}: {e}")
        return None

def export_to_graphviz(states, transitions, filename="lr0_automaton"):
    """
    states: lista de sets de Item  → estados I0, I1, I2, …
    transitions: dict mapping (from_state, symbol) -> to_state
    filename: nombre base para .dot y .png
    """
    dot = Digraph('LR0', comment='Autómata LR(0)')
    dot.attr(rankdir='LR', fontsize='10')
    dot.attr('node', shape='box', fontname='Courier', fontsize='9')

    # 1) crear un nodo por cada estado
    for i, items in enumerate(states):
        # construye la etiqueta con saltos de línea
        label = f"I{i}\\n"
        for itm in sorted(items, key=str):
            # reemplazamos el espacio por salto de línea interno \l
            label += str(itm).replace(" ", " ") + "\\l"
        dot.node(f"I{i}", label)

    # 2) crear las transiciones
    for (src, sym), dst in transitions.items():
        dot.edge(f"I{src}", f"I{dst}", label=str(sym))

    # 3) renderizar
    dot.render(filename, format='png', cleanup=True)
    print(f"🖼  Grafo generado: {filename}.png")


def augment_grammar(grammar: Grammar) -> None:
    """Aumenta la gramática agregando un nuevo símbolo inicial S' -> S"""
    if not grammar or not grammar.start_symbol:
        return
    
    original_start = grammar.start_symbol
    new_start = f"{original_start}'"
    
    # Agregar nueva producción al inicio
    if new_start not in grammar.productions:
        # Crear el nuevo diccionario ordenado con S' al inicio
        new_productions = OrderedDict()
        new_productions[new_start] = [[original_start]]
        
        # Copiar el resto de producciones
        for nt, rules in grammar.productions.items():
            new_productions[nt] = rules
        
        grammar.productions = new_productions
        
        # Actualizar la lista de no terminales
        grammar.non_terminals.add(new_start)
        
        # Actualizar el símbolo inicial
        grammar.start_symbol = new_start
        
        # Recrear la lista numerada de producciones
        grammar.production_list = []
        for idx, (nt, rules) in enumerate(grammar.productions.items()):
            for rule_idx, rule in enumerate(rules):
                number = idx * 10 + rule_idx  # Numeración que deja espacio entre reglas
                prod = Production(nt, rule, number)
                grammar.production_list.append(prod)
        
        print(f"\nGramática aumentada con: {new_start} -> {original_start}")
        print(f"  Nueva producción inicial: {grammar.production_list[0]}")
    else:
        print(f"\nLa gramática ya estaba aumentada con: {new_start}")


def create_initial_items(grammar: Grammar) -> Set[Item]:
    """Crea los items iniciales a partir del símbolo inicial aumentado"""
    if not grammar or not grammar.production_list:
        return set()
    
    # Buscar todas las producciones que comienzan con el símbolo inicial
    initial_items = set()
    for prod in grammar.production_list:
        if prod.left == grammar.start_symbol:
            initial_item = Item(prod, 0)  # Crear ítem con el punto al inicio
            initial_items.add(initial_item)
    
    print(f"\nItems iniciales creados:")
    for item in sorted(initial_items, key=str):
        print(f"  {item}")
    
    return initial_items


def closure(items: Set[Item], grammar: Grammar) -> Set[Item]:
    """Calcula el cierre de un conjunto de ítems LR(0).
    
    Para cada ítem A -> α•Bβ en el conjunto (donde B es un no terminal):
    - Para cada producción B -> γ en la gramática:
      - Añadir el ítem B -> •γ al conjunto
    - Repetir hasta que no se puedan añadir más ítems.
    
    Args:
        items: Conjunto de ítems LR(0) iniciales
        grammar: Gramática para buscar producciones
    
    Returns:
        Set[Item]: Conjunto cerrado de ítems LR(0)
    """
    # Comenzar con una copia del conjunto original
    result = set(items)
    
    # Crear un conjunto para rastrear los nuevos ítems que se agregan en cada paso
    changed = True
    
    # Continuar hasta que no se agreguen más ítems
    while changed:
        changed = False
        new_items = set()
        
        # Examinar cada ítem actual
        for item in result:
            # Si el ítem no está completo (el punto no está al final)
            if not item.is_complete:
                next_symbol = item.next_symbol
                
                # Si el símbolo después del punto es un no terminal
                if next_symbol in grammar.non_terminals:
                    # Encontrar todas las producciones que tienen este no terminal en el lado izquierdo
                    for prod in grammar.production_list:
                        if prod.left == next_symbol:
                            # Crear un nuevo ítem con el punto al inicio de la producción
                            new_item = Item(prod, 0)
                            
                            # Añadir el nuevo ítem si no está ya en el resultado
                            if new_item not in result:
                                new_items.add(new_item)
                                changed = True
        
        # Agregar los nuevos ítems al conjunto resultado
        result.update(new_items)
    
    return result


def goto(items: Set[Item], symbol: str, grammar: Grammar) -> Set[Item]:
    """Calcula el conjunto de ítems al que se llega desde un estado dado al seguir una transición con un símbolo específico.
    
    El goto se calcula:
    1. Toma todos los ítems A -> α•Xβ donde X es el símbolo dado
    2. Avanza el punto para obtener A -> αX•β
    3. Calcula el cierre de este nuevo conjunto
    
    Args:
        items: Conjunto de ítems LR(0) del estado actual
        symbol: Símbolo para la transición (terminal o no terminal)
        grammar: Gramática para calcular el cierre
    
    Returns:
        Set[Item]: Nuevo conjunto de ítems
    """
    # Encuentra los ítems que tienen el símbolo después del punto
    next_items = set()
    
    for item in items:
        # Si el ítem no está completo y el símbolo después del punto coincide
        if not item.is_complete and item.next_symbol == symbol:
            # Avanza el punto y agrega el nuevo ítem
            next_items.add(item.advance())
    
    # Calcula el cierre del nuevo conjunto
    if next_items:
        return closure(next_items, grammar)
    else:
        return set()


@dataclass
class State:
    """Representa un estado del autómata LR(0)"""
    number: int
    items: Set[Item] = field(default_factory=set)
    transitions: Dict[str, int] = field(default_factory=dict)  # {símbolo: número de estado}
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, State):
            return False
        return self.items == other.items
    
    def __hash__(self) -> int:
        # El hash se basa en los ítems, no en el número del estado
        return hash(frozenset(self.items))


def build_lr0_automaton(grammar: Grammar) -> List[State]:
    """Construye el autómata LR(0) completo para una gramática.
    
    El algoritmo es:
    1. Crea el estado inicial con el cierre del ítem inicial
    2. Para cada estado no procesado y para cada símbolo después del punto:
       a. Calcula el GOTO para obtener un nuevo conjunto de ítems
       b. Si este conjunto no existe como estado, créalo
       c. Agrega una transición del estado actual al nuevo estado con el símbolo
    3. Repite hasta que no haya más estados nuevos
    4. Añade un estado de aceptación final con transición $ desde el estado que tiene el ítem completo S' -> S.
    
    Args:
        grammar: Gramática aumentada
        
    Returns:
        List[State]: Lista de estados del autómata
    """
    # Crear el estado inicial
    initial_items = create_initial_items(grammar)  # Obtener solo el ítem inicial
    initial_state_items = closure(initial_items, grammar)  # Calcular su cierre
    
    # Lista de estados y sus transiciones
    states = [State(0, initial_state_items)]  # Empezar con el estado 0
    
    # Diccionario para mapear conjuntos de ítems a números de estado
    # Esto nos ayuda a no crear estados duplicados
    item_sets_to_state = {}
    item_sets_to_state[frozenset(item.production.number for item in initial_state_items)] = 0
    
    # Cola de estados por procesar
    states_queue = [0]  # Empezar procesando el estado 0
    
    # Procesar todos los estados
    while states_queue:
        # Tomar el siguiente estado a procesar
        current_state_idx = states_queue.pop(0)
        current_state = states[current_state_idx]
        
        # Encontrar todos los símbolos después del punto en los ítems del estado
        symbols_after_dot = set()
        for item in current_state.items:
            if not item.is_complete and item.next_symbol:
                symbols_after_dot.add(item.next_symbol)
        
        # Procesar cada símbolo
        for symbol in symbols_after_dot:
            # Calcular el conjunto de ítems que se obtiene con GOTO
            goto_items = goto(current_state.items, symbol, grammar)
            
            if not goto_items:  # Si no hay ítems, no hay transición
                continue
            
            # Crear una clave para el conjunto de ítems (usando frozenset de números de producción)
            goto_items_key = frozenset(item.production.number for item in goto_items)
            
            # Verificar si este conjunto de ítems ya existe como estado
            if goto_items_key in item_sets_to_state:
                # El estado ya existe, usar su número
                existing_state_idx = item_sets_to_state[goto_items_key]
            else:
                # Crear un nuevo estado
                new_state_idx = len(states)
                new_state = State(new_state_idx, goto_items)
                states.append(new_state)
                item_sets_to_state[goto_items_key] = new_state_idx
                states_queue.append(new_state_idx)  # Añadir a la cola para procesar
                existing_state_idx = new_state_idx
            
            # Añadir la transición desde el estado actual al nuevo/existente
            current_state.transitions[symbol] = existing_state_idx

    
    return states


# Función para mostrar un conjunto de ítems de manera formateada
def print_items_set(items_set, title="Conjunto de ítems"):
    """Imprime un conjunto de ítems LR(0) con un título"""
    print(f"\n{title}:")
    print("="*60)
    
    # Ordenar los ítems primero por símbolo no terminal, luego por número de producción y posición del punto
    def sort_key(item):
        return (item.left, item.production.number, item.dot_position)
    
    items_by_nt = {}
    for item in items_set:
        nt = item.left
        if nt not in items_by_nt:
            items_by_nt[nt] = []
        items_by_nt[nt].append(item)
    
    # Imprimir los ítems agrupados por no terminal, manteniendo un orden determinista
    for nt in sorted(items_by_nt.keys()):  # Ordenar no terminales alfabéticamente
        print(f"\n{nt}:")
        # Ordenar los ítems de manera determinista usando múltiples criterios
        for item in sorted(items_by_nt[nt], key=sort_key):
            print(f"  {item}")
def goto(items: Set[Item], symbol: str, grammar: Grammar) -> Set[Item]:
    # 1) Recoger todos los ítems donde next_symbol == symbol
    next_items = set()
    for item in items:
        if not item.is_complete and item.next_symbol == symbol:
            next_items.add(item.advance())
    
    # 2) Aplicar closure al conjunto movido
    return closure(next_items, grammar) if next_items else set()


def export_to_graphviz(states, filename="lr0_automaton"):
    """
    Exporta el autómata LR(0) a un archivo de imagen usando Graphviz.
    
    Args:
        states: lista de objetos State con los estados del autómata
        filename: nombre base para .dot y .png
    """
    if Digraph is None:
        print("No se puede generar el gráfico: la biblioteca graphviz no está disponible")
        return
        
    dot = Digraph('LR0', comment='Autómata LR(0)')
    dot.attr(rankdir='LR', fontsize='10')
    dot.attr('node', shape='box', fontname='Courier', fontsize='9')

    # 1) crear un nodo por cada estado
    for state in states:
        # construye la etiqueta con saltos de línea
        label = f"I{state.number}\n"
        for itm in sorted(state.items, key=str):
            # reemplazamos el espacio por salto de línea interno \l
            label += str(itm) + "\\l"
        dot.node(f"I{state.number}", label)
    
    # Encontrar el estado de aceptación (donde hay un ítem completo con la producción inicial)
    accept_state_idx = None
    for idx, state in enumerate(states):
        for item in state.items:
            if item.is_complete and item.production.number == 0:  # Producción inicial aumentada
                accept_state_idx = idx
                break
        if accept_state_idx is not None:
            break
            
    # Añadir un nodo especial de aceptación
    if accept_state_idx is not None:
        dot.node("accept", "accept", shape='doublecircle', fontname='Courier', style='filled', fillcolor='lightgreen')
        dot.edge(f"I{accept_state_idx}", "accept", label="$")

    # 2) crear las transiciones normales entre estados
    for state in states:
        for symbol, target_state in state.transitions.items():
            # Saltamos la transición $ que agregamos manualmente arriba
            if symbol == "$" and state.number == accept_state_idx:
                continue
            dot.edge(f"I{state.number}", f"I{target_state}", label=str(symbol))

    # 3) renderizar
    try:
        dot.render(filename, format='png', cleanup=True)
        print(f"Grafo generado: {filename}.png")
    except Exception as e:
        print(f"Error al generar el gráfico: {e}")


# Ejemplo de uso
if __name__ == "__main__":
    # Verificar argumentos de línea de comandos
    if len(sys.argv) > 1:
        yalp_file = sys.argv[1]
    else:
        # Archivo de ejemplo por defecto
        yalp_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "slr-1.yalp")
        print(f"Usando archivo de gramática por defecto: {yalp_file}")
    
    # Verificar si el archivo existe
    if not os.path.exists(yalp_file):
        print(f"Error: No se encuentra el archivo {yalp_file}")
        sys.exit(1)
    
    # Directorio para guardar el JSON generado
    resources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources")
    os.makedirs(resources_dir, exist_ok=True)
    
    # Nombre del archivo JSON basado en el nombre del archivo YALP
    base_name = os.path.basename(yalp_file)
    file_name_without_ext = os.path.splitext(base_name)[0]
    json_file = os.path.join(resources_dir, f"{file_name_without_ext}.json")
    
    # Generar el JSON usando yapar_parser2
    print(f"\nGenerando JSON a partir de {yalp_file}...")
    grammar_obj = parse_yalp_file(yalp_file)
    json_content = parse_yalp_to_json(yalp_file, json_file)
    print(f"JSON generado en: {json_file}")
    
    # Cargar la gramática desde el JSON generado
    grammar = load_grammar_from_json(json_file)
    
    if grammar:
        # Aumentar la gramática
        augment_grammar(grammar)
        
        # Crear los items iniciales
        initial_items = create_initial_items(grammar)
        
        # Mostrar los items iniciales (antes del cierre)
        print("\n" + "="*80)
        print("ITEMS INICIALES (Antes del cierre)")
        print("="*80)
        print_items_set(initial_items, title="Items iniciales")
        
        # Construir el autómata LR(0) completo
        print("\n" + "="*80)
        print("CONSTRUYENDO AUTÓMATA LR(0)")
        print("="*80)
        
        states = build_lr0_automaton(grammar)
        
        # Generar visualización gráfica del autómata
        automaton_filename = os.path.join(resources_dir, f"{file_name_without_ext}_automaton")
        export_to_graphviz(states, filename=automaton_filename)
        
        # Mostrar cada estado con sus items
        print("\n" + "="*80)
        print(f"ESTADOS DEL AUTÓMATA LR(0) (Total: {len(states)} estados)")
        print("="*80)
        
        # Imprimir cada estado con sus items
        for state in states:
            print_items_set(state.items, title=f"ESTADO {state.number}")
            
            print("\n" + "-"*60 + "\n")
            
        # Mostrar la tabla de transiciones
        print("\n" + "="*80)
        print("TABLA DE TRANSICIONES")
        print("="*80)
        print("Transiciones:")
        
        try:
            # Ordenar todos los símbolos (terminales y no terminales) para una presentación consistente
            all_symbols = sorted(grammar.terminals) + sorted(grammar.non_terminals)
            
            # Para cada estado, mostrar sus transiciones
            for state in states:
                for symbol in all_symbols:
                    if symbol in state.transitions:
                        target_state = state.transitions[symbol]
                        if symbol in grammar.terminals:
                            print(f"δ(q{state.number}, '{symbol}') --> q{target_state}")
                        else:
                            print(f"δ(q{state.number}, {symbol}) --> q{target_state}")
        except UnicodeEncodeError:
            # Si hay un error de codificación, usar 'd' en lugar de delta
            # Ordenar todos los símbolos (terminales y no terminales) para una presentación consistente
            all_symbols = sorted(grammar.terminals) + sorted(grammar.non_terminals)
            
            # Para cada estado, mostrar sus transiciones
            for state in states:
                for symbol in all_symbols:
                    if symbol in state.transitions:
                        target_state = state.transitions[symbol]
                        if symbol in grammar.terminals:
                            print(f"d(q{state.number}, '{symbol}') --> q{target_state}")
                        else:
                            print(f"d(q{state.number}, {symbol}) --> q{target_state}")
        
        # Identificar estados de aceptación (aquellos con ítems completos donde la producción es la inicial)
        print("\n" + "="*80)
        print("ESTADO DE ACEPTACIÓN Y PRODUCCIÓN AUMENTADA")
        print("="*80)
        
        # Estado de aceptación
        accept_states = []
        for state in states:
            for item in state.items:
                # Si es un ítem completo y su producción es la inicial aumentada (0)
                if item.is_complete and item.production.number == 0:
                    accept_states.append(state.number)
                    break
        
        if accept_states:
            print(f"Estado de aceptación: q{accept_states[0]}")
        else:
            print("No se encontró estado de aceptación")
            
        # Mostrar producción aumentada
        if grammar.production_list and len(grammar.production_list) > 0:
            initial_production = grammar.production_list[0]
            print(f"Producción aumentada: {initial_production}")
            
            # Mostrar los ítems iniciales relacionados con la producción aumentada
            for item in initial_items:
                print(f"Item inicial: {item}")
