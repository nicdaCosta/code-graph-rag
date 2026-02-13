from pathlib import Path

from codebase_rag.parsers.resolvers import TypeScriptModuleResolver
from codebase_rag.parsers.workspace.factory import WorkspaceResolverFactory


def test_typescript_resolver_workspace_package(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    (workspace / "pnpm-workspace.yaml").write_text("packages:\n  - 'libs/*'\n")

    package_dir = workspace / "libs" / "shared-acorn-redux"
    package_dir.mkdir(parents=True)
    (package_dir / "package.json").write_text(
        '{"name": "@web-platform/shared-acorn-redux", "version": "1.0.0"}'
    )

    src_dir = package_dir / "src" / "selectors"
    src_dir.mkdir(parents=True)
    src_file = src_dir / "validItineraries.ts"
    src_file.write_text("export function getAllValidItineraryIds() {}")

    ws_factory = WorkspaceResolverFactory(workspace, "workspace")
    ws_resolver = ws_factory.create_resolver()

    ts_resolver = TypeScriptModuleResolver(
        repo_path=workspace,
        project_name="workspace",
        workspace_resolver=ws_resolver,
    )
    ts_resolver.initialize()

    from_file = workspace / "apps" / "flights" / "FlightsDayView.tsx"
    from_file.parent.mkdir(parents=True, exist_ok=True)
    from_file.write_text("// test")

    import_spec = "@web-platform/shared-acorn-redux/src/selectors/validItineraries"
    resolved = ts_resolver.resolve(import_spec, from_file)

    assert resolved is not None
    assert resolved == src_file
    assert resolved.exists()


def test_typescript_resolver_external_package(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    (workspace / "pnpm-workspace.yaml").write_text("packages:\n  - 'libs/*'\n")
    (workspace / "package.json").write_text('{"dependencies": {"cypress": "^13.0.0"}}')

    ws_factory = WorkspaceResolverFactory(workspace, "workspace")
    ws_resolver = ws_factory.create_resolver()

    ts_resolver = TypeScriptModuleResolver(
        repo_path=workspace,
        project_name="workspace",
        workspace_resolver=ws_resolver,
    )

    from_file = workspace / "tests" / "spec.ts"
    from_file.parent.mkdir(parents=True, exist_ok=True)
    from_file.write_text("// test")

    resolved = ts_resolver.resolve("cypress/angular", from_file)
    assert resolved is None

    assert ts_resolver.is_external("cypress/angular") is True
    assert ts_resolver.is_external("react") is True


def test_typescript_resolver_relative_import(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    src_dir = workspace / "src"
    src_dir.mkdir()
    (src_dir / "utils.ts").write_text("export function helper() {}")
    (src_dir / "index.ts").write_text("import { helper } from './utils'")

    ts_resolver = TypeScriptModuleResolver(
        repo_path=workspace,
        project_name="workspace",
    )

    from_file = src_dir / "index.ts"
    resolved = ts_resolver.resolve("./utils", from_file)

    assert resolved == src_dir / "utils.ts"
    assert ts_resolver.is_external("./utils") is False


def test_typescript_resolver_long_running_subprocess(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    src_dir = workspace / "src"
    src_dir.mkdir()
    (src_dir / "utils.ts").write_text("export function helper() {}")
    (src_dir / "models.ts").write_text("export class Model {}")
    (src_dir / "index.ts").write_text("import { helper } from './utils'")

    ts_resolver = TypeScriptModuleResolver(
        repo_path=workspace,
        project_name="workspace",
    )
    ts_resolver.initialize()

    if ts_resolver._node_available:
        assert ts_resolver._node_process is not None
        initial_pid = ts_resolver._node_process.pid
        assert ts_resolver._node_process.poll() is None

        from_file = src_dir / "index.ts"

        resolved1 = ts_resolver.resolve("./utils", from_file)
        assert resolved1 == src_dir / "utils.ts"

        assert ts_resolver._node_process.pid == initial_pid
        assert ts_resolver._node_process.poll() is None

        resolved2 = ts_resolver.resolve("./models", from_file)
        assert resolved2 == src_dir / "models.ts"

        assert ts_resolver._node_process.pid == initial_pid
        assert ts_resolver._node_process.poll() is None

        ts_resolver.cleanup()
        assert ts_resolver._node_process is None
    else:
        assert ts_resolver._node_process is None
