HighAsm:Language Documentation
Overview

"This document is a theoretical syntax specification and memory-model blueprint. 
It is released to the public domain as prior art for researchers and compiler engineers interested in zero-cost memory safety. 
I am seeking implementers to develop the BIR and compiler based on these logic rules."

"This is a theoretical specification provided for educational and research purposes only. 
The author is not providing implementation services or technical support."

i do want to say i'm sorry about the Documentation this was a brain dumped refined over the month
it' should give you want you need but your skills are going to be needed 

a pure-method based language

This language is designed to be a highly efficient and flexible hybrid system, combining the best of compiled and interpreted paradigms. This is a general system programming lanauge
Key Features

    Modularity: Extendable through syntax libraries and external dynamic libraries (DLL), allowing users to add new functionality as needed.
    Performance Focused: optimized in that their is no reference lookup at runtime unless done so by method
    Strong Type System: A rigorous casting system that ensures type safety and prevents misuse of variables by maintaining strict type constraints.

    the syntax is built around the concept of methods
        declare_keyword var:method/type([args]...),
        to prevent overwriting you must do
        [declare] var:`[type]` = var2:method(args)



Core Concepts
1. declares and special calls

    `func [name]:[return_type](args...){}` -- for functions this is static
    `class|interface[name]{}` -- to build a class -- returns a class object (used by compiler only)
        `template {}` -- used only in the class& interface stores a blueprint and is called on by the
    `interface [name]{}` -- used to handle system interactive with the hardware
    `char(value:literal_character)` -- defines a char (1 byte)
    `int8/int64(value:literal_integer)` -- defines  a int from 8 to 64
    `float8/float64(value:literal_float)` -- defines a float from 8 to 64

2. compiler time  functions: these are complied functions that are at compile time can by used by any type
    size_of() -- returns the byte_size of the var
    copy(value) -- by default equal sign "=" only sets references use this to create a true (deep_copy)

3. logic methods/routine methods
    logic methods are boolean based methods
    `[condition_var]:loop([keys]){}`
    `[condition_var]:branch(fn_ptr)` -- dose not create a new scope (is not a call) could be

4. functions:
    functions use what rust cost borrowing where the augments borrow the pointer to the meta_array and value
    The following functions are available for function and asm class you must use the `=` sign here as the fn would be overwritten if not done so
    shared by both:
    call(args...) -- this calls the object , fn:call(args...)

    function only :
    pcall(args...) -- this is a protected call the function object fn:pcall(args...)

    to declare a function look in section 1

6. scope management
    in HighAsm we use Scope base memory_management (you cannot copy a pointer)
        local  - The keyword  is  to define for the stack a the function or block and freed when scope ends can be on ram with a stack pointer , or on the stack itself
        ret  -- vars meant to be returned -- note this is not the return word itself but; at the end of a scope it will auto_return as their can only be one
        data - put in the data segment of ram and is not readonly , this is not freed when the scope ends and can only be referred to by the pointer
        borrow -- this is used if you want to alais a variable it will not free and can not be returned or moved

7. classes and interfaces -- this has been changed due to new system design
    this will pull on the word def for new method and can only be used inside
    ```class [name]{
        template {
            var:int8
        }
        def __init:instance(argument_name:type,...){
            ret myName = self:newtemp()
            myName.var = 40
        } -- all vars with ret are auto returned
    }```
    ```interface [name]{
        syscalls_list {
            [name]:[number],
            ...,
        }
        template {
            var:int8
        }
        def [method]:[type](arg:name,...){

        }
    }```
7.1
    to use a syscall in the interface you must do syscall:[id](args_values)
7.2 
    this also contains a io lib , io.put([address],var) and io.get([address])
    this is limited to the interface class


Advanced Topics
1. imports
    to_import a file you must use `#import/#static_import <[name]>{[fn]:[type]([args:argsType],...)|{},...}`
    the reason for the wrapper is confirmation that you understand what your doing
    you call a imported lib in the wrapper you just use `[lib].[fn]:call(...)`
    if you want to hook the api you just add a body but don't forget to use self:call() in the body like
    ```[fn]:[type](arg_name:type,...){
        ....
        self:call(args,...) - you must handle the return value
    }```

2. Scoped Variables and Type Safety
    Once a variable is declared  it is type-safe and it can not be casted expect to a byte type (which is assumed system_int)

3. System Calls
    now defined in the class and interface section

4. Locking and Concurrency
    Concurrency can be managed via low-level locking mechanisms, allowing multiple threads or processes to safely access shared resources. 
    this is not yet defined i'm thinking of using a mailbox protocal don't know

internal_logic
    tab[n] -- this is a macro it is not just a ptr+n look up and has limits 
    you can only borrow from this 
    this is how it would look on the x86-64 if build correctly
        mov rdi, [base_ptr]    // Meta-lookup
        call __getMeta         // Returns Ptr to MetaTable [TotalSize, TypeSize] in RAX
        mov r10, rax           // R10 = MetaTable Address
        mov rax, [index]       // Load user's Base-10 Index
        mov r11, [r10 + 8]     // Load the 2nd Element (TypeSize/Width) 
        multi r11              // Conversion: RAX = Index * TypeSize
        jo [__guillotine_err]  // THE LOGIC GATE: Overflow check
        // Comparison against the 1st Element (Total Segment Size)
        cmp rax, [r10]         
        jae [__guillotine_err] // THE MEMORY GATE: Boundary check
        mov val,rax+base_ptr
