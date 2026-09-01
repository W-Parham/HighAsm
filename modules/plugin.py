# this plugin manager isn't to handle the lexing or parsign but to handle the semantics anylazatuion and final constuction of the Ast
from dataclasses import dataclass

class PluginManager:
    pass

@dataclass(slots=True,kw_only=True)
class Plugin:
    pass