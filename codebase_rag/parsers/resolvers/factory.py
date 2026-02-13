from __future__ import annotations

from pathlib import Path

from codebase_rag import constants as cs
from codebase_rag.types_defs import ModuleResolverProtocol

from .base import BaseModuleResolver
from .typescript import TypeScriptModuleResolver

MODULE_RESOLVER_REGISTRY: dict[cs.SupportedLanguage, type[ModuleResolverProtocol]] = {}


def register_resolver(
    language: cs.SupportedLanguage,
    resolver_class: type[ModuleResolverProtocol],
) -> None:
    """Register a module resolver for a language.

    Args:
        language: Language enum
        resolver_class: Resolver class implementing ModuleResolver protocol
    """
    MODULE_RESOLVER_REGISTRY[language] = resolver_class


def create_module_resolver(
    language: cs.SupportedLanguage,
    repo_path: Path,
    project_name: str,
    **kwargs,
) -> ModuleResolverProtocol:
    """Create a module resolver for the given language.

    Args:
        language: Language to create resolver for
        repo_path: Repository root path
        project_name: Project name for QN construction
        **kwargs: Language-specific resolver options:
            - workspace_resolver: WorkspaceResolver for monorepos (TS/JS)
            - tsconfig_resolver: TsConfigResolver for TypeScript (TS/JS)
            - (Future: python_path, cargo_config, etc.)

    Returns:
        Language-specific resolver, or BaseModuleResolver if no specific resolver exists
    """
    if language not in MODULE_RESOLVER_REGISTRY:
        return BaseModuleResolver(repo_path, project_name)

    resolver_class = MODULE_RESOLVER_REGISTRY[language]

    if language in (cs.SupportedLanguage.TS, cs.SupportedLanguage.JS):
        if resolver_class is TypeScriptModuleResolver:
            resolver = TypeScriptModuleResolver(
                repo_path=repo_path,
                project_name=project_name,
                workspace_resolver=kwargs.get("workspace_resolver"),
                tsconfig_resolver=kwargs.get("tsconfig_resolver"),
            )
            resolver.initialize()
            return resolver

    try:
        resolver = resolver_class(repo_path, project_name, **kwargs)
    except TypeError:
        resolver = resolver_class(repo_path, project_name)
    resolver.initialize()
    return resolver


register_resolver(cs.SupportedLanguage.TS, TypeScriptModuleResolver)
register_resolver(cs.SupportedLanguage.JS, TypeScriptModuleResolver)
