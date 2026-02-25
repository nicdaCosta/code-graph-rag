from pathlib import Path
from typing import Protocol

from .types import Package, PackageRegistry


class WorkspaceResolver(Protocol):
    @property
    def repo_path(self) -> Path: ...

    @property
    def project_name(self) -> str: ...

    @property
    def external_packages(self) -> set[str]: ...

    def discover_packages(self) -> PackageRegistry: ...

    def is_internal_package(self, package_name: str) -> bool: ...

    def resolve_package_to_path(
        self, package_name: str, subpath: str | None = None
    ) -> str | None: ...

    def get_package_info(self, package_name: str) -> Package | None: ...

    def normalize_package_name(self, import_path: str) -> tuple[str, str | None]: ...
