from collections import namedtuple,deque
from dataclasses import dataclass, field
from typing import Any, Iterator, List, Optional, Union,Tuple,Generator

class CST_SyntaxError(Exception):
    """Custom exception for HighAsm syntax violations."""
    pass
# =====================================================================
# THE BASE CLASS
# =====================================================================
@dataclass(slots=True)
class Token:
    """Slotted base class ensuring line and column track properly across all nodes."""
    line: int                     # Line number for tracking error diagnostics
    column: int                   # Starting column location for compiler warning!

# =====================================================================
# RECURSIVE MATHEMATICAL NODES
# =====================================================================
@dataclass(slots=True, kw_only=True)
class MathExpressionNode(Token):
    """A recursive mathematical structure that supports infinite equations."""
    left: Union[str, int, 'MathExpressionNode']                  
    operator: str                    
    right: Optional[Union[str, int, 'MathExpressionNode']] = None 

# =====================================================================
# THE LOSSY CONCRETE SYNTAX TREE NODE
# =====================================================================
@dataclass(slots=True, kw_only=True)
class LossyCSNode(Token):
    """
    A comprehensive lossy CST node designed to hold every syntactic 
    token, delimiter, and modifier without dropping data.
    """
    # --- Structural Components ---
    key: Optional[str] = None                     # e.g., 'local', 'loan', 'pass', 'data'                  
    subject: Optional[Union[str, 'LossyCSNode', MathExpressionNode]] = None  
    sub_index: Optional['LossyCSNode'] = None      # e.g., '[type]', 'Type[T]'      
    operator: Optional[str] = None               
    assignment: Optional[Union['LossyCSNode', MathExpressionNode]] = None     
    
    # Dynamic field factories cleanly isolated at the bottom
    operator_index: List[Union['LossyCSNode', str, int, MathExpressionNode]] = field(default_factory=list) 
    body: Optional[List['LossyCSNode']] = field(default_factory=list)


Frame = namedtuple("Frame", ["generator", "context"])

class LexerStream:
    def __init__(self, source: str):
        self.source = source
        # Turn your original execution logic into a stateful iterator stream
        self.iterator = self.__lex_generator()
        self.buffer: deque[Tuple[str, int]] = deque()

    def __lex_generator(self) -> Iterator[Tuple[str, int]]:
        """ Your original token extraction logic, untouched """
        currentWord = ""
        for index, char in enumerate(self.source):
            if char in [" ",",", "\n", "(", "{", "[", ")", "}", "]", ":"]:
                # === ADD THE CHECK HERE ===
                if char == ":":
                    if index > 0 and self.source[index - 1] == " ":
                        raise CST_SyntaxError(f"Syntax Error at index {index}: Spaces are not allowed before a colon ':'.")
                if currentWord:
                    yield currentWord, index - len(currentWord)
                    currentWord = ""
                if char != " ": 
                    yield char, index
                continue
            currentWord = f"{currentWord}{char}"
        if currentWord:
            yield currentWord, len(self.source) - len(currentWord)

    def __fill_buffer(self, count: int):
        """ Dynamically pulls tokens from the yield engine only when needed """
        while len(self.buffer) <= count:
            try:
                next_token = next(self.iterator)
                self.buffer.append(next_token)
            except StopIteration:
                break # Stream is fully exhausted
    def peek(self, n: int) -> Tuple[str, int]:
        # If n = 3, this calls __fill_buffer(4)
        # The generator yields until the deque has exactly 4 items sitting on the shelf
        self.__fill_buffer(n)
        # Return the item at index [3] without popping it from the deque
        return self.buffer[n]

    def __next__(self):
        if len(self.buffer) == 0:
            return next(self.iterator)
        return self.buffer.popleft()

class CSTLexer:
    def __init__(self,source:str):
        self.stream = LexerStream(source)
        self.precedence = {
            '+': 1, '-': 1,
            '*': 2, '/': 2,
            '^': 3
        }

    def _get_token_meta(self, offset: int = 0) -> tuple[int, int]:
        """
        Safely extracts line and column metadata from the lookahead stream window.
        Returns a flat tuple of (line, column_index).
        """
        if self.stream:
            tok_data = self.stream.peek(offset)
            if tok_data:
                # tok_data is a Tuple[str, int] (e.g., ("local", 6))
                # Unpack the token string run and its absolute character index
                _, absolute_char_index = tok_data
                
                # Replace this with your line-counting log if you want, 
                # but passing the raw integer position works perfectly for now!
                return 1, absolute_char_index
                
        return 1, 0


    # CORRECTED HINT: Yields a Generator, receives Any back from send(), returns a terminal math node
    def parse_primary_gen(self) -> Generator[Generator[Any, Any, Any], Any, Union[str, int, MathExpressionNode]]:
        if not self.stream:
            raise RuntimeError("Parser execution attempted without an attached stream context.")
            
        token, _ = self.stream.peek(0)
        line, col = self._get_token_meta(0)

        if token == "(":
            self.stream.__next__()  # Consume '('
            expr = yield self.parse_math_expr_gen(0)
            next_tok, _ = self.stream.peek(0)
            if next_tok == ")":
                self.stream.__next__()  # Consume ')'
            return expr

        tok, _ = self.stream.__next__()
        if tok.isdigit():
            return int(tok)
        return tok

    # CORRECTED HINT: Yields a Generator, receives Any, returns MathExpressionNode or terminal primitives
    def parse_math_expr_gen(self, min_prec: int = 0) -> Generator[Generator[Any, Any, Any], Any, Union[str, int, MathExpressionNode]]:
        line, col = self._get_token_meta(0)
        left = yield self.parse_primary_gen()

        while True:
            if not self.stream: break
            try:
                op, _ = self.stream.peek(0)
            except (StopIteration, IndexError):
                break

            if op not in self.precedence or self.precedence[op] < min_prec:
                break

            self.stream.__next__()  
            right = yield self.parse_math_expr_gen(self.precedence[op] + 1)
            left = MathExpressionNode(line=line, column=col, left=left, operator=op, right=right)

        return left

    # CORRECTED HINT: Yields a Generator, receives Any, returns your clean LossyCSNode
    def parse_statement_gen(self) -> Generator[Generator[Any, Any, Any], Any, Optional[LossyCSNode]]:
        if not self.stream:
            return None
            
        try:
            t0, _ = self.stream.peek(0)
        except (StopIteration, IndexError):
            return None 

        line, col = self._get_token_meta(0)

        try: t1, _ = self.stream.peek(1)
        except (StopIteration, IndexError): t1 = None

        try: t2, _ = self.stream.peek(2)
        except (StopIteration, IndexError): t2 = None

        key_val = None
        subject_val = None

        if t1 and t2 and t2 in [":", "="]:
            key_val, _ = self.stream.__next__()
            subject_val, _ = self.stream.__next__()
        elif t1 and t1 in [":", "="]:
            subject_val, _ = self.stream.__next__()
        else:
            expr_tree = yield self.parse_math_expr_gen(0)
            return LossyCSNode(line=line, column=col, subject=expr_tree)

        pivot_op, _ = self.stream.__next__() 

        if pivot_op == "=":
            assignment_tree = yield self.parse_math_expr_gen(0)
            return LossyCSNode(
                line=line, column=col, key=key_val, subject=subject_val,
                operator="=", assignment=assignment_tree
            )

        elif pivot_op == ":":
            method_name, _ = self.stream.__next__()
            op_idx = []
            
            try: next_tok, _ = self.stream.peek(0)
            except (StopIteration, IndexError): next_tok = None
            
            if next_tok == "[":
                self.stream.__next__()  
                while True:
                    tok, _ = self.stream.peek(0)
                    if tok == "]":
                        self.stream.__next__()  
                        break
                    val = yield self.parse_primary_gen()
                    op_idx.append(LossyCSNode(line=line, column=col, subject=val))
                    if self.stream.peek(0) == ",":
                        self.stream.__next__()

            return LossyCSNode(
                line=line, column=col, key=key_val, subject=subject_val, operator=":",
                assignment=LossyCSNode(line=line, column=col, subject=method_name),
                operator_index=op_idx
            )

        return None

    # =====================================================================
    # THE CALLABLE ENTRY POINT
    # =====================================================================
    def __call__(self) -> Optional[LossyCSNode]: 
        stack = [self.parse_statement_gen()]
        value = None
        while stack:
            top = stack[-1]
            try:
                if isinstance(value, Exception):
                    raise value
                sub = top.send(value)
                stack.append(sub)
                value = None 
            except StopIteration as e:
                stack.pop()
                value = e.value
                
        return value
