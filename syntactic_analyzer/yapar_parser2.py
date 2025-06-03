import json
from dataclasses import dataclass
from typing import Dict, List, Set

@dataclass
class Grammar:
    terminals: Set[str]
    non_terminals: Set[str]
    productions: Dict[str, List[List[str]]]
    start_symbol: str
    ignored_tokens: Set[str]

    def to_dict(self):
        """Convert the Grammar object to a dictionary for JSON serialization"""
        return {
            'terminals': list(self.terminals),
            'non_terminals': list(self.non_terminals),
            'productions': self.productions,
            'start_symbol': self.start_symbol,
            'ignored_tokens': list(self.ignored_tokens)
        }

class YalpParser:
    def __init__(self):
        self.terminals = set()
        self.non_terminals = set()
        self.productions = {}
        self.start_symbol = None
        self.ignored_tokens = set()
    
    def is_whitespace(self, c):
        """Check if a character is whitespace"""
        return c in [' ', '\t', '\n', '\r']
    
    def is_alpha(self, c):
        """Check if a character is a letter"""
        return ('a' <= c <= 'z') or ('A' <= c <= 'Z')
    
    def is_identifier_char(self, c):
        """Check if a character can be part of an identifier"""
        return self.is_alpha(c) or c == '_'
    
    def parse_file(self, file_path: str) -> Grammar:
        """Parse a .yalp file and extract grammar elements"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Process the file contents
        content = self.remove_comments(content)
        self.process_content(content)
        
        # Create and return Grammar object
        return Grammar(
            terminals=self.terminals,
            non_terminals=self.non_terminals,
            productions=self.productions,
            start_symbol=self.start_symbol,
            ignored_tokens=self.ignored_tokens
        )
    
    def remove_comments(self, content: str) -> str:
        """Remove C-style comments /* ... */ from the content"""
        result = []
        i = 0
        while i < len(content):
            # Check for comment start
            if i + 1 < len(content) and content[i] == '/' and content[i + 1] == '*':
                # Skip until comment end
                i += 2
                while i + 1 < len(content) and not (content[i] == '*' and content[i + 1] == '/'):
                    i += 1
                if i + 1 < len(content):  # Skip the closing */
                    i += 2
            else:
                result.append(content[i])
                i += 1
        
        return ''.join(result)
    
    def process_content(self, content: str) -> None:
        """Process the content to extract grammar elements"""
        i = 0
        while i < len(content):
            # Skip whitespace
            while i < len(content) and self.is_whitespace(content[i]):
                i += 1
            
            if i >= len(content):
                break
            
            # Process token declaration
            if content[i:i+7] == '%token ' and i + 7 < len(content):
                i += 7  # Skip '%token '
                i = self.process_token_declaration(content, i)
            
            # Process production rules
            elif self.is_identifier_char(content[i]):
                identifier_start = i
                while i < len(content) and self.is_identifier_char(content[i]):
                    i += 1
                
                identifier = content[identifier_start:i]
                
                # Skip whitespace
                while i < len(content) and self.is_whitespace(content[i]):
                    i += 1
                
                # Check if this is a production rule
                if i < len(content) and content[i] == ':':
                    i += 1  # Skip ':'
                    i = self.process_production_rule(content, i, identifier)
                # Do NOT increment i here; process_production_rule returns the correct next index
                # else:
                #     i += 1  # (Removed: this caused skipping the first char of next non-terminal)
            else:
                i += 1  # Skip other characters
    
    def process_token_declaration(self, content: str, start_idx: int) -> int:
        """Process a token declaration line and return the next index to process"""
        i = start_idx
        # Skip leading whitespace
        while i < len(content) and self.is_whitespace(content[i]):
            i += 1
        
        while i < len(content) and content[i] != '\n':
            # Extract token name
            token_start = i
            while i < len(content) and not self.is_whitespace(content[i]) and content[i] != '\n':
                i += 1
            
            token_name = content[token_start:i].strip()
            if token_name:  # Only add non-empty tokens
                self.terminals.add(token_name)
            
            # Skip whitespace between tokens
            while i < len(content) and self.is_whitespace(content[i]) and content[i] != '\n':
                i += 1
        
        return i
    
    def process_production_rule(self, content: str, start_idx: int, non_terminal: str) -> int:
        """Process a production rule and return the next index to process"""
        self.non_terminals.add(non_terminal)
        
        # If this is the first non-terminal, set it as the start symbol
        if self.start_symbol is None:
            self.start_symbol = non_terminal
        
        i = start_idx
        productions_for_nt = []
        current_production = []
        
        # Skip whitespace before first production
        while i < len(content) and self.is_whitespace(content[i]):
            i += 1
        
        while i < len(content) and content[i] != ';':
            # Handle OR operator
            if content[i] == '|':
                if current_production:  # Add the current production if not empty
                    productions_for_nt.append(current_production)
                    current_production = []
                i += 1  # Skip '|'
                
                # Skip whitespace after |
                while i < len(content) and self.is_whitespace(content[i]):
                    i += 1
            
            # Handle whitespace between symbols
            elif self.is_whitespace(content[i]):
                i += 1
            
            # Handle symbol (terminal or non-terminal)
            elif self.is_identifier_char(content[i]):
                symbol_start = i
                while i < len(content) and self.is_identifier_char(content[i]):
                    i += 1
                
                symbol = content[symbol_start:i]
                if symbol:  # Only add non-empty symbols
                    current_production.append(symbol)
            else:
                i += 1  # Skip other characters
        
        # Add the last production if not empty
        if current_production:
            productions_for_nt.append(current_production)
        
        # Store the productions for this non-terminal
        if productions_for_nt:
            self.productions[non_terminal] = productions_for_nt
        
        # Skip the semicolon
        if i < len(content) and content[i] == ';':
            i += 1
        
        return i

def parse_yalp_file(file_path: str) -> Grammar:
    """Parse a .yalp file and return a Grammar object"""
    parser = YalpParser()
    return parser.parse_file(file_path)

def parse_yalp_to_json(file_path: str, output_json_path: str = None) -> str:
    """Parse a .yalp file and convert to JSON format"""
    grammar = parse_yalp_file(file_path)
    grammar_json = json.dumps(grammar.to_dict(), indent=4)
    
    if output_json_path:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            f.write(grammar_json)
    
    return grammar_json

# Example usage
if __name__ == "__main__":
    import sys
    import os
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        grammar = parse_yalp_file(file_path)
        
        # Print the grammar in the desired format
        print(f"Grammar(\n    terminals       = {grammar.terminals},")
        print(f"    non_terminals   = {grammar.non_terminals},")
        print(f"    productions     = {{")        
        for nt, prods in grammar.productions.items():
            print(f"        '{nt}': {prods},")
        print(f"    }},")
        print(f"    start_symbol    = '{grammar.start_symbol}',")
        print(f"    ignored_tokens  = {grammar.ignored_tokens}")
        print(")")
        
        # Save the grammar as a JSON file in the resources directory
        base_name = os.path.basename(file_path)
        file_name_without_ext = os.path.splitext(base_name)[0]
        json_file_path = os.path.join(os.path.dirname(__file__), 'resources', f"{file_name_without_ext}.json")
        
        # Ensure the resources directory exists
        os.makedirs(os.path.dirname(json_file_path), exist_ok=True)
        
        # Save the grammar to JSON file
        json_content = parse_yalp_to_json(file_path, json_file_path)
        print(f"\nGrammar saved to: {json_file_path}")
    else:
        print("Please provide a path to a .yalp file")
