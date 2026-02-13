from pathlib import Path
from typing import Protocol

from .types import Package, PackageRegistry


class WorkspaceResolver(Protocol):
    """Protocol for workspace resolution strategies.

    Defines the interface that all workspace resolvers must implement.
    Language-agnostic and extensible for different workspace types.
    """

    @property
    def repo_path(self) -> Path:
        """Root path of the repository."""
        ...

    @property
    def project_name(self) -> str:
        """Name of the project."""
        ...

    def discover_packages(self) -> PackageRegistry:
        """Discover all packages in the workspace.

        Returns:
            PackageRegistry containing all discovered packages
        """
        ...

    def is_internal_package(self, package_name: str) -> bool:
        """Check if a package name belongs to this workspace.

        Args:
            package_name: Full package name (e.g., '@web-platform/shared-acorn-redux')

        Returns:
            True if package is internal to this workspace
        """
        ...

    def resolve_package_to_path(
        self, package_name: str, subpath: str | None = None
    ) -> str | None:
        """Resolve a package name to a qualified internal path.

        Args:
            package_name: Full package name
            subpath: Optional subpath within package (e.g., 'utils')

        Returns:
            Qualified name (e.g., 'banana.libs.shared.acorn.redux.utils')
            or None if not found
        """
        ...

    def get_package_info(self, package_name: str) -> Package | None:
        """Get package information.

        Args:
            package_name: Full package name

        Returns:
            Package object or None if not found
        """
        ...

    def normalize_package_name(self, import_path: str) -> tuple[str, str | None]:
        """Split import path into package name and subpath.

        Args:
            import_path: Import string (e.g., '@web-platform/shared-acorn-redux/utils')

        Returns:
            Tuple of (package_name, subpath)
            e.g., ('@web-platform/shared-acorn-redux', 'utils')
        """
        ...
