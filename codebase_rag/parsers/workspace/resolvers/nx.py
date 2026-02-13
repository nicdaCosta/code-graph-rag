import logging

from ..constants import ManifestType
from ..types import Package, PackageRegistry
from .base import BaseWorkspaceResolver

logger = logging.getLogger(__name__)


class NxWorkspaceResolver(BaseWorkspaceResolver):
    """Resolver for NX workspaces.

    Supports dual configuration per NX docs:
    1. Standalone project.json files
    2. package.json files with 'nx' property
    """

    def discover_packages(self) -> PackageRegistry:
        """Discover NX projects from project.json and package.json files."""
        registry = PackageRegistry()

        self._discover_from_project_json(registry)
        self._discover_from_package_json_with_nx(registry)

        logger.info(
            f"NxWorkspaceResolver: Discovered {len(registry)} packages "
            f"in {self.repo_path}"
        )

        return registry

    def _discover_from_project_json(self, registry: PackageRegistry) -> None:
        """Discover NX projects from standalone project.json files."""
        project_json_files = self.repo_path.glob("**/project.json")

        for project_json_path in project_json_files:
            if not project_json_path.is_file():
                continue

            project_dir = project_json_path.parent

            project_data = self._read_package_manifest(
                project_dir, ManifestType.PROJECT_JSON
            )

            if not project_data:
                continue

            package_json = self._read_package_manifest(
                project_dir, ManifestType.PACKAGE_JSON
            )

            if package_json:
                package_name = package_json.get("name")
            else:
                project_name = project_data.get("name")
                if isinstance(project_name, str):
                    package_name = project_name
                else:
                    package_name = project_dir.relative_to(self.repo_path).as_posix()

            if not isinstance(package_name, str):
                logger.debug(
                    f"Skipping {project_dir}: could not determine package name"
                )
                continue

            if registry.has_package(package_name):
                logger.debug(
                    f"Skipping {project_dir}: package '{package_name}' already registered"
                )
                continue

            version = None
            if package_json:
                package_version = package_json.get("version")
                if isinstance(package_version, str):
                    version = package_version

            package = Package(
                name=package_name,
                path=project_dir,
                version=version,
                metadata={
                    "workspace_type": "nx",
                    "config_type": "project.json",
                    "project_data": project_data,
                },
            )

            registry.add(package)
            logger.debug(
                f"NX: Registered package '{package_name}' from project.json "
                f"at {project_dir}"
            )

    def _discover_from_package_json_with_nx(self, registry: PackageRegistry) -> None:
        """Discover NX projects from package.json files with 'nx' property."""
        package_json_files = self.repo_path.glob("**/package.json")

        for package_json_path in package_json_files:
            if not package_json_path.is_file():
                continue

            package_dir = package_json_path.parent

            package_data = self._read_package_manifest(
                package_dir, ManifestType.PACKAGE_JSON
            )

            if not package_data:
                continue

            if "nx" not in package_data:
                continue

            package_name = package_data.get("name")
            if not isinstance(package_name, str):
                logger.debug(f"Skipping {package_dir}: no valid 'name' in package.json")
                continue

            if registry.has_package(package_name):
                logger.debug(
                    f"Skipping {package_dir}: package '{package_name}' already registered"
                )
                continue

            package_version = package_data.get("version")
            version = package_version if isinstance(package_version, str) else None

            package = Package(
                name=package_name,
                path=package_dir,
                version=version,
                metadata={
                    "workspace_type": "nx",
                    "config_type": "package.json",
                    "nx_config": package_data.get("nx"),
                    "dependencies": self._parse_dependencies(
                        package_data, ManifestType.PACKAGE_JSON
                    ),
                },
            )

            registry.add(package)
            logger.debug(
                f"NX: Registered package '{package_name}' from package.json "
                f"at {package_dir}"
            )
