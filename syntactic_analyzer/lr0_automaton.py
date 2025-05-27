from collections import OrderedDict

class Grammar:
    """Clase para representar una gramática libre de contexto"""
    def __init__(self):
        self.tokens = []           # Lista de terminales
        self.non_terminals = []    # Lista de no-terminales
        self.productions = OrderedDict()  # Dict: {no_terminal: [reglas]}
        self.start_symbol = None   # Símbolo inicial
        self.ignored_tokens = []   # Tokens a ignorar
        self.production_list = []  # Lista numerada de producciones para reducciones

class Production:
    """Clase para representar una producción individual"""
    def __init__(self, left, right, number):
        self.left = left    # Lado izquierdo (no-terminal)
        self.right = right  # Lado derecho (lista de símbolos)
        self.number = number  # Número de producción
    
    def __repr__(self):
        return f"{self.number}: {self.left} → {' '.join(self.right)}"

class Item:
    """
    Representa un ítem LR(0) de la forma A → α•β
    donde A es el lado izquierdo, α es lo que ya se ha visto,
    y β es lo que falta por ver.
    """
    def __init__(self, production, dot_position=0):
        """
        Args:
            production: Objeto Production de yapar_parser
            dot_position: Posición del punto (•) en la producción
        """
        self.production = production
        self.dot_position = dot_position
        
    @property
    def left(self):
        """Retorna el lado izquierdo de la producción"""
        return self.production.left
    
    @property
    def right(self):
        """Retorna el lado derecho de la producción"""
        return self.production.right
    
    @property
    def before_dot(self):
        """Retorna los símbolos antes del punto"""
        return self.production.right[:self.dot_position]
    
    @property
    def after_dot(self):
        """Retorna los símbolos después del punto"""
        return self.production.right[self.dot_position:]
    
    @property
    def next_symbol(self):
        """Retorna el símbolo inmediatamente después del punto, o None si es ítem completo"""
        if self.dot_position < len(self.production.right):
            return self.production.right[self.dot_position]
        return None
    
    @property
    def is_complete(self):
        """Retorna True si el punto está al final (ítem completo)"""
        return self.dot_position >= len(self.production.right)
    
    @property
    def is_kernel(self):
        """
        Retorna True si es un ítem kernel.
        Un ítem es kernel si:
        - Es el ítem inicial S' → •S
        - O si el punto no está al inicio (dot_position > 0)
        """
        return (self.production.number == 0 and self.dot_position == 0) or self.dot_position > 0
    
    def advance(self):
        """Retorna un nuevo ítem con el punto avanzado una posición"""
        if self.is_complete:
            raise ValueError("No se puede avanzar un ítem completo")
        return Item(self.production, self.dot_position + 1)
    
    def __eq__(self, other):
        """Dos ítems son iguales si tienen la misma producción y posición del punto"""
        if not isinstance(other, Item):
            return False
        return (self.production.number == other.production.number and 
                self.dot_position == other.dot_position)
    
    def __hash__(self):
        """Hash basado en el número de producción y la posición del punto"""
        return hash((self.production.number, self.dot_position))
    
    def __repr__(self):
        """Representación string del ítem"""
        before = ' '.join(self.before_dot)
        after = ' '.join(self.after_dot)
        
        if before and after:
            return f"{self.left} → {before} • {after}"
        elif before:
            return f"{self.left} → {before} •"
        elif after:
            return f"{self.left} → • {after}"
        else:
            return f"{self.left} → •"
    
    def __str__(self):
        return self.__repr__()

class State:
    """
    Representa un estado en el autómata LR(0).
    Un estado es un conjunto de ítems LR(0).
    """
    def __init__(self, items, state_id=None):
        """
        Args:
            items: Conjunto (set) de objetos Item
            state_id: Identificador único del estado
        """
        self.items = frozenset(items)  # Inmutable para poder usar como clave
        self.id = state_id
        self.transitions = {}  # {symbol: state_id}
        
    @property
    def kernel_items(self):
        """Retorna solo los ítems kernel del estado"""
        return {item for item in self.items if item.is_kernel}
    
    @property
    def non_kernel_items(self):
        """Retorna los ítems no-kernel del estado"""
        return {item for item in self.items if not item.is_kernel}
    
    def get_symbols_after_dot(self):
        """Retorna todos los símbolos que aparecen después del punto en los ítems"""
        symbols = set()
        for item in self.items:
            if not item.is_complete:
                symbols.add(item.next_symbol)
        return symbols
    
    def get_complete_items(self):
        """Retorna los ítems completos del estado"""
        return {item for item in self.items if item.is_complete}
    
    def add_transition(self, symbol, target_state_id):
        """Agrega una transición al estado"""
        self.transitions[symbol] = target_state_id
    
    def __eq__(self, other):
        """Dos estados son iguales si tienen los mismos ítems"""
        if not isinstance(other, State):
            return False
        return self.items == other.items
    
    def __hash__(self):
        """Hash basado en los ítems del estado"""
        return hash(self.items)
    
    def __repr__(self):
        items_str = '\n  '.join(str(item) for item in sorted(self.items, key=str))
        return f"State {self.id}:\n  {items_str}"
    
    def __str__(self):
        return self.__repr__()

class LR0Automaton:
    """
    Representa el autómata LR(0) completo.
    Contiene todos los estados y las transiciones entre ellos.
    """
    def __init__(self, grammar):
        """
        Args:
            grammar: Objeto Grammar de yapar_parser (debe estar aumentada)
        """
        self.grammar = grammar
        self.states = []  # Lista de objetos State
        self.state_map = {}  # {frozenset(items): state_id}
        self.initial_state_id = None
        
    def add_state(self, items):
        """
        Agrega un nuevo estado al autómata o retorna el ID si ya existe.
        
        Args:
            items: Conjunto de ítems para el estado
            
        Returns:
            int: ID del estado (nuevo o existente)
        """
        items_frozen = frozenset(items)
        
        # Si el estado ya existe, retornar su ID
        if items_frozen in self.state_map:
            return self.state_map[items_frozen]
        
        # Crear nuevo estado
        state_id = len(self.states)
        state = State(items, state_id)
        
        self.states.append(state)
        self.state_map[items_frozen] = state_id
        
        return state_id
    
    def get_state(self, state_id):
        """Retorna el estado con el ID dado"""
        if 0 <= state_id < len(self.states):
            return self.states[state_id]
        return None
    
    def add_transition(self, from_state_id, symbol, to_state_id):
        """Agrega una transición entre estados"""
        from_state = self.get_state(from_state_id)
        if from_state:
            from_state.add_transition(symbol, to_state_id)
    
    def get_symbols(self):
        """Retorna todos los símbolos (terminales y no-terminales) de la gramática"""
        return set(self.grammar.tokens) | set(self.grammar.non_terminals)
    
    def print_automaton(self):
        """Imprime el autómata de forma legible"""
        print(f"\n=== AUTÓMATA LR(0) ===")
        print(f"Estados: {len(self.states)}")
        print(f"Estado inicial: {self.initial_state_id}")
        
        for state in self.states:
            print(f"\n{state}")
            
            if state.transitions:
                print("  Transiciones:")
                for symbol, target_id in sorted(state.transitions.items()):
                    print(f"    {symbol} → Estado {target_id}")
    
    def get_action_items(self, state_id):
        """
        Retorna los ítems que determinan las acciones para un estado.
        Separa entre ítems completos (reduce) y no completos (shift).
        """
        state = self.get_state(state_id)
        if not state:
            return [], []
        
        complete_items = []
        shift_items = []
        
        for item in state.items:
            if item.is_complete:
                complete_items.append(item)
            else:
                shift_items.append(item)
        
        return shift_items, complete_items
    
    def to_dict(self):
        """Convierte el autómata a un diccionario para serialización"""
        return {
            'states': [
                {
                    'id': state.id,
                    'items': [str(item) for item in state.items],
                    'kernel_items': [str(item) for item in state.kernel_items],
                    'transitions': state.transitions
                }
                for state in self.states
            ],
            'initial_state': self.initial_state_id,
            'num_states': len(self.states)
        }

def closure(items, grammar):
    """
    Calcula el cierre de un conjunto de ítems.
    
    Para cada ítem A → α•Bβ en items:
    - Para cada producción B → γ en la gramática:
      - Agregar B → •γ al conjunto
    
    Args:
        items: Conjunto (set) de objetos Item
        grammar: Objeto Grammar
        
    Returns:
        set: Conjunto cerrado de ítems
    """
    # Comenzar con el conjunto original
    closure_set = set(items)
    
    # Repetir hasta que no se agreguen más ítems
    changed = True
    while changed:
        changed = False
        items_to_add = set()
        
        # Para cada ítem en el conjunto actual (ordenado para determinismo)
        for item in sorted(closure_set, key=lambda x: (x.production.number, x.dot_position)):
            # Si el ítem no está completo y el siguiente símbolo es un no-terminal
            if not item.is_complete and item.next_symbol in grammar.non_terminals:
                non_terminal = item.next_symbol
                
                # Para cada producción de ese no-terminal
                if non_terminal in grammar.productions:
                    for rule in grammar.productions[non_terminal]:
                        # Encontrar la producción correspondiente
                        for prod in grammar.production_list:
                            if prod.left == non_terminal and prod.right == rule:
                                # Crear nuevo ítem con el punto al inicio
                                new_item = Item(prod, 0)
                                
                                # Si el ítem no está en el conjunto, agregarlo
                                if new_item not in closure_set:
                                    items_to_add.add(new_item)
                                    changed = True
                                break
        
        # Agregar todos los nuevos ítems
        closure_set.update(items_to_add)
    
    return closure_set

def goto(items, symbol, grammar):
    """
    Calcula GOTO(items, symbol).
    
    GOTO(I, X) = closure({A → αX•β | A → α•Xβ ∈ I})
    
    Args:
        items: Conjunto de ítems (estado)
        symbol: Símbolo de transición
        grammar: Objeto Grammar
        
    Returns:
        set: Nuevo conjunto de ítems después de la transición
    """
    goto_set = set()
    
    # Para cada ítem en el conjunto (ordenado para determinismo)
    for item in sorted(items, key=lambda x: (x.production.number, x.dot_position)):
        # Si el símbolo después del punto es el símbolo buscado
        if not item.is_complete and item.next_symbol == symbol:
            # Avanzar el punto
            new_item = item.advance()
            goto_set.add(new_item)
    
    # Calcular el cierre del conjunto resultante
    if goto_set:
        return closure(goto_set, grammar)
    
    return set()

def build_lr0_automaton(grammar):
    """
    Construye el autómata LR(0) completo para la gramática dada.
    
    Algoritmo:
    1. Crear el estado inicial con el ítem S' → •S
    2. Para cada estado no procesado:
       - Para cada símbolo X donde GOTO(estado, X) no es vacío:
         - Crear o encontrar el estado destino
         - Agregar la transición
    
    Args:
        grammar: Objeto Grammar (debe estar aumentada)
        
    Returns:
        LR0Automaton: Autómata LR(0) construido
    """
    # Verificar que la gramática esté aumentada
    if not grammar.production_list or grammar.production_list[0].left != grammar.start_symbol:
        raise ValueError("La gramática debe estar aumentada antes de construir el autómata")
    
    # Crear el autómata
    automaton = LR0Automaton(grammar)
    
    # Crear el ítem inicial: S' → •S
    initial_production = grammar.production_list[0]
    initial_item = Item(initial_production, 0)
    
    # Calcular el cierre del ítem inicial
    initial_items = closure({initial_item}, grammar)
    
    # Crear el estado inicial
    initial_state_id = automaton.add_state(initial_items)
    automaton.initial_state_id = initial_state_id
    
    # Cola de estados por procesar
    states_to_process = [initial_state_id]
    processed_states = set()
    
    print(f"\nConstruyendo autómata LR(0)...")
    print(f"Estado inicial creado con {len(initial_items)} ítems")
    
    # Procesar estados hasta que no queden más
    while states_to_process:
        current_state_id = states_to_process.pop(0)
        
        if current_state_id in processed_states:
            continue
        
        processed_states.add(current_state_id)
        current_state = automaton.get_state(current_state_id)
        
        print(f"\nProcesando Estado {current_state_id}...")
        
        # Obtener todos los símbolos después del punto (ordenados para determinismo)
        symbols = sorted(current_state.get_symbols_after_dot())
        
        # Para cada símbolo, calcular GOTO
        for symbol in symbols:
            # Calcular GOTO(current_state.items, symbol)
            goto_items = goto(current_state.items, symbol, grammar)
            
            if goto_items:
                # Agregar o encontrar el estado destino
                target_state_id = automaton.add_state(goto_items)
                
                # Agregar la transición
                automaton.add_transition(current_state_id, symbol, target_state_id)
                
                print(f"  Transición con '{symbol}' → Estado {target_state_id}")
                
                # Si es un estado nuevo, agregarlo a la cola
                if target_state_id not in processed_states:
                    states_to_process.append(target_state_id)
    
    print(f"\nAutómata construido con {len(automaton.states)} estados")
    
    return automaton

def print_closure_steps(items, grammar):
    """
    Imprime los pasos del cálculo del cierre (útil para debugging).
    
    Args:
        items: Conjunto inicial de ítems
        grammar: Objeto Grammar
    """
    print("\nCalculando CLOSURE:")
    print("Ítems iniciales:")
    for item in items:
        print(f"  {item}")
    
    closure_set = set(items)
    added_items = []
    
    changed = True
    iteration = 0
    
    while changed:
        changed = False
        iteration += 1
        items_to_add = set()
        
        for item in closure_set:
            if not item.is_complete and item.next_symbol in grammar.non_terminals:
                non_terminal = item.next_symbol
                
                if non_terminal in grammar.productions:
                    for rule in grammar.productions[non_terminal]:
                        for prod in grammar.production_list:
                            if prod.left == non_terminal and prod.right == rule:
                                new_item = Item(prod, 0)
                                
                                if new_item not in closure_set:
                                    items_to_add.add(new_item)
                                    added_items.append((iteration, item, new_item))
                                    changed = True
                                break
        
        closure_set.update(items_to_add)
    
    if added_items:
        print("\nÍtems agregados por CLOSURE:")
        current_iteration = 0
        for iteration, trigger_item, new_item in added_items:
            if iteration != current_iteration:
                current_iteration = iteration
                print(f"\n  Iteración {iteration}:")
            print(f"    Por '{trigger_item.next_symbol}' en {trigger_item}")
            print(f"    → Agregar: {new_item}")
    else:
        print("\nNo se agregaron ítems adicionales")
    
    return closure_set

def analyze_automaton(automaton):
    """
    Analiza el autómata y proporciona estadísticas útiles.
    
    Args:
        automaton: LR0Automaton construido
        
    Returns:
        dict: Diccionario con estadísticas
    """
    stats = {
        'num_states': len(automaton.states),
        'num_transitions': 0,
        'terminals_used': set(),
        'non_terminals_used': set(),
        'shift_states': 0,
        'reduce_states': 0,
        'shift_reduce_states': 0
    }
    
    for state in automaton.states:
        # Contar transiciones
        stats['num_transitions'] += len(state.transitions)
        
        # Recopilar símbolos usados
        for symbol in state.transitions:
            if symbol in automaton.grammar.tokens:
                stats['terminals_used'].add(symbol)
            else:
                stats['non_terminals_used'].add(symbol)
        
        # Clasificar estados
        has_shift = False
        has_reduce = False
        
        for item in state.items:
            if item.is_complete:
                has_reduce = True
            elif item.next_symbol in automaton.grammar.tokens:
                has_shift = True
        
        if has_shift and has_reduce:
            stats['shift_reduce_states'] += 1
        elif has_shift:
            stats['shift_states'] += 1
        elif has_reduce:
            stats['reduce_states'] += 1
    
    return stats

def find_conflicts(automaton, follow_sets):
    """
    Encuentra conflictos shift/reduce y reduce/reduce en el autómata.
    
    Args:
        automaton: LR0Automaton construido
        follow_sets: Diccionario con conjuntos FOLLOW
        
    Returns:
        dict: Diccionario con información sobre conflictos
    """
    conflicts = {
        'shift_reduce': [],
        'reduce_reduce': []
    }
    
    for state in automaton.states:
        # Obtener ítems completos (reduce)
        reduce_items = [item for item in state.items if item.is_complete]
        
        if reduce_items:
            # Obtener símbolos de shift
            shift_symbols = set()
            for item in state.items:
                if not item.is_complete and item.next_symbol in automaton.grammar.tokens:
                    shift_symbols.add(item.next_symbol)
            
            # Verificar conflictos shift/reduce
            for reduce_item in reduce_items:
                if reduce_item.left in follow_sets:
                    follow = follow_sets[reduce_item.left]
                    conflict_symbols = shift_symbols & follow
                    
                    if conflict_symbols:
                        conflicts['shift_reduce'].append({
                            'state': state.id,
                            'reduce_item': reduce_item,
                            'symbols': conflict_symbols
                        })
            
            # Verificar conflictos reduce/reduce
            if len(reduce_items) > 1:
                for i in range(len(reduce_items)):
                    for j in range(i + 1, len(reduce_items)):
                        item1, item2 = reduce_items[i], reduce_items[j]
                        
                        if item1.left in follow_sets and item2.left in follow_sets:
                            follow1 = follow_sets[item1.left]
                            follow2 = follow_sets[item2.left]
                            conflict_symbols = follow1 & follow2
                            
                            if conflict_symbols:
                                conflicts['reduce_reduce'].append({
                                    'state': state.id,
                                    'item1': item1,
                                    'item2': item2,
                                    'symbols': conflict_symbols
                                })
    
    return conflicts

# Funciones auxiliares para debugging

def print_item_details(item):
    """Imprime detalles de un ítem"""
    print(f"Ítem: {item}")
    print(f"  Producción #{item.production.number}")
    print(f"  Antes del punto: {item.before_dot}")
    print(f"  Después del punto: {item.after_dot}")
    print(f"  Símbolo siguiente: {item.next_symbol}")
    print(f"  ¿Completo?: {item.is_complete}")
    print(f"  ¿Kernel?: {item.is_kernel}")

def print_state_details(state):
    """Imprime detalles de un estado"""
    print(f"\n{state}")
    print(f"  Ítems kernel: {len(state.kernel_items)}")
    print(f"  Ítems no-kernel: {len(state.non_kernel_items)}")
    print(f"  Símbolos después del punto: {state.get_symbols_after_dot()}")
    print(f"  Ítems completos: {len(state.get_complete_items())}")
    
    if state.transitions:
        print("  Transiciones:")
        for symbol, target in state.transitions.items():
            print(f"    {symbol} → Estado {target}")