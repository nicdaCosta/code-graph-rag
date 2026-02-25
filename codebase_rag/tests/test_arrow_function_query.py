import pytest
from tree_sitter import QueryCursor

from codebase_rag import constants as cs
from codebase_rag.parser_loader import load_parsers


def test_arrow_function_captured_by_function_query():
    """Test that const arrow functions are found by the FUNCTIONS query."""
    parsers, queries = load_parsers()

    code = """
    const mapStateToProps = (state) => ({
        itineraryIds: getAllValidItineraryIds(state),
    });
    """

    parser = parsers[cs.SupportedLanguage.TS]
    language_queries = queries[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    function_query = language_queries.get(cs.QUERY_FUNCTIONS)
    assert function_query is not None, "Function query should be loaded"

    cursor = QueryCursor(function_query)
    captures = cursor.captures(root_node)
    function_nodes = captures.get(cs.CAPTURE_FUNCTION, [])

    print("\n" + "=" * 60)
    print("FUNCTION QUERY RESULTS")
    print("=" * 60)
    print(f"Found {len(function_nodes)} function nodes")
    for i, func_node in enumerate(function_nodes):
        print(
            f"  [{i + 1}] type={func_node.type}, text={func_node.text.decode('utf-8')[:50]}..."
        )

    if len(function_nodes) == 0:
        print("\n❌ FAIL: Arrow function NOT captured by function query!")
        print("\nDEBUG: Full AST:")

        def print_tree(node, depth=0):
            indent = "  " * depth
            text_preview = node.text.decode("utf-8")[:40] if node.text else "None"
            print(f"{indent}{node.type}: {text_preview}...")
            for child in node.children:
                print_tree(child, depth + 1)

        print_tree(root_node)
        pytest.fail("Arrow function not captured by FUNCTIONS query")

    arrow_funcs = [n for n in function_nodes if n.type == cs.TS_ARROW_FUNCTION]
    assert len(arrow_funcs) > 0, "Should have at least one arrow_function node"

    print("\n✅ TEST PASSED: Arrow function IS captured by function query")


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
