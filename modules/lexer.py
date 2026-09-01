from dataclasses import dataclass

from modules.plugin import PluginManager,Plugin

from dataclasses import dataclass
import regex as re
from GeneralModules.scopeManager import FrameInfo, UniversalStack, YieldItem
from modules.sourceErrors import InvalidSyntax, StructureError
from typing import  Any, List, Union
from modules.abstraction_module import StatementToken,MathToken

MAINPATTERN = r"""
(?(DEFINE)
    (?<name> <[^>]+> | "[^"]+"| [^\s\(\)\[\]\{\}:;=\.]+ )
    (?<subscript> \[ (?: (?&name) |(?&subscript) | [^\[\]] )* \] )
    (?<parens>    \( (?> [^()]+   | (?&parens)    )* \) )
    (?<scope_inner>(?:[^{}]+|\{(?&scope_inner) \})*)
    (?<boundary>  \s* [;}\n] | \s+ (?&name) | \s* $ )
)
^ \s*
# 1. THE HEADER (Address Discovery)
(?: (?P<header_context>(?&name))\s+)?
(?:
    # PATH A: The 'Paren Expression'
    (?= \( )\( (?P<subject_expr> (?> (?&parens) | [^()] )* ) \)
    |
    # PATH B: The 'Standard Declaration'
    (?P<subject>(?&name))
    (?: \.(?P<index> (?&name)(?: \. (?&name) )* ))?
    # This matches '[' then captures everything UNTIL the matching ']'
    (?: \[ (?P<subject_index> (?>(?&subscript) | [^\[\]] )* ) \] )?
)?
# 2. THE LOGIC CHAIN (The Pivot Zone)
(?:
    : 
    (?> 
        (?P<qualifier>(?&name))
        (?>
            (?:\[(?P<qualifier_index> (?> (?&subscript) | [^\[\]]*) ) \])?
            (?:\((?P<arg_guts> (?> (?&parens) | [^()] )* )\) )?
        )?
    )
)?+ \s*

# 3. THE JUNCTION (The Atomic Switch)
(?> 
    (?:
        # PATH A: Assignment
        (?= \s* = )
        = \s* 
        (?P<assignment_val> .* )
        |
        # PATH B: Scope Body
        (?= \s* \{ )
        \{
            (?P<main_body> (?&scope_inner) )
        \} (?: \s* else \s* \{
            (?P<else_body> (?&scope_inner))
        \})?
        |
        # PATH C: The Landing
        (?= \s* [;\n] | $ )
    )
)?
\s* ;? \s*
"""

class StreamingLexer:
    def __init__(self, main_source: str):
        # 1. Root frame is your main source code
        self.stack = UniversalStack(root_payload=main_source)
        self.line = 1
        self.column = 1

    def peek_char(self) -> str:
        """Uses StackFrame's internal peek register for zero-cost lookahead."""
        try:
            yield_item = self.stack.current_node.peek()
            return yield_item.value
        except StopIteration:
            return ""

    def read_char(self) -> str:
        """Consumes the next character through UniversalStack."""
        try:
            ch, frame_info = self.stack.next()
            if ch == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
            return ch
        except StopIteration:
            return ""

    def handle_import(self, imported_source_code: str):
        """Pushes a new stream frame directly onto the execution stack."""
        self.stack.push_frame(
            block_payload=imported_source_code,
            engine=iter(imported_source_code)
        )
    def __iter__(self) -> str:
        

