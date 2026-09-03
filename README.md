# HighAsm

A method-centric systems programming language with zero-keyword syntax.

## What Makes HighAsm Different

Instead of traditional keywords (`if`, `for`, `var`), HighAsm uses pure method dispatch:

```highasm
var:condition { /* executes if true */ }
counter:repeat { /* loop */ }
list:for(key, value) { /* iterate */ }
```

This eliminates syntax bloat and makes every operation a method call on objects or primitives.

## Status

**Early stage / 8-year refactor in progress**

We're rebuilding the parser on the `prototype` branch. If you're interested in language design or parser architecture, [check out the blocker issue](https://github.com/W-Parham/HighAsm/issues).

## Project Structure

- `docs/HighAsm_Language_Documentation.md` — Full language specification
- `prototype` branch — Parser refactor in progress
- `main` branch — Documentation and project foundation

## Help Wanted

We need contributors experienced with **parser design** to help build a proper lexer + recursive descent parser for HighAsm's method-centric syntax.

Interested? Open an issue or check the parser refactor discussion.

## License
Apache 2.0