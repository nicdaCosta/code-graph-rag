from __future__ import annotations

import json
from pathlib import Path

import pytest

from codebase_rag import constants as cs
from codebase_rag.parsers.js_ts.tsconfig_resolver import TsConfigResolver


@pytest.fixture
def tsconfig_workspace(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()

    lib_a = repo / "libs" / "lib-a"
    lib_a.mkdir(parents=True)
    (lib_a / "package.json").write_text(
        json.dumps({"name": "@scope/lib-a", "typings": "./src/index.ts"})
    )
    src_a = lib_a / "src"
    src_a.mkdir()
    (src_a / "index.ts").write_text("export const a = 1;")
    (src_a / "utils.ts").write_text("export const util = 2;")

    lib_b = repo / "libs" / "lib-b"
    lib_b.mkdir(parents=True)
    (lib_b / "package.json").write_text(
        json.dumps({"name": "@scope/lib-b", "main": "./dist/index.js"})
    )
    dist_b = lib_b / "dist"
    dist_b.mkdir()
    (dist_b / "index.js").write_text("module.exports = {};")

    lib_c = repo / "libs" / "lib-c"
    lib_c.mkdir(parents=True)
    (lib_c / "package.json").write_text(json.dumps({"name": "@scope/lib-c"}))
    src_c = lib_c / "src"
    src_c.mkdir()
    (src_c / "index.ts").write_text("export const c = 3;")

    lib_d = repo / "libs" / "lib-d"
    lib_d.mkdir(parents=True)
    (lib_d / "package.json").write_text(
        json.dumps({"name": "@scope/lib-d", "types": "./types/index.d.ts"})
    )
    types_d = lib_d / "types"
    types_d.mkdir()
    (types_d / "index.d.ts").write_text("export declare const d: number;")

    (repo / "tsconfig.json").write_text(
        json.dumps(
            {
                "compilerOptions": {"baseUrl": "."},
                "references": [
                    {"path": "libs/lib-a"},
                    {"path": "libs/lib-b"},
                    {"path": "libs/lib-c"},
                    {"path": "libs/lib-d"},
                ],
            }
        )
    )

    app_dir = repo / "apps" / "main"
    app_dir.mkdir(parents=True)
    (app_dir / "index.ts").write_text("import { a } from '@scope/lib-a';")

    return repo


class TestResolveReferences:
    def test_resolves_references_from_root_tsconfig(
        self, tsconfig_workspace: Path
    ) -> None:
        resolver = TsConfigResolver(tsconfig_workspace)
        root_tsconfig = tsconfig_workspace / cs.TSCONFIG_JSON
        paths = resolver.resolve_references(root_tsconfig)

        assert "@scope/lib-a" in paths
        assert "@scope/lib-a/*" in paths
        assert "@scope/lib-b" in paths
        assert "@scope/lib-c" in paths

    def test_entry_point_priority_typings_first(self, tsconfig_workspace: Path) -> None:
        resolver = TsConfigResolver(tsconfig_workspace)
        root_tsconfig = tsconfig_workspace / cs.TSCONFIG_JSON
        paths = resolver.resolve_references(root_tsconfig)

        # (H) typings field has highest priority -> src/index (without .ts extension)
        exact_target = paths["@scope/lib-a"][0]
        assert "src/index" in exact_target

    def test_entry_point_types_field(self, tsconfig_workspace: Path) -> None:
        resolver = TsConfigResolver(tsconfig_workspace)
        root_tsconfig = tsconfig_workspace / cs.TSCONFIG_JSON
        paths = resolver.resolve_references(root_tsconfig)

        exact_target = paths["@scope/lib-d"][0]
        assert "types/index" in exact_target

    def test_entry_point_main_field(self, tsconfig_workspace: Path) -> None:
        resolver = TsConfigResolver(tsconfig_workspace)
        root_tsconfig = tsconfig_workspace / cs.TSCONFIG_JSON
        paths = resolver.resolve_references(root_tsconfig)

        exact_target = paths["@scope/lib-b"][0]
        assert "dist/index" in exact_target

    def test_entry_point_fallback_src_index(self, tsconfig_workspace: Path) -> None:
        resolver = TsConfigResolver(tsconfig_workspace)
        root_tsconfig = tsconfig_workspace / cs.TSCONFIG_JSON
        paths = resolver.resolve_references(root_tsconfig)

        # (H) lib-c has no entry fields, falls back to src/index
        exact_target = paths["@scope/lib-c"][0]
        assert "src/index" in exact_target

    def test_reference_paths_cached(self, tsconfig_workspace: Path) -> None:
        resolver = TsConfigResolver(tsconfig_workspace)
        root_tsconfig = tsconfig_workspace / cs.TSCONFIG_JSON

        first = resolver.resolve_references(root_tsconfig)
        second = resolver.resolve_references(root_tsconfig)
        assert first is second

    def test_wildcard_patterns_generated(self, tsconfig_workspace: Path) -> None:
        resolver = TsConfigResolver(tsconfig_workspace)
        root_tsconfig = tsconfig_workspace / cs.TSCONFIG_JSON
        paths = resolver.resolve_references(root_tsconfig)

        wildcard_target = paths["@scope/lib-a/*"][0]
        assert wildcard_target.endswith("/*")
        assert "libs/lib-a" in wildcard_target


class TestResolvePathMappingWithReferences:
    def test_resolves_subpath_via_references(self, tsconfig_workspace: Path) -> None:
        resolver = TsConfigResolver(tsconfig_workspace)
        result = resolver.resolve_path_mapping(
            "@scope/lib-a/src/utils", "workspace.apps.main.index"
        )
        assert result is not None
        assert "utils" in result
        assert not result.startswith("@scope")

    def test_resolves_exact_match_via_references(
        self, tsconfig_workspace: Path
    ) -> None:
        resolver = TsConfigResolver(tsconfig_workspace)
        result = resolver.resolve_path_mapping(
            "@scope/lib-a", "workspace.apps.main.index"
        )
        assert result is not None
        assert "index" in result
        assert not result.startswith("@scope")

    def test_unknown_package_returns_none(self, tsconfig_workspace: Path) -> None:
        resolver = TsConfigResolver(tsconfig_workspace)
        result = resolver.resolve_path_mapping(
            "@unknown/package", "workspace.apps.main.index"
        )
        assert result is None
