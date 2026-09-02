# Parser Refactor: Moving from Regex to Proper Parser Architecture

**Status:** Blocker for language progress  
**Skill Level Needed:** Intermediate+ (parser design, Python)

## Background
HighAsm is a method-centric programming language with zero-keyword syntax. 
For 8 years, I've been the only contributor, and I've hit my skill limit on the parser.

## The Problem
1. Started with a regex-based tokenizer (MAINPATTERN in old code)
   - Worked initially but couldn't scale with language evolution
   - Became unmaintainable as edge cases accumulated
   - Eventually broke on complex nested syntax

2. Semantic analysis in `analyzer.py` was supposed to handle classification
   - But garbage in = garbage out. Bad tokenization cascaded into analysis failures

## What We Need
A proper **statement-level parser** that can handle:
- Method dispatch chains: `obj:method():another()`
- Nested generics: `Type[List[int64]]`
- Complex scopes: `var:logic[T] { nested:call { } }`
- Edge cases we haven't discovered yet (because current parser chokes on them)

## Approach
Instead of trying to fix the regex, we should:
1. Build a **simple lexer** that just tokenizes (no semantic decisions)
2. Write a **recursive descent parser** for statement structure
3. Keep `analyzer.py` doing semantic classification

## Why This Matters
Once parsing works reliably, we can:
- Actually test language features
- Get contributors excited about building the standard library
- Prove the language works, not just that it's theoretically sound

## Looking For
- Someone comfortable with parser design (Python or willing to write it)
- Experience with custom syntax (Lisp, Forth, or similar esoteric languages a plus)
- Commitment to document decisions (this needs to be maintainable by others)