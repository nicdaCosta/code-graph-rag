from pathlib import Path

from codebase_rag.parsers.workspace.factory import WorkspaceResolverFactory


def test_external_packages_from_package_json(tmp_path: Path) -> None:
    """Test that external packages from package.json are not classified as internal."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    root_package_json = workspace / "package.json"
    root_package_json.write_text("""{
        "name": "workspace",
        "dependencies": {
            "react": "^18.0.0",
            "lodash": "^4.17.21",
            "@types/node": "^20.0.0"
        },
        "devDependencies": {
            "cypress": "^13.0.0",
            "@types/react": "^18.0.0"
        }
    }""")

    pnpm_workspace = workspace / "pnpm-workspace.yaml"
    pnpm_workspace.write_text("packages:\n  - 'libs/*'\n")

    libs_dir = workspace / "libs" / "my-lib"
    libs_dir.mkdir(parents=True)
    (libs_dir / "package.json").write_text('{"name": "@workspace/my-lib"}')

    factory = WorkspaceResolverFactory(workspace, "workspace")
    resolver = factory.create_resolver()

    assert len(resolver.external_packages) == 5

    assert not resolver.is_internal_package("cypress")
    assert not resolver.is_internal_package("react")
    assert not resolver.is_internal_package("lodash")
    assert not resolver.is_internal_package("@types/node")
    assert not resolver.is_internal_package("@types/react")

    assert resolver.is_internal_package("@workspace/my-lib")


def test_scoped_external_vs_workspace_packages(tmp_path: Path) -> None:
    """Test distinction between scoped external packages and scoped workspace packages."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    root_package_json = workspace / "package.json"
    root_package_json.write_text("""{
        "name": "workspace",
        "dependencies": {
            "@external/package1": "^1.0.0",
            "@external/package2": "^2.0.0"
        }
    }""")

    pnpm_workspace = workspace / "pnpm-workspace.yaml"
    pnpm_workspace.write_text("packages:\n  - 'libs/*'\n")

    libs_dir = workspace / "libs" / "my-lib"
    libs_dir.mkdir(parents=True)
    (libs_dir / "package.json").write_text('{"name": "@workspace/my-lib"}')

    factory = WorkspaceResolverFactory(workspace, "workspace")
    resolver = factory.create_resolver()

    assert not resolver.is_internal_package("@external/package1")
    assert not resolver.is_internal_package("@external/package2")

    assert resolver.is_internal_package("@workspace/my-lib")


def test_no_package_json_at_root(tmp_path: Path) -> None:
    """Test that resolver works correctly when root package.json doesn't exist."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    pnpm_workspace = workspace / "pnpm-workspace.yaml"
    pnpm_workspace.write_text("packages:\n  - 'libs/*'\n")

    libs_dir = workspace / "libs" / "my-lib"
    libs_dir.mkdir(parents=True)
    (libs_dir / "package.json").write_text('{"name": "@workspace/my-lib"}')

    factory = WorkspaceResolverFactory(workspace, "workspace")
    resolver = factory.create_resolver()

    assert len(resolver.external_packages) == 0

    assert resolver.is_internal_package("@workspace/my-lib")


def test_external_packages_cached(tmp_path: Path) -> None:
    """Test that external packages set is cached and only read once."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    root_package_json = workspace / "package.json"
    root_package_json.write_text("""{
        "name": "workspace",
        "dependencies": {"react": "^18.0.0"}
    }""")

    pnpm_workspace = workspace / "pnpm-workspace.yaml"
    pnpm_workspace.write_text("packages:\n  - 'libs/*'\n")

    factory = WorkspaceResolverFactory(workspace, "workspace")
    resolver = factory.create_resolver()

    external1 = resolver.external_packages
    assert "react" in external1

    external2 = resolver.external_packages
    assert external1 is external2

    assert not resolver.is_internal_package("react")
    assert not resolver.is_internal_package("react")


def test_all_dependency_fields_parsed(tmp_path: Path) -> None:
    """Test that all dependency field types are parsed from package.json."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    root_package_json = workspace / "package.json"
    root_package_json.write_text("""{
        "name": "workspace",
        "dependencies": {"dep1": "^1.0.0"},
        "devDependencies": {"dep2": "^2.0.0"},
        "peerDependencies": {"dep3": "^3.0.0"},
        "optionalDependencies": {"dep4": "^4.0.0"}
    }""")

    pnpm_workspace = workspace / "pnpm-workspace.yaml"
    pnpm_workspace.write_text("packages:\n  - 'libs/*'\n")

    factory = WorkspaceResolverFactory(workspace, "workspace")
    resolver = factory.create_resolver()

    assert "dep1" in resolver.external_packages
    assert "dep2" in resolver.external_packages
    assert "dep3" in resolver.external_packages
    assert "dep4" in resolver.external_packages
    assert len(resolver.external_packages) == 4
