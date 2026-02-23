from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from loguru import logger

from codebase_rag import constants as cs
from codebase_rag import logs as ls


class TypeScriptTypeResolver:
    def __init__(self, repo_path: Path, project_name: str) -> None:
        self.repo_path = repo_path
        self.project_name = project_name
        self._node_process: subprocess.Popen[str] | None = None
        self._is_available: bool = False
        self._cache: dict[Path, dict[str, dict[str, dict[str, str]]]] = {}

    def initialize(self) -> None:
        node_path = shutil.which("node")
        if not node_path:
            logger.debug(ls.TYPE_RESOLVER_UNAVAILABLE.format(reason="node_not_found"))
            return

        script_path = Path(__file__).parent / "scripts" / "ts_type_resolve.js"
        if not script_path.exists():
            logger.debug(ls.TYPE_RESOLVER_UNAVAILABLE.format(reason="script_not_found"))
            return

        try:
            self._node_process = subprocess.Popen(
                ["node", str(script_path)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except Exception as e:
            logger.debug(ls.TYPE_RESOLVER_ERROR.format(error=e))
            self._node_process = None
            return

        tsconfig_path = self.repo_path / cs.TSCONFIG_JSON
        init_message = {
            "init": True,
            "tsconfigPath": str(tsconfig_path),
        }

        try:
            if not self._node_process.stdin or not self._node_process.stdout:
                logger.debug(
                    ls.TYPE_RESOLVER_UNAVAILABLE.format(
                        reason="stdin_stdout_unavailable"
                    )
                )
                self.cleanup()
                return

            self._node_process.stdin.write(json.dumps(init_message) + "\n")
            self._node_process.stdin.flush()

            response_line = self._node_process.stdout.readline().strip()
            if not response_line:
                logger.debug(
                    ls.TYPE_RESOLVER_UNAVAILABLE.format(reason="no_init_response")
                )
                self.cleanup()
                return

            response = json.loads(response_line)
            status = response.get("status", "")

            if status == "ok":
                self._is_available = True
                logger.info(
                    ls.TYPE_RESOLVER_INIT.format(
                        status=status,
                        path=str(tsconfig_path),
                        count=response.get("fileCount", 0),
                    )
                )
            else:
                reason = response.get("reason", status)
                logger.debug(ls.TYPE_RESOLVER_UNAVAILABLE.format(reason=reason))
                self.cleanup()

        except (json.JSONDecodeError, BrokenPipeError, OSError) as e:
            logger.debug(ls.TYPE_RESOLVER_ERROR.format(error=e))
            self.cleanup()

    def resolve_function_types(
        self, file_path: Path
    ) -> dict[str, dict[str, dict[str, str]]]:
        if not self._is_available or not self._node_process:
            return {}

        if file_path in self._cache:
            return self._cache[file_path]

        if self._node_process.poll() is not None:
            logger.debug(ls.TYPE_RESOLVER_RESTART)
            self._restart_process()
            if not self._is_available:
                return {}

        try:
            if not self._node_process.stdin or not self._node_process.stdout:
                return {}

            query = {"file": str(file_path)}
            self._node_process.stdin.write(json.dumps(query) + "\n")
            self._node_process.stdin.flush()

            response_line = self._node_process.stdout.readline().strip()
            if not response_line:
                return {}

            response = json.loads(response_line)

            if response.get("error"):
                logger.debug(ls.TYPE_RESOLVER_ERROR.format(error=response["error"]))
                self._cache[file_path] = {}
                return {}

            functions = response.get("functions", {})
            self._cache[file_path] = functions

            func_count = len(functions)
            if func_count > 0:
                logger.debug(
                    ls.TYPE_RESOLVER_QUERY.format(
                        path=str(file_path), func_count=func_count
                    )
                )

            return functions

        except (json.JSONDecodeError, BrokenPipeError, OSError) as e:
            logger.debug(ls.TYPE_RESOLVER_ERROR.format(error=e))
            self._cache[file_path] = {}
            return {}

    def cleanup(self) -> None:
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
                logger.debug(ls.TYPE_RESOLVER_CLEANUP)
            except Exception:
                try:
                    self._node_process.kill()
                except Exception:
                    pass
            finally:
                self._node_process = None
                self._is_available = False

    def __del__(self) -> None:
        self.cleanup()

    @property
    def is_available(self) -> bool:
        return self._is_available

    def _restart_process(self) -> None:
        self.cleanup()
        self._cache.clear()
        self.initialize()
