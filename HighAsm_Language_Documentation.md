# HighAsm: Language Specification & Architecture Blueprint

**Status:** Technical Draft / Prior Art  
**License:** Public Domain  

---

## Abstract & Overview

**HighAsm** is a general-purpose systems programming language designed as a highly efficient hybrid system, combining the speed and predictability of compiled execution with dynamic modularity. Built around a **pure method-centric model**, HighAsm eliminates syntax bloat by expressing primitives, mathematical logic, control flow, and object operations as direct method invocations.

### Key Architectural Pillars
1. **Zero-Cost Memory Safety & Scope Control:** Multi-tier memory allocation semantics (`local`, `loan`, `pass`, `data`) combined with compiler-managed references and Cursors.
2. **Method-Centric Syntax:** Uniform syntax model where control flow, boolean evaluation, and data operations use object/primitive methods.
3. **Pre-Main Singletons (`construct`):** Deterministic, static auto-initialization prior to `main()` execution.
4. **Dynamic Dynamic ABI Stability:** Swift-inspired runtime lookup via immutable `.slot` metadata sections in dynamic library binaries (`.linklib`).

---

## 1. Type System & Declaration Syntax

HighAsm enforces a strict, static type system. Primitive types specify explicit bit-widths. Variables must be declared before use and adhere to explicit assignment constraints.

### Primitive Types
* `char` — 1-byte character literal
* `int8` .. `int64` — Signed integers (8 to 64-bit precision)
* `float8` .. `float64` — Floating-point values (8 to 64-bit precision)
* `Reference[T]` — Managed pointer type auto-dereferenced on access rebindable
* `Cursor[T]` -- used for arrays (this is a unsafe indexing mehism) - non-rebindable 


### Declarations & Functions
```highasm
    // Primitive Declarations
    declare_keyword var:[type] = value
    [key] c:char = 'A'
    [key] count:int64 = 100
    [key] pi:float64 = 3.14

    // Instantiation
    declare_keyword obj:[class_name](args...)

    // Method Calls vs Assignment Overwriting
    // Direct Method Call:
    var:method(args...)

    // Assignment from Method Return (prevents accidental method overwriting):
    [declare] target:[type] = source:method(args...)

    // Static Functions
    func [name]:[return_type](arg1:type, arg2:type) {
        // Function body
    }
```

---

## 2. Compiler-Level Primitives

HighAsm provides core compile-time introspection and copy semantics built directly into the compiler toolchain:

* `size_of(var)` — Returns the byte size of a variable or type structure.
* `copy(value)` — Enforces a true deep-copy of a value/structure. Direct assignment (`=`) creates references or shallow bindings by default.

---

### 3. Generics & Templates

HighAsm templates utilize compile-time type parameters. To assist the parser's lexer in identifying generic type slots without requiring extensive lookaheads, generic field declarations use the explicit `Type[T]` marker.

```highasm
    template Person[T, U] {
        name: Type[T]
        age: Type[U]
    }
```
* **Instantiation & Initialization Behavior**:

    1. **Primitive Initialization:**
    Standard variable creation invokes the primitive constructor (`__init__`) directly:
    ```highasm
    local var:Person["Alice", 30]
    ```
    2. **heap_allocation**
        The `allocation_without_iniation` method is used for allocating heap memory without initializing it. This can be useful in scenarios where you need to allocate space but don't want to initialize the data immediately.
        local var:create[type,...]
        note this is memory Safe (refer to 5.1 for understanding)

    3. **Classes vs. Templates:**
    While standalone templates define independent data structures (`StructObject`), encapsulating data within a `class` binds methods and behavioral logic directly to the type (`ClassObject`).

### Method Evaluation & Variable Replacement
```highasm
// Boolean Logic Block
    var:logic_method {
        // Executes if condition evaluates to true
    }

    // Inline Conditional Replacement:
    // Replaces 'var' with 'replaceValue' if 'var' satisfies 'cmpValue'
    var:method([cmpValue, replaceValue])

    // Conditional Assignment:
    // Assigns 'var2' to 'var' or 'replaceValue' depending on condition evaluation
    var2 = var:logic_method(cmpValue, replaceValue)
```

### Type-Specific Logic Routines
* **Math Types:** `equal`, `greater`, `less`, `isZero`, `notZero`, `repeat`, `switch`
* **Table / Collections:** `for([key], [value])`
* **Char / Strings:** `repeat`, `isEqual`
* **Control Loop:** `repeat` (continues execution until target evaluates to `null`)

---

## 4. Functions & Callable Objects

Functions and low-level assembly blocks use Rust-like borrowing semantics. Arguments borrow pointers to metadata arrays and underlying values.

```highasm
    // Callable Interface
    obj:call(args...)

    // Function Invocation
    fn_name:call(args...)
```

---

## 5. Scope & Memory Architecture

Memory allocation and lifetime management are explicit at the declaration site, allowing the compiler to generate optimized stack or heap allocations without a garbage collector.

* **Memory Allocation Keywords**
    * `local` — Stack-allocated within current scope. Automatically freed upon exiting scope.
    * `loan` / `pass` — Memory borrowed from caller (`loan`) or passed through to callees without unpacking (`pass`).
    * `data` — Placed in static read/write data segment of RAM. Retained for program lifespan; accessible only via pointer.

### 5.1 Managed References & Pointer Rules
HighAsm uses managed, auto-dereferenced pointers (`Reference[T]`).
and Cursors

* **Address-Of Operator (`&`):** Obtains the memory address of a target variable. can't be used on a local value
* **Auto-Dereferencing:** There is **no explicit dereference operator (`*`)**. Using a `Reference[T]` variable automatically accesses or mutates the underlying target value.
* **Non-Rebindable:** Once initialized, a `Curosr[T]` cannot be rebound to point to another memory address. Any subsequent assignment updates the referenced value.

```highasm
    data x:int64 = 42
    data y:int64 = 100

    // 'ref' permanently binds to the memory location of 'x'
    local ref:Cursor[int64] = &x

    // Mutates x to 99 (Does NOT rebind 'ref' to 'y')
    ref = 99 
```

---

## 6. Safety & Verification Blocks

    To maximize raw execution speed, HighAsm omits continuous runtime math based sanity checks (e.g., math overflow bounds) by default. Explicit boundary protection for math  is handled via `try` verification blocks. 

*    *>note: this is  not about memory safety, but 'sanity' like making sure 5+5=10* 

    ```highasm
        try {
            main: {
                // Safe execution zone
            },
            [flag]: {
                // Exception by CPU flag
            }
        };
    ```

    ---

## 7. Object Model: Classes, Singletons & Polyobjects

    HighAsm supports flexible object-oriented architectures through standard classes, pre-main initialized singletons (`construct`), and multi-threaded polymorphic structures (`polyobject`).

    ```highasm
    // Standard Class Definition
    class #ClassName {
        template {
            var:int8
        };
        def __init:instance(arg1:type) {
            self.var = 40;
        }; // All variables marked with return context auto-return
    };

    // Singleton Construct (Pre-Main Global Initialization)
    construct #SingletonName[#dynamic_address] {
        template {
            var:int8
        };
        def __init:instance(arg:type) {
            // Executed at global initialization phase before main()
        };
        def [method]:[type](arg:type) {
            // Instance method
        };
    };

    // Static-Address Construct
    construct SingletonStatic:#static_address {
        template {
            var:int8
        };
        def __init:instance() {
            // Global static initialization
        };
    };
    ```

---

## 8. Dynamic Libraries & ABI Stability

### Import Syntax & Wrappers
Importing external libraries requires explicit wrapper declarations to confirm interface constraints.

    ```highasm
    #import <library_name> {
        [fn]:[return_type]([arg_name:arg_type],...) | {}
        [name]:[type]
    }

    // Invocation:
    library_name.fn:call(...)

    // Extended API Landing Wrapper (handling returns explicitly):
    [fn]:[type](arg_name:type) {
        self:call(arg_name);
    };
    ```

### Stable ABI Runtime Resolution (`.slot` Segment)
    To prevent fragile binary interface issues across compiled libraries (`.linklib`), each dynamic library embeds a read-only `.slot` segment. Dynamic dependencies read these metadata slots at runtime to calculate payload/structure sizing dynamically (similar to Swift's resilient layout model).

    ---

### 9. Concurrency & Threading

    Concurrency is native to HighAsm through atomic polyobjects and OS-managed routine threads.

    ```highasm
    polyobject #ConcurrentObject {
        template {
            status:int8
        };
        def __init:instance(status:int8) {
            self.status = status;
        };
    };
    ```
* 1. ### threads 
    ```
    thread routine_name:return_type {
        // Block executes asynchronously within a dedicated OS thread
    }
    ```
    to spawn you do
    Id = thread_ID:Spwan(arguments):
    to push items 
    Id:push(polyObject)
    


