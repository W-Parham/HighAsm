# test.py
from modules.front import CSTLexer, LexerStream, LossyCSNode, MathExpressionNode

def run_test(scenario_name: str, source_code: str):
    print("=" * 70)
    print(f"SCENARIO: {scenario_name}")
    print(f"INPUT:    '{source_code}'")
    print("=" * 70)
    
    # Initialize the pipeline
    parser = CSTLexer(source_code)
    
    try:
        # Run the non-recursive trampoline engine
        cst_root = parser()
        
        # Display the structural tree
        if cst_root:
            print_node(cst_root)
        else:
            print("Output: None (Empty file or skipped expression)")
            
    except Exception as e:
        print(f"❌ COMPILER CRASH: {e}")
    print("\n")

def print_node(node, indent: int = 0):
    """Helper script to pretty-print your custom slotted nodes gracefully."""
    spacing = "  " * indent
    if isinstance(node, LossyCSNode):
        print(f"{spacing}LossyCSNode (Line: {node.line}, Col: {node.column})")
        if node.key:        print(f"{spacing}  ├─ key:        '{node.key}'")
        if node.subject:    
            print(f"{spacing}  ├─ subject:")
            print_node(node.subject, indent + 3)
        if node.operator:   print(f"{spacing}  ├─ operator:   '{node.operator}'")
        if node.assignment: 
            print(f"{spacing}  ├─ assignment:")
            print_node(node.assignment, indent + 3)
        if node.operator_index:
            print(f"{spacing}  ├─ operator_index:")
            for arg in node.operator_index:
                print_node(arg, indent + 3)
    elif isinstance(node, MathExpressionNode):
        print(f"{spacing}MathExpressionNode [Op: '{node.operator}']")
        print(f"{spacing}  ├─ left:")
        print_node(node.left, indent + 2)
        print(f"{spacing}  └─ right:")
        print_node(node.right, indent + 2)
    else:
        # Terminal types (str, int)
        print(f"{spacing}'{node}' ({type(node).__name__})")

# =====================================================================
# THE HIGHASM EXHAUSTIVE TEST SUITE
# =====================================================================
if __name__ == "__main__":
    # Test 1: Traditional memory-scoped variable assignment with math bounds
    run_test(
        scenario_name="Modified Allocation with Math Precedence (PEMDAS)",
        source_code="local count = 5 + 4 * 2"
    )

    # Test 2: Unmodified/bare assignment layout verification
    run_test(
        scenario_name="Bare Assignment without Memory Key",
        source_code="total = 100 / 10"
    )

    # Test 3: HighAsm signature method call format
    run_test(
        scenario_name="Bare Method Invocation",
        source_code="count:increment"
    )

    # Test 4: Pure memory routing macro method calls
    run_test(
        scenario_name="Modified Method Invocation",
        source_code="loan buffer:release"
    )

    # Test 5: Complex parenthetical mathematical overrides
    run_test(
        scenario_name="Parentheses Math Precedence Override",
        source_code="result = (5 + 4) * 2"
    )

    # Test 6: In-line array indexing/dynamic conditional switches
    run_test(
        scenario_name="Method Call with Inline Bracket Arguments",
        source_code="local target:method[cmp, replace]"
    )
