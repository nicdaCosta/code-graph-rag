from __future__ import annotations

from pathlib import Path

from loguru import logger


class BaseModuleResolver:
    """Base resolver with no-op implementations for fallback.

    Languages without a specific resolver get this behavior:
    - resolve() returns None (triggers fallback to naive string replacement)
    - is_external() returns True (treats everything as external)
    - initialize() does nothing
    """

    def __init__(self, repo_path: Path, project_name: str) -> None:
        self.repo_path = repo_path
        self.project_name = project_name
        logger.debug(
            f"BaseModuleResolver initialized for {project_name} at {repo_path}"
        )

    def resolve(self, import_specifier: str, from_file: Path) -> Path | None:
        logger.debug(
            f"BaseModuleResolver.resolve: {import_specifier} from {from_file} -> None (fallback)"
        )
        return None

    def is_external(self, import_specifier: str) -> bool:
        return True

    def initialize(self) -> None:
        pass

    def cleanup(self) -> None:
        pass
