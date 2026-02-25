from pathlib import Path

from codebase_rag import constants as cs
from codebase_rag.graph_updater import FunctionRegistryTrie
from codebase_rag.parsers.import_processor import ImportProcessor
from codebase_rag.parsers.js_ts.tsconfig_resolver import TsConfigResolver
from codebase_rag.parsers.resolvers.factory import create_module_resolver
from codebase_rag.parsers.workspace.factory import WorkspaceResolverFactory
from codebase_rag.types_defs import NodeType


def test_get_all_valid_itinerary_ids_cross_package_resolution(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    (workspace / "pnpm-workspace.yaml").write_text(
        """packages:
  - 'libs/*'
  - 'apps/*'
"""
    )

    (workspace / "package.json").write_text(
        """{
  "name": "workspace",
  "private": true,
  "workspaces": ["libs/*", "apps/*"]
}"""
    )

    redux_package = workspace / "libs" / "shared-acorn-redux"
    redux_package.mkdir(parents=True)
    (redux_package / "package.json").write_text(
        """{
  "name": "@web-platform/shared-acorn-redux",
  "version": "1.0.0",
  "main": "src/index.ts"
}"""
    )

    selectors_dir = redux_package / "src" / "selectors"
    selectors_dir.mkdir(parents=True)
    valid_itineraries_file = selectors_dir / "validItineraries.ts"
    valid_itineraries_file.write_text(
        """import { createSelector } from 'reselect';

export interface Itinerary {
    id: string;
    isValid: boolean;
}

/**
 * Gets all valid itinerary IDs from the Redux store.
 * @returns Array of valid itinerary ID strings
 */
export function getAllValidItineraryIds(state: any): string[] {
    const validItineraries = state.validItineraries || [];
    return validItineraries.filter((it: Itinerary) => it.isValid).map((it: Itinerary) => it.id);
}

export const selectValidItineraryIds = createSelector(
    getAllValidItineraryIds,
    (ids) => ids
);
"""
    )

    app_package = workspace / "apps" / "flights-day-view"
    app_package.mkdir(parents=True)
    (app_package / "package.json").write_text(
        """{
  "name": "flights-day-view",
  "version": "1.0.0",
  "dependencies": {
    "@web-platform/shared-acorn-redux": "workspace:*"
  }
}"""
    )

    flights_day_view_file = app_package / "FlightsDayView.tsx"
    flights_day_view_file.write_text(
        """import React from 'react';
import { useSelector } from 'react-redux';
import { getAllValidItineraryIds } from '@web-platform/shared-acorn-redux/src/selectors/validItineraries';

interface Props {
    date: string;
}

export function FlightsDayView({ date }: Props) {
    const validIds = useSelector(getAllValidItineraryIds);

    return (
        <div className="flights-day-view">
            <h1>Flights for {date}</h1>
            <p>Valid itineraries: {validIds.length}</p>
        </div>
    );
}
"""
    )

    ws_factory = WorkspaceResolverFactory(workspace, "workspace")
    workspace_resolver = ws_factory.create_resolver()

    assert workspace_resolver.is_internal_package("@web-platform/shared-acorn-redux")
    package_info = workspace_resolver.get_package_info(
        "@web-platform/shared-acorn-redux"
    )
    assert package_info is not None
    assert package_info.path == redux_package

    tsconfig_resolver = TsConfigResolver(workspace)

    module_resolver = create_module_resolver(
        language=cs.SupportedLanguage.TS,
        repo_path=workspace,
        project_name="workspace",
        workspace_resolver=workspace_resolver,
        tsconfig_resolver=tsconfig_resolver,
    )

    function_registry = FunctionRegistryTrie()
    import_processor = ImportProcessor(
        repo_path=workspace,
        project_name="workspace",
        function_registry=function_registry,
        workspace_resolver=workspace_resolver,
        module_resolver=module_resolver,
    )
    import_processor.tsconfig_resolver = tsconfig_resolver

    expected_function_qn = "workspace.libs.shared-acorn-redux.src.selectors.validItineraries.getAllValidItineraryIds"

    function_registry[expected_function_qn] = NodeType.FUNCTION

    assert expected_function_qn in function_registry

    import_specifier = "@web-platform/shared-acorn-redux/src/selectors/validItineraries"
    resolved_path = module_resolver.resolve(import_specifier, flights_day_view_file)
    assert resolved_path == valid_itineraries_file, (
        f"Module resolver should resolve {import_specifier} to {valid_itineraries_file}, "
        f"got {resolved_path}"
    )

    assert not module_resolver.is_external(import_specifier)

    current_module = "workspace.apps.flights-day-view.FlightsDayView"

    resolved_qn = import_processor._resolve_js_module_path(
        import_specifier, current_module, cs.SupportedLanguage.TS
    )

    assert (
        resolved_qn
        == "workspace.libs.shared-acorn-redux.src.selectors.validItineraries"
    ), (
        f"Import processor should resolve {import_specifier} to filesystem-based QN, "
        f"got {resolved_qn}"
    )

    full_function_qn = f"{resolved_qn}.getAllValidItineraryIds"
    assert full_function_qn == expected_function_qn
    assert full_function_qn in function_registry


def test_npm_scoped_qn_does_not_match_function_registry(tmp_path: Path) -> None:
    function_registry = FunctionRegistryTrie()

    filesystem_qn = "workspace.libs.shared-acorn-redux.src.selectors.validItineraries.getAllValidItineraryIds"
    function_registry[filesystem_qn] = NodeType.FUNCTION

    npm_scoped_qn = "@web-platform.shared-acorn-redux.src.selectors.validItineraries.getAllValidItineraryIds"

    assert filesystem_qn in function_registry
    assert npm_scoped_qn not in function_registry

    assert filesystem_qn is not None
