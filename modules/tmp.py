from dataclasses import dataclass, field



# =====================================================================
# 1. LEXER (Your original bracket-stack engine remains untouched)
# =====================================================================
def lex(source: str) -> list[dict]:
    tokens = []
    bracket_stack = []
    block_start_index = 0
    word_start = None
    
    current_line = 1
    current_column = 1
    transform_to_operator = False
    
    bracket_meanings = {
        '(': 'ARG_GROUP',
        '[': 'BRACKET_GROUP',
        '{': 'BODY_GROUP'
    }
    matching_bracket = {']': '[', '}': '{', ')': '('}
    open_brackets = set(matching_bracket.values())
    close_brackets = set(matching_bracket.keys())
    
    i = 0
    length = len(source)
    
    while i < length:
        char = source[i]
        next_column = current_column + 1
        next_line = current_line
        if char == '\n':
            next_line = current_line + 1
            next_column = 1
            
        if char == '/' and i + 1 < length and source[i + 1] == '/':
            if not bracket_stack and word_start is not None:
                val = source[word_start:i].strip()
                t_type = "OPERATOR" if transform_to_operator else "ID"
                tokens.append({"type": t_type, "value": val})
                word_start = None
                transform_to_operator = False
            
            while i < length and source[i] != '\n' and source[i] not in close_brackets:
                if source[i] == '\n':
                    current_line += 1
                    current_column = 1
                else:
                    current_column += 1
                i += 1
            continue 
            
        if bracket_stack:
            if char in open_brackets:
                bracket_stack.append({
                    "char": char, "index": i, "line": current_line, "column": current_column
                })
            elif char in close_brackets:
                if bracket_stack[-1]["char"] == matching_bracket[char]:
                    bracket_stack.pop()
                    if not bracket_stack:
                        opening_type = bracket_meanings[source[block_start_index]]
                        inner_value = source[block_start_index + 1 : i].strip()
                        tokens.append({"type": opening_type, "value": inner_value})
                else:
                    bracket_stack.pop()
            
            current_line = next_line
            current_column = next_column
            i += 1
            continue
            
        if char in open_brackets:
            if word_start is not None:
                val = source[word_start:i].strip()
                t_type = "OPERATOR" if transform_to_operator else "ID"
                tokens.append({"type": t_type, "value": val})
                word_start = None
                transform_to_operator = False
                
            bracket_stack.append({
                "char": char, "index": i, "line": current_line, "column": current_column
            })
            block_start_index = i
            current_line = next_line
            current_column = next_column
            i += 1
            continue
            
        if char == '\n':
            if word_start is not None:
                val = source[word_start:i].strip()
                t_type = "OPERATOR" if transform_to_operator else "ID"
                tokens.append({"type": t_type, "value": val})
                word_start = None
                transform_to_operator = False
            tokens.append({"type": "NEWLINE", "value": "\n"})
            current_line = next_line
            current_column = next_column
            i += 1
            continue
            
        if char.isalnum() or char == '_':
            if word_start is None:
                word_start = i
        else:
            if word_start is not None:
                val = source[word_start:i].strip()
                t_type = "OPERATOR" if transform_to_operator else "ID"
                tokens.append({"type": t_type, "value": val})
                word_start = None
                transform_to_operator = False
                
            if char == ':':
                transform_to_operator = True
            elif not char.isspace():
                tokens.append({"type": "SYMBOL", "value": char})
                
        current_line = next_line
        current_column = next_column
        i += 1
        
    if word_start is not None:
        val = source[word_start:].strip()
        t_type = "OPERATOR" if transform_to_operator else "ID"
        tokens.append({"type": t_type, "value": val})
        
        # CRITICAL CHECK FOR UNCLOSED BRACKETS
    if bracket_stack:
        offending_bracket = bracket_stack[-1]
        unclosed_char = offending_bracket["char"]
        group_type = bracket_meanings[unclosed_char]
        expected_closer = { '(': ')', '[': ']', '{': '}' }[unclosed_char]
        
        # FIXED: Now correctly injects expected_closer into the diagnostic output text
        raise SyntaxError(
            f"\nHighAsm Compile Error: Unclosed bracket block!\n"
            f"The opening '{unclosed_char}' ({group_type}) on line {offending_bracket['line']}, "
            f"column {offending_bracket['column']} was never closed.\n"
            f"Expected a matching '{expected_closer}' before the end of the file."
        )
        
    return tokens


# =====================================================================
# 2. STRUCTURALIZER (Updated to yield agnostic visual shapes)
# =====================================================================
@dataclass(slots=True)
class structualizer:
    source: str = field(default="")
    tokens: list[dict] = field(default_factory=list, init=False)
    token_index: int = field(default=0, init=False)

    def __post_init__(self):
        self.tokens = lex(self.source)

    def __iter__(self):
            """Acts as a true native generator object, streaming structural role blocks 
            lazily one-by-one when invoked inside compiler loops or recursive passes.
            """
            for index,token in enumerate(self.tokens):
                if token == "NEWLINE":
                    continue
                