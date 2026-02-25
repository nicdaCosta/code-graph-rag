from codebase_rag.types_defs import ModuleResolverProtocol

from .typescript import TypeScriptModuleResolver

ModuleResolver = ModuleResolverProtocol

__all__ = [
    "ModuleResolver",
    "ModuleResolverProtocol",
    "TypeScriptModuleResolver",
]
