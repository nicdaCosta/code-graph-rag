from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from codebase_rag.tests.conftest import run_updater

JS_AVAILABLE = importlib.util.find_spec("tree_sitter_javascript") is not None
PY_AVAILABLE = importlib.util.find_spec("tree_sitter_python") is not None


@pytest.fixture
def function_ref_project(temp_repo: Path) -> Path:
    project_path = temp_repo / "function_ref_test"
    project_path.mkdir()
    (project_path / "src").mkdir()
    return project_path


@pytest.mark.skipif(not JS_AVAILABLE, reason="tree-sitter-javascript not available")
class TestFunctionReferenceTracking:
    def test_redux_selector_reference(
        self, function_ref_project: Path, mock_ingestor: MagicMock
    ) -> None:
        (function_ref_project / "src" / "selectors.js").write_text(
            "export const getAllIds = () => [1, 2, 3];"
        )
        (function_ref_project / "src" / "component.js").write_text(
            """
import { getAllIds } from './selectors';
const ids = useSelector(getAllIds);
"""
        )

        run_updater(function_ref_project, mock_ingestor)

        calls = [
            call
            for call in mock_ingestor.ensure_relationship_batch.call_args_list
            if call.args[1] == "CALLS" and "getAllIds" in str(call.args[2])
        ]
        assert len(calls) >= 1

    def test_array_map_callback(
        self, function_ref_project: Path, mock_ingestor: MagicMock
    ) -> None:
        (function_ref_project / "src" / "utils.js").write_text(
            "export const processItem = (x) => x * 2;"
        )
        (function_ref_project / "src" / "app.js").write_text(
            """
import { processItem } from './utils';
const items = [1, 2, 3];
const processed = items.map(processItem);
"""
        )

        run_updater(function_ref_project, mock_ingestor)

        calls = [
            call
            for call in mock_ingestor.ensure_relationship_batch.call_args_list
            if call.args[1] == "CALLS" and "processItem" in str(call.args[2])
        ]
        assert len(calls) >= 1

    def test_react_memo_component(
        self, function_ref_project: Path, mock_ingestor: MagicMock
    ) -> None:
        (function_ref_project / "src" / "Component.js").write_text(
            "export const MyComponent = () => <div>Hello</div>;"
        )
        (function_ref_project / "src" / "Memoized.js").write_text(
            """
import React from 'react';
import { MyComponent } from './Component';
const MemoizedComponent = React.memo(MyComponent);
"""
        )

        run_updater(function_ref_project, mock_ingestor)

        calls = [
            call
            for call in mock_ingestor.ensure_relationship_batch.call_args_list
            if call.args[1] == "CALLS" and "MyComponent" in str(call.args[2])
        ]
        assert len(calls) >= 1

    def test_higher_order_compose(
        self, function_ref_project: Path, mock_ingestor: MagicMock
    ) -> None:
        (function_ref_project / "src" / "functions.js").write_text(
            """
export const fn1 = (x) => x + 1;
export const fn2 = (x) => x * 2;
"""
        )
        (function_ref_project / "src" / "compose.js").write_text(
            """
import { fn1, fn2 } from './functions';
const composed = compose(fn1, fn2);
"""
        )

        run_updater(function_ref_project, mock_ingestor)

        calls = [
            call
            for call in mock_ingestor.ensure_relationship_batch.call_args_list
            if call.args[1] == "CALLS"
            and ("fn1" in str(call.args[2]) or "fn2" in str(call.args[2]))
        ]
        assert len(calls) >= 2

    def test_callback_pattern(
        self, function_ref_project: Path, mock_ingestor: MagicMock
    ) -> None:
        (function_ref_project / "src" / "handlers.js").write_text(
            "export const handleClick = () => console.log('clicked');"
        )
        (function_ref_project / "src" / "timer.js").write_text(
            """
import { handleClick } from './handlers';
setTimeout(handleClick, 1000);
"""
        )

        run_updater(function_ref_project, mock_ingestor)

        calls = [
            call
            for call in mock_ingestor.ensure_relationship_batch.call_args_list
            if call.args[1] == "CALLS" and "handleClick" in str(call.args[2])
        ]
        assert len(calls) >= 1

    def test_filters_non_functions(
        self, function_ref_project: Path, mock_ingestor: MagicMock
    ) -> None:
        (function_ref_project / "src" / "app.js").write_text(
            """
const x = 5;
const name = "test";
doSomething(x, 42, name);
"""
        )

        run_updater(function_ref_project, mock_ingestor)

        calls = [
            call
            for call in mock_ingestor.ensure_relationship_batch.call_args_list
            if call.args[1] == "CALLS"
        ]
        invalid_calls = [
            call
            for call in calls
            if any(
                substr in str(call.args[2])
                for substr in ["src.app.x", "src.app.name", "src.app.42"]
            )
        ]
        assert len(invalid_calls) == 0


@pytest.mark.skipif(not PY_AVAILABLE, reason="tree-sitter-python not available")
class TestPythonFunctionReferences:
    def test_python_map_builtin(
        self, function_ref_project: Path, mock_ingestor: MagicMock
    ) -> None:
        (function_ref_project / "utils.py").write_text(
            "def transform(x):\n    return x * 2"
        )
        (function_ref_project / "main.py").write_text(
            """
from utils import transform
items = [1, 2, 3]
result = map(transform, items)
"""
        )

        run_updater(function_ref_project, mock_ingestor)

        calls = [
            call
            for call in mock_ingestor.ensure_relationship_batch.call_args_list
            if call.args[1] == "CALLS" and "transform" in str(call.args[2])
        ]
        assert len(calls) >= 1
