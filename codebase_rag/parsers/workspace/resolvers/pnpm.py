import logging

from ..constants import ManifestType
from ..types import Package, PackageRegistry
from .base import BaseWorkspaceResolver

logger = logging.getLogger(__name__)


class PnpmWorkspaceResolver(BaseWorkspaceResolver):
    """Resolver for PNPM workspaces.

    Parses pnpm-workspace.yaml to discover packages.
    """

    def discover_packages(self) -> PackageRegistry:
        """Discover packages from pnpm-workspace.yaml."""
        registry = PackageRegistry()

        workspace_file = self.repo_path / "pnpm-workspace.yaml"
        workspace_data = self._read_yaml_file(workspace_file)

        if not workspace_data:
            logger.warning(f"Could not read {workspace_file}, using empty registry")
            return registry

        packages_patterns_raw = workspace_data.get("packages", [])
        if not isinstance(packages_patterns_raw, list):
            logger.warning(
                f"Invalid 'packages' field in {workspace_file}, expected list"
            )
            return registry

        packages_patterns: list[str] = []
        for pattern in packages_patterns_raw:
            if isinstance(pattern, str):
                packages_patterns.append(pattern)
            else:
                logger.warning(
                    f"Skipping non-string pattern in {workspace_file}: {pattern}"
                )

        package_dirs = self._expand_workspace_patterns(packages_patterns)

        for package_dir in package_dirs:
            manifest = self._read_package_manifest(
                package_dir, ManifestType.PACKAGE_JSON
            )

            if not manifest:
                continue

            package_name = manifest.get("name")
            if not isinstance(package_name, str):
                logger.debug(f"Skipping {package_dir}: no valid 'name' in package.json")
                continue

            package_version = manifest.get("version")
            version = package_version if isinstance(package_version, str) else None

            package = Package(
                name=package_name,
                path=package_dir,
                version=version,
                metadata={
                    "workspace_type": "pnpm",
                    "dependencies": self._parse_dependencies(
                        manifest, ManifestType.PACKAGE_JSON
                    ),
                },
            )

            registry.add(package)
            logger.debug(f"PNPM: Registered package '{package_name}' at {package_dir}")

        logger.info(
            f"PnpmWorkspaceResolver: Discovered {len(registry)} packages "
            f"in {self.repo_path}"
        )

        return registry
