from __future__ import annotations

import pytest
from tree_sitter import Node, QueryCursor

from codebase_rag import constants as cs
from codebase_rag.parser_loader import load_parsers


@pytest.fixture(scope="module")
def ts_parser_and_queries():
    parsers, queries = load_parsers()
    return parsers[cs.SupportedLanguage.TS], queries[cs.SupportedLanguage.TS]


def _extract_calls_from_code(
    code: str,
    ts_parser_and_queries: tuple,
) -> list[str]:
    parser, queries = ts_parser_and_queries
    tree = parser.parse(bytes(code, "utf8"))
    root = tree.root_node

    call_query = queries.get("calls")
    if not call_query:
        return []

    cursor = QueryCursor(call_query)
    captures = cursor.captures(root)

    call_targets = []
    for node in captures.get(cs.CAPTURE_CALL, []):
        func_node = node.child_by_field_name(cs.FIELD_FUNCTION)
        if func_node and func_node.text:
            call_target = func_node.text.decode("utf8")
            call_targets.append(call_target)

    return call_targets


def _find_arrow_functions(node: Node) -> list[Node]:
    arrows = []
    if node.type == "arrow_function":
        arrows.append(node)

    for child in node.children:
        arrows.extend(_find_arrow_functions(child))

    return arrows


def _get_call_targets_in_node(
    node: Node,
    queries,
) -> list[str]:
    call_query = queries.get("calls")
    if not call_query:
        return []

    cursor = QueryCursor(call_query)
    captures = cursor.captures(node)

    call_targets = []
    for call_node in captures.get(cs.CAPTURE_NAME_CALL, []):
        func_node = call_node.child_by_field_name(cs.FIELD_FUNCTION)
        if func_node and func_node.text:
            call_target = func_node.text.decode("utf8")
            call_targets.append(call_target)

    return call_targets


class TestPhase0VariableDeclarator:
    def test_arrow_in_variable_declarator(self, ts_parser_and_queries):
        """Test arrow function assigned to a const variable."""
        code = """
        const mapStateToProps = (state) => {
            return getAllValidItineraryIds(state);
        };
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "getAllValidItineraryIds" in calls

    def test_arrow_with_implicit_return(self, ts_parser_and_queries):
        """Test arrow function with implicit return (no braces)."""
        code = """
        const selector = (state) => getAllValidItineraryIds(state);
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "getAllValidItineraryIds" in calls


class TestPhase1CallbackArguments:
    def test_arrow_in_use_selector(self, ts_parser_and_queries):
        """Test arrow function passed as callback to useSelector."""
        code = """
        function FlightsDayViewBase() {
            const hasItineraries = useSelector((state) => getAllValidItineraryIds(state).length);
        }
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "getAllValidItineraryIds" in calls

    def test_arrow_in_array_map(self, ts_parser_and_queries):
        """Test arrow function passed to array.map()."""
        code = """
        function processItems(items) {
            return items.map((item) => transform(item));
        }
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "transform" in calls

    def test_arrow_in_set_timeout(self, ts_parser_and_queries):
        """Test arrow function passed to setTimeout."""
        code = """
        function cleanup() {
            setTimeout(() => destroyResources(), 1000);
        }
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "destroyResources" in calls

    def test_arrow_in_use_memo(self, ts_parser_and_queries):
        """Test arrow function passed to useMemo."""
        code = """
        function Component() {
            const filtered = useMemo(() => getFilteredIds(state), [state]);
        }
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "getFilteredIds" in calls


class TestPhase2ObjectPropertyValues:
    def test_arrow_in_object_literal(self, ts_parser_and_queries):
        """Test arrow function as object property value."""
        code = """
        const handlers = {
            onClick: () => handleClick(),
            onHover: () => trackHover(),
        };
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "handleClick" in calls
        assert "trackHover" in calls

    def test_arrow_in_react_props(self, ts_parser_and_queries):
        """Test arrow function in React component props."""
        code = """
        const button = React.createElement('button', {
            onClick: () => submitForm(),
        });
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "submitForm" in calls

    def test_arrow_in_redux_connect(self, ts_parser_and_queries):
        """Test arrow function in Redux connect mapDispatch."""
        code = """
        export default connect(mapStateToProps, {
            fetchData: () => loadData(),
            clearData: () => resetStore(),
        });
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "loadData" in calls
        assert "resetStore" in calls


class TestPhase3AssignmentExpressions:
    def test_arrow_in_member_assignment(self, ts_parser_and_queries):
        """Test arrow function assigned to object property."""
        code = """
        const obj = {};
        obj.handler = () => process();
        obj.callback = () => notify();
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "process" in calls
        assert "notify" in calls

    def test_arrow_in_this_assignment(self, ts_parser_and_queries):
        """Test arrow function assigned to this property."""
        code = """
        class Controller {
            init() {
                this.onComplete = () => finalize();
            }
        }
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "finalize" in calls

    def test_arrow_in_module_exports(self, ts_parser_and_queries):
        """Test arrow function in module.exports assignment."""
        code = """
        module.exports = () => initialize();
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "initialize" in calls


class TestPhase4NestedArrows:
    def test_arrow_returning_arrow(self, ts_parser_and_queries):
        """Test arrow function that returns another arrow function."""
        code = """
        const createHandler = () => () => innerCall();
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "innerCall" in calls

    def test_nested_arrow_in_compose(self, ts_parser_and_queries):
        """Test nested arrow in compose/pipe function."""
        code = """
        const pipeline = compose(
            () => () => transform()
        );
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "transform" in calls

    def test_nested_arrow_callbacks(self, ts_parser_and_queries):
        """Test arrow inside arrow, both as callbacks."""
        code = """
        function process(items) {
            return items.map((item) => item.children.filter((child) => isValid(child)));
        }
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "isValid" in calls

    def test_curried_arrow_functions(self, ts_parser_and_queries):
        """Test curried arrow functions (multiple arrows)."""
        code = """
        const curry = (a) => (b) => (c) => compute(a, b, c);
        """

        calls = _extract_calls_from_code(code, ts_parser_and_queries)
        assert "compute" in calls
