from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Package:
    """Represents a package in a workspace.

    Attributes:
        name: Package name (e.g., '@web-platform/shared-acorn-redux')
        path: Absolute path to package directory
        version: Package version if available
        metadata: Additional package metadata
    """

    name: str
    path: Path
    version: str | None = None
    metadata: dict[str, object] = field(default_factory=dict)

    @property
    def scope(self) -> str | None:
        if self.name.startswith("@") and "/" in self.name:
            return self.name.split("/")[0]
        return None

    @property
    def unscoped_name(self) -> str:
        if self.scope:
            return self.name.split("/", 1)[1]
        return self.name


class PackageRegistry:
    """Registry for efficient package lookup in workspaces.

    Provides multiple indexing strategies:
    - By full package name
    - By package path
    - By scope (for scoped packages like @web-platform/*)
    """

    def __init__(self) -> None:
        self._by_name: dict[str, Package] = {}
        self._by_path: dict[Path, Package] = {}
        self._by_scope: dict[str, list[Package]] = {}

    def add(self, package: Package) -> None:
        self._by_name[package.name] = package
        self._by_path[package.path] = package

        if package.scope:
            if package.scope not in self._by_scope:
                self._by_scope[package.scope] = []
            self._by_scope[package.scope].append(package)

    def get_by_name(self, name: str) -> Package | None:
        return self._by_name.get(name)

    def get_by_path(self, path: Path) -> Package | None:
        return self._by_path.get(path)

    def get_by_scope(self, scope: str) -> list[Package]:
        return self._by_scope.get(scope, [])

    def has_package(self, name: str) -> bool:
        return name in self._by_name

    def all_packages(self) -> list[Package]:
        return list(self._by_name.values())

    def __len__(self) -> int:
        return len(self._by_name)

    def __contains__(self, name: str) -> bool:
        return name in self._by_name
