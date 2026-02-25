import logging

from ..types import Package, PackageRegistry
from .base import BaseWorkspaceResolver

logger = logging.getLogger(__name__)


class StandardResolver(BaseWorkspaceResolver):
    """Resolver for standard single-package projects.

    Treats the entire repository as a single package.
    Preserves backward compatibility with existing behavior.
    """

    def discover_packages(self) -> PackageRegistry:
        """Discover packages (single package = entire repo)."""
        registry = PackageRegistry()

        package = Package(
            name=self.project_name,
            path=self.repo_path,
            version=None,
            metadata={"type": "standard"},
        )

        registry.add(package)

        logger.debug(
            f"StandardResolver: Registered single package '{self.project_name}' "
            f"at {self.repo_path}"
        )

        return registry

    def is_internal_package(self, package_name: str) -> bool:
        """Check if package is internal (always True for standard resolver)."""
        return package_name == self.project_name
