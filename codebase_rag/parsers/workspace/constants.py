from enum import StrEnum


class WorkspaceType(StrEnum):
    """Types of workspace configurations."""

    PNPM = "pnpm"
    NPM = "npm"
    NX = "nx"
    CARGO = "cargo"
    GO = "go"
    STANDARD = "standard"


class ManifestType(StrEnum):
    """Types of package manifest files."""

    PACKAGE_JSON = "package.json"
    CARGO_TOML = "Cargo.toml"
    GO_MOD = "go.mod"
    PYPROJECT_TOML = "pyproject.toml"
    PROJECT_JSON = "project.json"
