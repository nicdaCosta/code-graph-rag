from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from codebase_rag import constants as cs
from codebase_rag import logs as ls

if TYPE_CHECKING:
    from codebase_rag.parsers.js_ts.tsconfig_resolver import TsConfigResolver
    from codebase_rag.parsers.workspace.protocol import WorkspaceResolver

_TS_JS_EXTENSIONS = [".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".mts", ".cts"]


@dataclass
class ResolveResult:
    """Result of module resolution attempt.

    Attributes:
        path: Resolved filesystem path if successful
        is_external: True if in node_modules, False if internal, None if unknown
        error: Error message if resolution failed
    """

    path: Path | None
    is_external: bool | None
    error: str | None = None


class TypeScriptModuleResolver:
    """Module resolver for TypeScript and JavaScript.

    Uses Node.js native module resolution via subprocess to ensure accurate resolution
    that matches the TypeScript compiler's behavior. Falls back to Python-based
    resolution if Node.js is not available.

    Resolution strategy:
    1. Check if Node.js is available
    2. If available: Use Node.js helper script for resolution (delegates to require.resolve)
    3. Fallback: Use Python-based resolution (tsconfig paths, workspace packages)
    4. For relative imports: Always use Python-based resolution (no subprocess needed)
    """

    def __init__(
        self,
        repo_path: Path,
        project_name: str,
        workspace_resolver: WorkspaceResolver | None = None,
        tsconfig_resolver: TsConfigResolver | None = None,
    ) -> None:
        self.repo_path = repo_path
        self.project_name = project_name
        self.workspace_resolver = workspace_resolver
        self.tsconfig_resolver = tsconfig_resolver
        self._node_available: bool | None = None
        self._node_helper_script: Path | None = None
        self._node_process: subprocess.Popen | None = None
        self._resolution_cache: dict[tuple[str, str], Path | None] = {}

        logger.debug(
            f"TypeScriptModuleResolver initialized: "
            f"workspace={workspace_resolver is not None}, "
            f"tsconfig={tsconfig_resolver is not None}"
        )

    def initialize(self) -> None:
        """Initialize resolver - check Node.js availability and start long-running subprocess."""
        self._check_node_availability()

        if self._node_available:
            self._node_helper_script = (
                Path(__file__).parent / "scripts" / "ts_resolve.js"
            )

            if not self._node_helper_script.exists():
                logger.warning(
                    f"Node.js helper script not found at {self._node_helper_script}. "
                    "Falling back to Python-based resolution."
                )
                self._node_available = False
            else:
                logger.debug(
                    f"Node.js helper script available at {self._node_helper_script}"
                )
                self._start_node_process()

                if self._node_process:
                    self._send_workspace_init()

    def _check_node_availability(self) -> bool:
        """Check if Node.js is available in the system PATH."""
        if self._node_available is not None:
            return self._node_available

        node_path = shutil.which("node")
        self._node_available = node_path is not None

        if self._node_available:
            logger.debug(f"Node.js found at: {node_path}")
        else:
            logger.warning(
                "Node.js not found in PATH. TypeScript resolution will fall back to "
                "Python-based workspace/tsconfig resolution. Install Node.js for "
                "more accurate module resolution."
            )

        return self._node_available

    def _start_node_process(self) -> None:
        """Start long-running Node.js subprocess for batch resolution."""
        try:
            self._node_process = subprocess.Popen(
                ["node", str(self._node_helper_script)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            logger.debug(f"Started Node.js subprocess (PID: {self._node_process.pid})")
        except Exception as e:
            logger.warning(f"Failed to start Node.js subprocess: {e}")
            self._node_available = False
            self._node_process = None

    def cleanup(self) -> None:
        """Terminate the long-running Node.js subprocess."""
        if self._node_process:
            try:
                if self._node_process.stdin:
                    self._node_process.stdin.close()
                if self._node_process.stdout:
                    self._node_process.stdout.close()
                if self._node_process.stderr:
                    self._node_process.stderr.close()
                self._node_process.terminate()
                self._node_process.wait(timeout=2)
                logger.debug(
                    f"Terminated Node.js subprocess (PID: {self._node_process.pid})"
                )
            except Exception as e:
                logger.debug(f"Error during Node.js subprocess cleanup: {e}")
                try:
                    self._node_process.kill()
                except Exception:
                    pass
            finally:
                self._node_process = None

    def __del__(self) -> None:
        self.cleanup()

    def _build_workspace_paths(self) -> dict[str, list[str]] | None:
        """Build TypeScript paths mapping from workspace packages.

        Converts workspace package registry into paths entries that
        ts.resolveModuleName() can use for cross-package resolution.

        This generates two patterns per package:
        1. Wildcard pattern for subpath imports: "@scope/pkg/*" -> ["path/*"]
        2. Exact match for root imports: "@scope/pkg" -> ["path"]

        Returns:
            Dict mapping path patterns to filesystem paths, or None if
            no workspace resolver is available.

        Example:
            For package "@web-platform/shared-acorn-redux" at "libs/shared/acorn/redux":
            {
                "@web-platform/shared-acorn-redux/*": ["libs/shared/acorn/redux/*"],
                "@web-platform/shared-acorn-redux": ["libs/shared/acorn/redux"]
            }
        """
        if not self.workspace_resolver:
            return None

        paths: dict[str, list[str]] = {}

        assert self.workspace_resolver is not None
        for package in self.workspace_resolver.registry.all_packages():  # type: ignore[union-attr]
            try:
                relative_path = package.path.relative_to(self.repo_path)
            except ValueError:
                logger.debug(
                    f"Skipping package {package.name}: path {package.path} "
                    f"is outside repo {self.repo_path}"
                )
                continue

            pattern_wildcard = f"{package.name}/*"
            target_wildcard = f"{relative_path}/*"
            paths[pattern_wildcard] = [target_wildcard]

            entry = self._detect_package_entry_point(package.path)
            paths[package.name] = [entry] if entry else [str(relative_path)]

        if not paths:
            return None

        logger.debug(
            f"Built {len(paths)} workspace path mappings "
            f"({len(paths) // 2} packages with wildcard + exact patterns)"
        )
        return paths

    def _detect_package_entry_point(self, package_path: Path) -> str | None:
        pkg_json_path = package_path / cs.DEP_FILE_PACKAGE_JSON
        if not pkg_json_path.exists():
            return None

        try:
            with pkg_json_path.open() as f:
                pkg_data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        for field in cs.TSCONFIG_ENTRY_POINT_FIELDS:
            if value := pkg_data.get(field):
                if not isinstance(value, str):
                    continue
                entry_path = (package_path / value).resolve()
                entry_no_ext = entry_path.with_suffix("")
                for ext in _TS_JS_EXTENSIONS:
                    if entry_no_ext.with_suffix(ext).exists():
                        try:
                            rel = entry_no_ext.relative_to(self.repo_path)
                            return str(rel)
                        except ValueError:
                            continue
                if entry_path.exists():
                    try:
                        rel = entry_path.with_suffix("").relative_to(self.repo_path)
                        return str(rel)
                    except ValueError:
                        continue

        for fallback in cs.TSCONFIG_ENTRY_POINT_FALLBACKS:
            fallback_path = package_path / fallback
            for ext in _TS_JS_EXTENSIONS:
                if fallback_path.with_suffix(ext).exists():
                    try:
                        rel = fallback_path.relative_to(self.repo_path)
                        return str(rel)
                    except ValueError:
                        continue

        return None

    def _build_reference_paths(self) -> dict[str, list[str]] | None:
        if not self.tsconfig_resolver:
            return None

        root_tsconfig = self.repo_path / cs.TSCONFIG_JSON
        if not root_tsconfig.exists():
            return None

        return self.tsconfig_resolver.resolve_references(root_tsconfig) or None

    def _send_workspace_init(self) -> None:
        """Send workspace package paths to Node.js subprocess as init message.

        This must be called after _start_node_process() and whenever the
        subprocess is restarted. The init message injects workspace package
        mappings as synthetic TypeScript paths that ts.resolveModuleName()
        can use to resolve cross-package imports.

        Message format:
            {"init": true, "paths": {...}, "baseUrl": "/repo/path"}

        Expected response:
            {"init": true, "status": "ok", "pathCount": N}
        """
        if not self._node_process:
            logger.debug("No Node.js subprocess available for workspace init")
            return

        workspace_paths = self._build_workspace_paths() or {}
        reference_paths = self._build_reference_paths() or {}
        paths = {**workspace_paths, **reference_paths}

        if paths:
            logger.debug(
                ls.TSCONFIG_MERGED_PATHS.format(
                    workspace=len(workspace_paths),
                    reference=len(reference_paths),
                    total=len(paths),
                )
            )

        if not paths:
            logger.debug("No workspace paths to inject into Node.js resolver")
            return

        init_message = {
            "init": True,
            "paths": paths,
            "baseUrl": str(self.repo_path),
        }

        try:
            if not self._node_process.stdin or not self._node_process.stdout:
                logger.warning("Node.js subprocess stdin/stdout not available")
                return

            self._node_process.stdin.write(json.dumps(init_message) + "\n")  # type: ignore[union-attr]
            self._node_process.stdin.flush()  # type: ignore[union-attr]

            response_line = self._node_process.stdout.readline().strip()  # type: ignore[union-attr]

            if response_line:
                response = json.loads(response_line)
                if response.get("status") == "ok":
                    logger.info(
                        f"Injected {response.get('pathCount', 0)} workspace path "
                        f"mappings into TypeScript resolver subprocess"
                    )
                else:
                    logger.warning(
                        f"Unexpected init response from Node.js subprocess: {response}"
                    )
            else:
                logger.warning(
                    "No response from Node.js subprocess for workspace init message"
                )

        except json.JSONDecodeError as e:
            logger.warning(
                f"Failed to parse init response from Node.js subprocess: {e}"
            )
        except BrokenPipeError:
            logger.warning(
                "Pipe broken while sending workspace init to Node.js subprocess"
            )
        except Exception as e:
            logger.warning(f"Failed to send workspace init to Node.js subprocess: {e}")

    def resolve(self, import_specifier: str, from_file: Path) -> Path | None:
        """Resolve TypeScript/JavaScript import to filesystem path.

        Args:
            import_specifier: Import string (e.g., '@web-platform/shared-acorn-redux/src/utils')
            from_file: File containing the import

        Returns:
            Absolute filesystem path, or None if external
        """
        cache_key = (import_specifier, str(from_file))
        if cache_key in self._resolution_cache:
            return self._resolution_cache[cache_key]

        if import_specifier.startswith(("./", "../")):
            result = self._resolve_relative_import(import_specifier, from_file)
            self._resolution_cache[cache_key] = result
            return result

        if self._node_available and self._node_process:
            result = self._resolve_via_nodejs(import_specifier, from_file)

            if result.path is not None:
                self._resolution_cache[cache_key] = result.path
                return result.path

            if result.is_external is True:
                self._resolution_cache[cache_key] = None
                return None

        result = self._resolve_via_python(import_specifier, from_file)
        self._resolution_cache[cache_key] = result
        return result

    def _resolve_via_nodejs(
        self, import_specifier: str, from_file: Path
    ) -> ResolveResult:
        """Resolve using long-running Node.js subprocess.

        Returns:
            ResolveResult with path, is_external status, and error message
        """
        if not self._node_process or self._node_process.poll() is not None:
            logger.debug("Node.js subprocess not available, attempting restart")
            self._start_node_process()
            if self._node_process:
                self._send_workspace_init()
            if not self._node_process:
                return ResolveResult(
                    path=None, is_external=None, error="Node.js subprocess unavailable"
                )

        assert self._node_process is not None

        try:
            input_data = json.dumps(
                {"specifier": import_specifier, "fromFile": str(from_file.absolute())}
            )

            if not self._node_process.stdin or not self._node_process.stdout:
                return ResolveResult(
                    path=None,
                    is_external=None,
                    error="Subprocess stdin/stdout unavailable",
                )

            self._node_process.stdin.write(input_data + "\n")  # type: ignore[union-attr]
            self._node_process.stdin.flush()  # type: ignore[union-attr]

            output_line = self._node_process.stdout.readline().strip()  # type: ignore[union-attr]

            if not output_line:
                return ResolveResult(path=None, is_external=None, error="Empty output")

            result = json.loads(output_line)

            error_msg = result.get("error")
            if error_msg:
                logger.debug(
                    f"Node.js resolution error for {import_specifier}: {error_msg}"
                )

            is_external = result.get("isExternal")
            resolved_path_str = result.get("resolvedPath")

            if is_external is True:
                logger.debug(
                    f"External package detected (node_modules): {import_specifier}"
                )
                return ResolveResult(path=None, is_external=True, error=error_msg)

            if resolved_path_str:
                resolved_path = Path(resolved_path_str)
                logger.debug(f"Node.js resolved {import_specifier} -> {resolved_path}")
                return ResolveResult(path=resolved_path, is_external=False, error=None)

            logger.debug(
                f"Node.js couldn't resolve {import_specifier}, falling back to Python"
            )
            return ResolveResult(path=None, is_external=is_external, error=error_msg)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(
                f"Failed to parse Node.js resolution output for {import_specifier}: {e}"
            )
            return ResolveResult(path=None, is_external=None, error=str(e))
        except BrokenPipeError:
            logger.warning("Node.js subprocess pipe broken, restarting")
            self.cleanup()
            self._start_node_process()
            if self._node_process:
                self._send_workspace_init()
            return ResolveResult(path=None, is_external=None, error="Pipe broken")
        except Exception as e:
            logger.warning(
                f"Unexpected error during Node.js resolution for {import_specifier}: {e}"
            )
            return ResolveResult(path=None, is_external=None, error=str(e))

    def _resolve_via_python(
        self, import_specifier: str, from_file: Path
    ) -> Path | None:
        """Fallback Python-based resolution using tsconfig and workspace resolvers.

        Args:
            import_specifier: Import string
            from_file: File containing the import

        Returns:
            Absolute filesystem path, or None if external/unresolved
        """
        if self.tsconfig_resolver:
            try:
                from_module_parts = (
                    from_file.relative_to(self.repo_path).with_suffix("").parts
                )
                if from_module_parts and from_module_parts[-1] == "index":
                    from_module_parts = from_module_parts[:-1]
                from_module_qn = f"{self.project_name}.{'.'.join(from_module_parts)}"

                resolved_qn = self.tsconfig_resolver.resolve_path_mapping(
                    import_specifier, from_module_qn
                )
                if resolved_qn and resolved_qn.startswith(f"{self.project_name}."):
                    parts = resolved_qn[len(self.project_name) + 1 :].split(".")
                    resolved_path = self.repo_path / Path(*parts)
                    for ext in _TS_JS_EXTENSIONS:
                        file_with_ext = (
                            resolved_path.parent / f"{resolved_path.name}{ext}"
                        )
                        if file_with_ext.exists():
                            return file_with_ext
                    for ext in _TS_JS_EXTENSIONS:
                        index_path = resolved_path / f"index{ext}"
                        if index_path.exists():
                            return index_path
                    if resolved_path.exists():
                        return resolved_path
            except (ValueError, AttributeError) as e:
                logger.debug(f"tsconfig resolution failed for {import_specifier}: {e}")

        if self.workspace_resolver:
            package_name, subpath = self.workspace_resolver.normalize_package_name(
                import_specifier
            )

            if self.workspace_resolver.is_internal_package(package_name):
                package = self.workspace_resolver.get_package_info(package_name)
                if package:
                    if subpath:
                        resolved_path = package.path / subpath
                        if not resolved_path.suffix:
                            for ext in _TS_JS_EXTENSIONS:
                                file_path = Path(str(resolved_path) + ext)
                                if file_path.exists():
                                    return file_path
                            for ext in _TS_JS_EXTENSIONS:
                                index_path = resolved_path / f"index{ext}"
                                if index_path.exists():
                                    return index_path
                        return resolved_path if resolved_path.exists() else None
                    else:
                        for ext in _TS_JS_EXTENSIONS:
                            index_path = package.path / f"index{ext}"
                            if index_path.exists():
                                return index_path
                        return None

        logger.debug(f"External package (Python fallback): {import_specifier}")
        return None

    def is_external(self, import_specifier: str) -> bool:
        """Check if import is external.

        Args:
            import_specifier: Import string

        Returns:
            True if external (node_modules), False if internal
        """
        if import_specifier.startswith(("./", "../")):
            return False

        if self.workspace_resolver:
            package_name, _ = self.workspace_resolver.normalize_package_name(
                import_specifier
            )
            return not self.workspace_resolver.is_internal_package(package_name)

        return True

    def _resolve_relative_import(
        self, import_specifier: str, from_file: Path
    ) -> Path | None:
        """Resolve relative import (./, ../) to filesystem path.

        Args:
            import_specifier: Relative import string
            from_file: File containing the import

        Returns:
            Absolute filesystem path
        """
        current_dir = from_file.parent
        import_parts = import_specifier.split("/")

        for part in import_parts:
            if part == ".":
                continue
            elif part == "..":
                current_dir = current_dir.parent
            elif part:
                current_dir = current_dir / part

        if not current_dir.suffix:
            for ext in _TS_JS_EXTENSIONS:
                file_with_ext = current_dir.parent / f"{current_dir.name}{ext}"
                if file_with_ext.exists():
                    return file_with_ext
            for ext in _TS_JS_EXTENSIONS:
                index_path = current_dir / f"index{ext}"
                if index_path.exists():
                    return index_path

        return current_dir if current_dir.exists() else None
