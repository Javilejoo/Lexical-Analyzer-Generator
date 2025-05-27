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