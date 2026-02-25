import pytest
from tree_sitter import QueryCursor

from codebase_rag import constants as cs
from codebase_rag.parser_loader import load_parsers


def test_implicit_return_arrow_function_calls():
    """Test that calls inside implicit return arrow functions are tracked.

    This tests the pattern: () => ({...}) where the arrow function
    has an implicit return of an object literal.

    This is the CRITICAL issue causing 92% of function calls to be missing.
    """
    parsers, queries = load_parsers()

    code = """
    function getAllValidItineraryIds(state) {
        return state.ids;
    }

    function sponsoredFilterEnabled(state) {
        return state.sponsored;
    }

    const mapStateToProps = (state) => ({
        itineraryIds: getAllValidItineraryIds(state),
        isSponsoredFilterEnabled: sponsoredFilterEnabled(state),
    });
    """

    parser = parsers[cs.SupportedLanguage.TS]
    language_queries = queries[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    arrow_functions = []

    def find_arrow_functions(node):
        if node.type == cs.TS_ARROW_FUNCTION:
            arrow_functions.append(node)
        for child in node.children:
            find_arrow_functions(child)

    find_arrow_functions(root_node)
    assert len(arrow_functions) == 1, "Should find one arrow function"

    arrow_fn = arrow_functions[0]

    print("\n" + "=" * 60)
    print("ARROW FUNCTION STRUCTURE")
    print("=" * 60)
    print(f"Type: {arrow_fn.type}")
    print(f"Text: {arrow_fn.text.decode('utf-8')[:100]}...")
    print("\nChildren:")
    for i, child in enumerate(arrow_fn.children):
        text_preview = child.text.decode("utf-8")[:50] if child.text else "None"
        print(f"  [{i}] {child.type:30s} - {text_preview}...")

    body = None
    body_type = None
    for child in arrow_fn.children:
        if child.type == cs.TS_PARENTHESIZED_EXPRESSION:
            body = child
            body_type = "parenthesized_expression"
            print("\n✓ Found parenthesized_expression body")
            break
        elif child.type == cs.TS_STATEMENT_BLOCK:
            body = child
            body_type = "statement_block"
            print("\n✓ Found statement_block body")
            break

    assert body is not None, "Arrow function should have a body"

    call_query = language_queries.get(cs.QUERY_CALLS)
    assert call_query is not None, "Call query should be loaded"

    cursor = QueryCursor(call_query)
    captures = cursor.captures(arrow_fn)
    call_nodes = captures.get(cs.CAPTURE_CALL, [])

    print("\n" + "=" * 60)
    print(f"CALL EXTRACTION RESULTS (body_type={body_type})")
    print("=" * 60)
    print(f"Found {len(call_nodes)} call nodes:")
    for i, call_node in enumerate(call_nodes):
        call_text = call_node.text.decode("utf-8")
        print(f"  [{i + 1}] {call_text}")

    if len(call_nodes) != 2:
        print(f"\n❌ FAIL: Expected 2 calls, found {len(call_nodes)}")
        print("\nDEBUG: Body structure:")

        def print_tree(node, depth=0):
            indent = "  " * depth
            text_preview = node.text.decode("utf-8")[:40] if node.text else "None"
            print(f"{indent}{node.type}: {text_preview}...")
            for child in node.children:
                print_tree(child, depth + 1)

        print_tree(body)
        pytest.fail(f"Expected 2 calls, found {len(call_nodes)}")

    call_texts = [node.text.decode("utf-8") for node in call_nodes]
    assert any("getAllValidItineraryIds" in text for text in call_texts), (
        "Should find getAllValidItineraryIds call"
    )
    assert any("sponsoredFilterEnabled" in text for text in call_texts), (
        "Should find sponsoredFilterEnabled call"
    )

    print(
        "\n✅ TEST PASSED: Calls are correctly extracted from implicit return arrow function"
    )


def test_explicit_return_arrow_function_calls():
    """Test that explicit return arrow functions work (baseline/control)."""
    parsers, queries = load_parsers()

    code = """
    function getAllValidItineraryIds(state) {
        return state.ids;
    }

    const mapStateToProps = (state) => {
        return {
            itineraryIds: getAllValidItineraryIds(state),
        };
    };
    """

    parser = parsers[cs.SupportedLanguage.TS]
    language_queries = queries[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    arrow_functions = []

    def find_arrow_functions(node):
        if node.type == cs.TS_ARROW_FUNCTION:
            arrow_functions.append(node)
        for child in node.children:
            find_arrow_functions(child)

    find_arrow_functions(root_node)
    arrow_fn = arrow_functions[0]

    call_query = language_queries.get(cs.QUERY_CALLS)
    assert call_query is not None, "Call query should be loaded"

    cursor = QueryCursor(call_query)
    captures = cursor.captures(arrow_fn)
    call_nodes = captures.get(cs.CAPTURE_CALL, [])

    print("\n" + "=" * 60)
    print("EXPLICIT RETURN - CALL EXTRACTION RESULTS (CONTROL)")
    print("=" * 60)
    print(f"Found {len(call_nodes)} call nodes")

    assert len(call_nodes) == 1, f"Expected 1 call, found {len(call_nodes)}"
    assert b"getAllValidItineraryIds" in call_nodes[0].text

    print("\n✅ CONTROL TEST PASSED: Explicit return works correctly")


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
