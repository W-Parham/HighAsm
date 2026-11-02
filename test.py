# test.py
import tkinter as tk
from tkinter import ttk
from modules.front import LossyCSTParser, LossyCSNode, MathExpressionNode

def print_cst_tree(nodes: list[LossyCSNode], indent: str = ""):
    for i, node in enumerate(nodes):
        is_last = (i == len(nodes) - 1)
        marker = "└── " if is_last else "├── "
        child_indent = indent + ("    " if is_last else "│   ")
        
        details = []
        if node.key: details.append(f"key='{node.key}'")
        if node.subject: details.append(f"subject='{node.subject}'")
        if node.operator: details.append(f"operator='{node.operator}'")
        
        if node.assignment:
            if isinstance(node.assignment, MathExpressionNode):
                details.append("assignment=MathExpressionNode(...)")
            else:
                details.append(f"assignment='{node.assignment}'")
        
        attr_string = " | ".join(details)
        print(f"{indent}{marker}LossyCSNode [Line {node.line}, Col {node.column:02d}] ──> {attr_string}")
        
        if isinstance(node.assignment, MathExpressionNode):
            expr: MathExpressionNode = node.assignment
            math_marker = "    └── " if not node.body else "    ├── "
            print(f"{child_indent}{math_marker}└── MathExpressionNode [Line {expr.line}, Col {expr.column:02d}]: left='{expr.left}' {expr.operator} right='{expr.right}'")

        if node.body:
            print_cst_tree(node.body, child_indent)

if __name__ == "__main__":
    highasm_code_snippet = """
    local author:int64 = "allic,matt"
    count:method
    local math_result:int64 = 5 + 5
    matrix grid:Space = "unsupported_keyword_test"
    
    try {
        main: {
            local ref:Cursor = 42
        }
    }
    """

    parser = LossyCSTParser(highasm_code_snippet)
    cst = parser.parse()
    print_cst_tree(cst)

