from __future__ import annotations

import json
from pathlib import Path

from loguru import logger


class TsConfigResolver:
    def __init__(self, repo_path: Path) -> None:
        self.repo_path = repo_path
        self.tsconfig_cache: dict[Path, dict] = {}

    def find_tsconfig_for_module(self, module_path: str) -> Path | None:
        module_parts = module_path.split(".")
        current = self.repo_path
        for part in module_parts[:-1]:
            current = current / part

        while current != self.repo_path.parent:
            tsconfig = current / "tsconfig.json"
            if tsconfig.exists():
                return tsconfig
            if current == self.repo_path:
                break
            current = current.parent

        root_tsconfig = self.repo_path / "tsconfig.json"
        return root_tsconfig if root_tsconfig.exists() else None

    def load_tsconfig(self, tsconfig_path: Path) -> dict:
        if tsconfig_path in self.tsconfig_cache:
            return self.tsconfig_cache[tsconfig_path]

        try:
            with tsconfig_path.open() as f:
                config = json.load(f)
        except Exception as e:
            logger.debug(f"Failed to load tsconfig at {tsconfig_path}: {e}")
            return {}

        if "extends" in config:
            extends_path_str = config["extends"]
            if extends_path_str.startswith("."):
                base_path = (tsconfig_path.parent / extends_path_str).resolve()
            else:
                base_path = tsconfig_path.parent / "node_modules" / extends_path_str
                if not base_path.exists():
                    base_path = tsconfig_path.parent / extends_path_str

            if base_path.exists():
                base_config = self.load_tsconfig(base_path)
                merged = {**base_config, **config}
                if "compilerOptions" in base_config:
                    merged["compilerOptions"] = {
                        **base_config.get("compilerOptions", {}),
                        **config.get("compilerOptions", {}),
                    }
                config = merged

        self.tsconfig_cache[tsconfig_path] = config
        return config

    def resolve_path_mapping(self, import_path: str, current_module: str) -> str | None:
        tsconfig_path = self.find_tsconfig_for_module(current_module)
        if not tsconfig_path:
            return None

        config = self.load_tsconfig(tsconfig_path)
        compiler_opts = config.get("compilerOptions", {})

        base_url = compiler_opts.get("baseUrl", ".")
        paths = compiler_opts.get("paths", {})

        for pattern, targets in paths.items():
            if "*" in pattern:
                prefix = pattern.split("*")[0]
                if import_path.startswith(prefix):
                    suffix = import_path[len(prefix) :]
                    for target in targets:
                        resolved = target.replace("*", suffix)
                        full_path = (
                            tsconfig_path.parent / base_url / resolved
                        ).resolve()

                        if self._path_exists_with_extensions(full_path):
                            try:
                                rel_path = full_path.relative_to(self.repo_path)
                                return str(rel_path).replace("/", ".")
                            except ValueError:
                                continue
            elif import_path == pattern:
                target = targets[0]
                full_path = (tsconfig_path.parent / base_url / target).resolve()

                if self._path_exists_with_extensions(full_path):
                    try:
                        rel_path = full_path.relative_to(self.repo_path)
                        return str(rel_path).replace("/", ".")
                    except ValueError:
                        continue

        if base_url and base_url != ".":
            base_path = (tsconfig_path.parent / base_url / import_path).resolve()
            if self._path_exists_with_extensions(base_path):
                try:
                    rel_path = base_path.relative_to(self.repo_path)
                    return str(rel_path).replace("/", ".")
                except ValueError:
                    pass

        return None

    def _path_exists_with_extensions(self, path: Path) -> bool:
        if path.exists():
            return True

        extensions = [".ts", ".tsx", ".js", ".jsx", ".d.ts"]
        for ext in extensions:
            if path.with_suffix(ext).exists():
                return True

        index_path = path / "index"
        for ext in extensions:
            if index_path.with_suffix(ext).exists():
                return True

        return False
