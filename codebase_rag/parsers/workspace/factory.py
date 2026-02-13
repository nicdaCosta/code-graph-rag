import logging
from pathlib import Path

from .constants import WorkspaceType
from .protocol import WorkspaceResolver
from .resolvers import NxWorkspaceResolver, PnpmWorkspaceResolver, StandardResolver

logger = logging.getLogger(__name__)


class WorkspaceResolverFactory:
    """Factory for detecting and creating appropriate workspace resolvers.

    Detects workspace type from marker files and returns the appropriate resolver.
    """

    DETECTION_RULES: list[tuple[WorkspaceType, list[str], type[WorkspaceResolver]]] = [
        (WorkspaceType.PNPM, ["pnpm-workspace.yaml"], PnpmWorkspaceResolver),
        (WorkspaceType.NX, ["nx.json"], NxWorkspaceResolver),
    ]

    def __init__(self, repo_path: Path, project_name: str) -> None:
        """Initialize factory.

        Args:
            repo_path: Root path of the repository
            project_name: Name of the project
        """
        self.repo_path = repo_path
        self.project_name = project_name
        self._cached_resolver: WorkspaceResolver | None = None

    def create_resolver(self) -> WorkspaceResolver:
        """Create and return appropriate workspace resolver.

        Uses cached resolver if already created.

        Returns:
            WorkspaceResolver instance appropriate for the repository
        """
        if self._cached_resolver is not None:
            return self._cached_resolver

        workspace_type, resolver_class = self._detect_workspace_type()

        self._cached_resolver = resolver_class(
            repo_path=self.repo_path, project_name=self.project_name
        )

        logger.info(
            f"WorkspaceResolverFactory: Using {resolver_class.__name__} "
            f"(type: {workspace_type.value}) for {self.repo_path}"
        )

        return self._cached_resolver

    def _detect_workspace_type(
        self,
    ) -> tuple[WorkspaceType, type[WorkspaceResolver]]:
        """Detect workspace type from marker files.

        Returns:
            Tuple of (WorkspaceType, resolver_class)
        """
        for workspace_type, marker_files, resolver_class in self.DETECTION_RULES:
            if self._check_markers(marker_files):
                if self._validate_workspace_structure(workspace_type):
                    return workspace_type, resolver_class

        logger.debug(
            f"No workspace markers found in {self.repo_path}, using StandardResolver"
        )
        return WorkspaceType.STANDARD, StandardResolver

    def _check_markers(self, marker_files: list[str]) -> bool:
        """Check if all marker files exist in the repository.

        Args:
            marker_files: List of marker file names to check

        Returns:
            True if all markers exist
        """
        for marker in marker_files:
            marker_path = self.repo_path / marker
            if not marker_path.exists():
                return False
        return True

    def _validate_workspace_structure(self, workspace_type: WorkspaceType) -> bool:
        """Validate that the workspace structure is valid.

        Performs additional checks beyond just marker file presence.

        Args:
            workspace_type: Type of workspace to validate

        Returns:
            True if workspace structure is valid
        """
        match workspace_type:
            case WorkspaceType.PNPM:
                return self._validate_pnpm_workspace()

            case WorkspaceType.NX:
                return self._validate_nx_workspace()

            case _:
                return True

    def _validate_pnpm_workspace(self) -> bool:
        """Validate PNPM workspace structure."""
        workspace_file = self.repo_path / "pnpm-workspace.yaml"

        try:
            import yaml

            with workspace_file.open() as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                logger.warning(
                    f"Invalid pnpm-workspace.yaml: expected dict, got {type(data)}"
                )
                return False

            if "packages" not in data:
                logger.warning("Invalid pnpm-workspace.yaml: missing 'packages' field")
                return False

            if not isinstance(data["packages"], list):
                logger.warning("Invalid pnpm-workspace.yaml: 'packages' must be a list")
                return False

            return True

        except Exception as e:
            logger.warning(f"Failed to validate pnpm-workspace.yaml: {e}")
            return False

    def _validate_nx_workspace(self) -> bool:
        """Validate NX workspace structure."""
        nx_json = self.repo_path / "nx.json"

        try:
            import json

            with nx_json.open() as f:
                data = json.load(f)

            if not isinstance(data, dict):
                logger.warning(f"Invalid nx.json: expected dict, got {type(data)}")
                return False

            return True

        except Exception as e:
            logger.warning(f"Failed to validate nx.json: {e}")
            return False
