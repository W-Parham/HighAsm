# highasm_engine.py
from dataclasses import dataclass, field
from time import sleep
from typing import Any, Iterator, List, Optional, Union, Tuple, Generator,Self

class CST_SyntaxError(Exception):
    """Custom exception for HighAsm syntax violations."""
    pass

# =====================================================================
# THE BASE DATA STRUCTURES (Slotted Specifications)
# =====================================================================
@dataclass(slots=True)
class Token:
    Parent:Optional[Self]
    line: int
    text:Optional[str] = field(default=None)

@dataclass(kw_only=True)
class MathExpressionNode(Token):
    left: Union[str, int, 'MathExpressionNode']                  
    operator: str = field(default="")                   
    right: Optional[Union[str, int, 'MathExpressionNode']] = field(default=None)

@dataclass(kw_only=True)
class LossyCSNode(Token):
    key: Optional[str] = field(default=None)                
    subject: Optional[Union[str, 'LossyCSNode', MathExpressionNode]] = field(default=None)  
    subject_brackets: Optional[list[Union[str, int, MathExpressionNode, 'LossyCSNode']]] = field(default=None)
    subject_Index:Optional[list[str]] = field(default=None)
    operator: Optional[str] = field(default=None)                       
    operator_args: Optional[list[Union[str, int, MathExpressionNode, 'LossyCSNode']]] = field(default=None)
    operator_Index: Optional[list[str]] = field(default=None)
    operator_brackets: Optional[list[Union[str, int, MathExpressionNode, 'LossyCSNode']]] = field(default=None)
    assignment: Optional[Union[str, 'LossyCSNode', MathExpressionNode]] = field(default=None)
    body: Optional[List['LossyCSNode']] = field(default=None)

@dataclass(kw_only=True)
class LiteralToken(Token):
    """Subclass for values that carry evaluated data payload contexts."""
    value:Optional[Any] = field(default=None)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(text={repr(self.text)}, value={repr(self.value)}, L:{self.line})"

# =====================================================================
# THE COMPILER PARSER CORE
# =====================================================================
class LossyCSTParser:
    def __init__(self, source_code: str):
        # Single source of truth for delimiters across the system
        self.delimiters = {" ", ",", "\n", "(", "{", "[", ")", "}", "]", ":", "=", "+", "-", "*", "/", "&", ";"}
        self.math_operators = {'+', '-', '*', '/'}
        
        self.token_stream: Iterator[Tuple[str, int, int]] = self.__lex_generator(source_code)
        
        # Upgraded to a sliding lookahead window list to allow safe lookahead peeking
        self.lookahead_buffer: List[Tuple[str, int, int]] = []
        for _ in range(5):
            self._prime_buffer()

    def _prime_buffer(self):
        """Pulls a single token from the generator into our lookahead pool."""
        try:
            tok = next(self.token_stream)
            self.lookahead_buffer.append(tok)
        except StopIteration:
            pass

    def _consume(self,n:Optional[int] = None) -> Optional[Tuple[str, int, int]]:
        """Consumes the front token and shifts the sliding lookahead window forward."""
        if not self.lookahead_buffer:
            return None
        for _ in range(n or 1):
            consumed = self.lookahead_buffer.pop(0)
            self._prime_buffer()
        return consumed

    def _peek(self, offset: int = 0) -> Optional[Tuple[str, int, int]]:
        """Safely inspects a future token without consuming it or shifting position."""
        if offset < len(self.lookahead_buffer):
            return self.lookahead_buffer[offset]
        return None

    def __lex_generator(self, source: str) -> Iterator[Tuple[str, int, int]]:
        """Continuous spatial coordinate accumulator using centralization shields."""
        currentWord = ""
        word_start_col = 1
        line_idx = 1
        col_idx = 1
        
        in_string = False
        string_quote = ""  

        for char in source:
            if in_string:
                currentWord = f"{currentWord}{char}"
                col_idx += 1
                if char == string_quote:
                    yield currentWord, line_idx, word_start_col
                    currentWord = ""
                    in_string = False
                continue

            if char in ('"', "'"):
                if currentWord:
                    yield currentWord, line_idx, word_start_col
                in_string = True
                string_quote = char
                word_start_col = col_idx
                currentWord = f"{char}"
                col_idx += 1
                continue

            if char == "\n":
                if currentWord:
                    yield currentWord, line_idx, word_start_col
                    currentWord = ""
                yield "\n", line_idx, col_idx
                line_idx += 1
                col_idx = 1
                continue
                
            if char in self.delimiters:
                if currentWord:
                    yield currentWord, line_idx, word_start_col
                    currentWord = ""
                if char != " ":
                    yield char, line_idx, col_idx
                col_idx += 1
                continue
                
            if not currentWord:
                word_start_col = col_idx
            currentWord = f"{currentWord}{char}"
            col_idx += 1
            
        if currentWord:
            yield currentWord, line_idx, word_start_col

    def __call__(self) -> LossyCSNode:

        root_node: LossyCSNode = LossyCSNode(Parent=None, line=-1, subject="Virtual_Root", body=[]) 
        
        # DIRECTION 1: Tracks the structural parent container (Changes ONLY on { and })
        active_parent_node: LossyCSNode = root_node
        # Tracks the active target list we are currently appending lines into
        current_body: list[LossyCSNode] = root_node.body  # type: ignore
        # DIRECTION 2: Tracks the immediate last line node created (Changes on EVERY \n)
        current_node: LossyCSNode = root_node
        while True:
            # 1. Safely check the current token without moving yet
            current_peek = self._peek(0)
            if current_peek is None:
                break  # Safe EOF exit
            
            text, line, col = current_peek
            # --- Structural Blocks ---
            if text == "\n":
                node = LossyCSNode(Parent=active_parent_node, line=line)
                current_body.append(node)
                current_node = node
                self._consume() # Move stream forward past \n
                continue        # Start loop over at the top

            if text == "{":
                current_node.body = []
                active_parent_node = current_node
                current_body = current_node.body
                self._consume() # Move stream forward past {
                continue
            if text == "}":
                if active_parent_node.Parent is not None:
                    active_parent_node = active_parent_node.Parent
                    current_body = active_parent_node.body  # type: ignore
                else:
                    active_parent_node = root_node
                    current_body = root_node.body  # type: ignore
                self._consume()
                continue

            # --- Complex Grammar (Safely handling lookaheads) ---
            if (current_node.key and current_node.subject) is None:
                next_item = self._peek(1)
                # FIX: Check "if next_item" exists FIRST before using [0]
                if next_item and next_item[0] != ":":
                    # Use the returned tuple directly from consume!
                    consumed_key = self._consume()
                    consumed_subject = self._consume()
                    if consumed_key and consumed_subject:
                        current_node.key = consumed_key[0]      # Grab the string text
                        current_node.subject = consumed_subject[0]  # Grab the string text
                    continue
            if current_node.subject is None:
                next_item = self._peek(1)
                # FIX: Check "if next_item" exists FIRST before using [0]
                if next_item and next_item[0] == ":":
                    consumed_subject = self._consume()
                    if consumed_subject:
                        current_node.subject = consumed_subject[0]
                    self._consume() # Consume the colon ":" token too
                    continue
            if (current_node.subject is not None and current_node.operator is None) and text not in self.delimiters:
                current_node.operator = self._consume() # type: ignore
            if text == "[":
                results: Optional[list[Union[str, int, MathExpressionNode, 'LossyCSNode']]] = []
                if current_node.operator is None and current_node.subject is not None: 
                    current_node.subject = results # type: ignore
                elif current_node.operator is not None:
                    current_node.operator = results # type: ignore
                else:
                    raise CST_SyntaxError(f"unexpected bracket at {line},{col}")
                #now it's time to split on the , and deal with them 
                
                continue
            if text == "]":
                pass

        return root_node

                
