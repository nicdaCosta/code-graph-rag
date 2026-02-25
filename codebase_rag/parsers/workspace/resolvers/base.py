import json
import logging
from pathlib import Path
from typing import Any, cast

import yaml

from codebase_rag import constants as cs

from ..constants import ManifestType
from ..types import Package, PackageRegistry

logger = logging.getLogger(__name__)


class BaseWorkspaceResolver:
    """Base class for workspace resolvers with shared functionality."""

    def __init__(self, repo_path: Path, project_name: str) -> None:
        """Initialize base resolver.

        Args:
            repo_path: Root path of the repository
            project_name: Name of the project
        """
        self._repo_path = repo_path
        self._project_name = project_name
        self._registry: PackageRegistry | None = None
        self._external_packages: set[str] | None = None

    @property
    def repo_path(self) -> Path:
        """Root path of the repository."""
        return self._repo_path

    @property
    def project_name(self) -> str:
        """Name of the project."""
        return self._project_name

    @property
    def registry(self) -> PackageRegistry:
        """Lazy-loaded package registry."""
        if self._registry is None:
            self._registry = self.discover_packages()
        return self._registry

    @property
    def external_packages(self) -> set[str]:
        """Lazy-loaded set of external package names.

        Scans node_modules directory once and caches result.
        Language-agnostic approach - works for any package manager that uses node_modules.
        """
        if self._external_packages is None:
            self._external_packages = self._discover_external_packages()
        return self._external_packages

    def discover_packages(self) -> PackageRegistry:
        """Discover packages in workspace.

        Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement discover_packages()")

    def _discover_external_packages(self) -> set[str]:
        """Discover all external packages from root package.json.

        Language-agnostic approach: Reads dependencies and devDependencies from
        root package.json to identify external packages. Much faster than scanning
        node_modules directory.

        Returns:
            Set of external package names (e.g., {'react', '@types/node', 'cypress'})
        """
        external = set()
        package_json_path = self.repo_path / "package.json"

        if not package_json_path.exists():
            logger.debug(
                f"No package.json found at {self.repo_path}, no external packages"
            )
            return external

        logger.debug(f"Reading external packages from {package_json_path}")

        try:
            package_data = self._read_package_manifest(
                self.repo_path, ManifestType.PACKAGE_JSON
            )

            if not package_data:
                logger.warning(f"Could not read package.json at {package_json_path}")
                return external

            for dep_field in [
                "dependencies",
                "devDependencies",
                "peerDependencies",
                "optionalDependencies",
            ]:
                if dep_field in package_data:
                    deps = package_data[dep_field]
                    if isinstance(deps, dict):
                        for package_name in deps:
                            if isinstance(package_name, str):
                                external.add(package_name)

        except Exception as e:
            logger.warning(
                f"Failed to parse dependencies from {package_json_path}: {e}"
            )
            return external

        logger.info(f"Discovered {len(external)} external packages from package.json")
        return external

    def is_internal_package(self, package_name: str) -> bool:
        """Check if package belongs to this workspace.

        A package is internal if:
        1. It is NOT in the external packages set (node_modules), AND
        2. It IS registered in the workspace registry

        This ensures external npm packages (cypress, react, etc.) are never
        treated as internal workspace packages.

        Args:
            package_name: Package name (e.g., '@web-platform/shared-acorn-redux', 'cypress')

        Returns:
            True if package is internal to this workspace
        """
        if package_name in self.external_packages:
            return False

        return self.registry.has_package(package_name)

    def get_package_info(self, package_name: str) -> Package | None:
        """Get package information."""
        return self.registry.get_by_name(package_name)

    def resolve_package_to_path(
        self, package_name: str, subpath: str | None = None
    ) -> str | None:
        """Resolve package name to qualified internal path.

        Args:
            package_name: Full package name
            subpath: Optional subpath within package

        Returns:
            Qualified name (e.g., 'banana.libs.shared.acorn.redux.utils')
        """
        package = self.get_package_info(package_name)
        if not package:
            return None

        relative_path = package.path.relative_to(self.repo_path)
        parts = [self.project_name] + list(relative_path.parts)

        if subpath:
            subpath_parts = subpath.replace("/", cs.SEPARATOR_DOT).split(
                cs.SEPARATOR_DOT
            )
            parts.extend(subpath_parts)

        qualified_name = cs.SEPARATOR_DOT.join(parts)
        return qualified_name

    def normalize_package_name(self, import_path: str) -> tuple[str, str | None]:
        """Split import path into package name and subpath.

        Default implementation for scoped packages like @scope/package/subpath.

        Args:
            import_path: Import string (e.g., '@web-platform/shared-acorn-redux/utils')

        Returns:
            Tuple of (package_name, subpath)
        """
        if import_path.startswith("@"):
            parts = import_path.split("/", 2)
            if len(parts) >= 2:
                package_name = f"{parts[0]}/{parts[1]}"
                subpath = parts[2] if len(parts) > 2 else None
                return package_name, subpath

        parts = import_path.split("/", 1)
        package_name = parts[0]
        subpath = parts[1] if len(parts) > 1 else None
        return package_name, subpath

    def _read_package_manifest(
        self, path: Path, manifest_type: ManifestType
    ) -> dict[str, object] | None:
        """Read and parse a package manifest file.

        Language-agnostic helper for reading package metadata files.

        Args:
            path: Path to manifest file
            manifest_type: Type of manifest to read

        Returns:
            Parsed manifest data or None if file doesn't exist or is invalid
        """
        manifest_path = path / manifest_type.value

        if not manifest_path.exists():
            return None

        try:
            match manifest_type:
                case ManifestType.PACKAGE_JSON | ManifestType.PROJECT_JSON:
                    with manifest_path.open() as f:
                        return json.load(f)

                case (
                    ManifestType.CARGO_TOML
                    | ManifestType.PYPROJECT_TOML
                    | ManifestType.GO_MOD
                ):
                    import tomllib

                    with manifest_path.open("rb") as f:
                        return tomllib.load(f)

                case _:
                    logger.warning(f"Unknown manifest type: {manifest_type}")
                    return None

        except Exception as e:
            logger.warning(f"Failed to parse {manifest_path}: {e}")
            return None

    def _parse_dependencies(
        self, manifest_data: dict[str, object], manifest_type: ManifestType
    ) -> dict[str, str]:
        """Extract dependencies from manifest data.

        Args:
            manifest_data: Parsed manifest data
            manifest_type: Type of manifest

        Returns:
            Dictionary of dependency name to version
        """
        dependencies: dict[str, str] = {}

        match manifest_type:
            case ManifestType.PACKAGE_JSON:
                for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
                    if dep_type in manifest_data:
                        deps = manifest_data[dep_type]
                        if isinstance(deps, dict):
                            for key, value in deps.items():
                                if isinstance(key, str) and isinstance(value, str):
                                    dependencies[key] = value

            case ManifestType.CARGO_TOML:
                if "dependencies" in manifest_data:
                    deps = manifest_data["dependencies"]
                    if isinstance(deps, dict):
                        for key, value in deps.items():
                            if isinstance(key, str) and isinstance(value, str):
                                dependencies[key] = value

            case ManifestType.PYPROJECT_TOML:
                if "project" in manifest_data:
                    project_data: Any = manifest_data["project"]
                    if (
                        isinstance(project_data, dict)
                        and "dependencies" in project_data
                    ):
                        project_dict = cast(dict[str, Any], project_data)
                        deps = project_dict["dependencies"]
                        if isinstance(deps, list):
                            for dep in deps:
                                if isinstance(dep, str):
                                    name = dep.split(">=")[0].split("==")[0].strip()
                                    dependencies[name] = dep

        return dependencies

    def _expand_workspace_patterns(self, patterns: list[str]) -> list[Path]:
        """Expand glob patterns to discover package directories.

        Shared utility for both PNPM and NX workspace pattern expansion.

        Args:
            patterns: List of glob patterns (e.g., ['libs/**/*', 'apps/*'])

        Returns:
            List of discovered package directories
        """
        discovered: list[Path] = []

        for pattern in patterns:
            try:
                matches = self.repo_path.glob(pattern)
                for match in matches:
                    if match.is_dir():
                        discovered.append(match)
            except Exception as e:
                logger.warning(
                    f"Failed to expand pattern '{pattern}' in {self.repo_path}: {e}"
                )

        return discovered

    def _read_yaml_file(self, path: Path) -> dict[str, object] | None:
        """Read and parse a YAML file.

        Args:
            path: Path to YAML file

        Returns:
            Parsed YAML data or None if file doesn't exist or is invalid
        """
        if not path.exists():
            return None

        try:
            with path.open() as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Failed to parse YAML file {path}: {e}")
            return None
