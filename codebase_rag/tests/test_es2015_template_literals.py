import pytest
from tree_sitter import QueryCursor

from codebase_rag import constants as cs
from codebase_rag.parser_loader import load_parsers


def test_template_literal_structure():
    """Test basic template literal parsing."""
    parsers, queries = load_parsers()

    code = """
    const name = 'World';
    const greeting = `Hello ${name}!`;
    const multiline = `
        Line 1
        Line 2
    `;
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("TEMPLATE LITERAL STRUCTURE")
    print("=" * 60)

    def find_all_nodes_by_type(node, node_type, results=None):
        if results is None:
            results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            find_all_nodes_by_type(child, node_type, results)
        return results

    template_strings = find_all_nodes_by_type(root_node, "template_string")
    print(f"\nFound {len(template_strings)} template strings")

    for i, template in enumerate(template_strings):
        print(f"\nTemplate {i + 1}:")
        print(f"  Text: {template.text.decode('utf-8')[:50]}...")
        print(
            f"  Children: {[child.type for child in template.children if child.is_named]}"
        )

    assert len(template_strings) >= 2, (
        f"Should find at least 2 template strings, found {len(template_strings)}"
    )
    print("\n✅ TEST PASSED: Template literals parsed correctly")


def test_template_literal_with_calls():
    """Test calls inside template literal substitutions."""
    parsers, queries = load_parsers()

    code = """
    const result = `User: ${getUser().name}, Age: ${calculateAge()}`;
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("TEMPLATE LITERAL WITH CALLS")
    print("=" * 60)

    language_queries = queries[cs.SupportedLanguage.TS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    cursor = QueryCursor(call_query)
    captures = cursor.captures(root_node)
    calls = captures.get(cs.CAPTURE_CALL, [])

    print(f"\nFound {len(calls)} calls in template literal:")
    for call in calls:
        print(f"  • {call.text.decode('utf-8')}")

    assert len(calls) >= 2, f"Should find at least 2 calls, found {len(calls)}"
    print("\n✅ TEST PASSED: Calls in template substitutions are tracked")


def test_tagged_template_basic():
    """Test tagged template expressions."""
    parsers, queries = load_parsers()

    code = """
    function myTag(strings, ...values) {
        return strings[0] + values[0];
    }

    const result = myTag`Hello ${name}!`;
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("TAGGED TEMPLATE BASIC")
    print("=" * 60)

    def find_all_nodes_by_type(node, node_type, results=None):
        if results is None:
            results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            find_all_nodes_by_type(child, node_type, results)
        return results

    def print_tree(node, depth=0):
        indent = "  " * depth
        text_preview = node.text.decode("utf-8")[:40] if node.text else "None"
        print(f"{indent}{node.type}: {text_preview}...")
        for child in node.children:
            if child.is_named and depth < 3:
                print_tree(child, depth + 1)

    print("\nAST structure:")
    print_tree(root_node)

    call_exprs = find_all_nodes_by_type(root_node, cs.TS_CALL_EXPRESSION)
    print(f"\nFound {len(call_exprs)} call expressions")

    tagged_templates = 0
    for call in call_exprs:
        has_template = any(
            child.type in {"template_string", "arguments"} for child in call.children
        )
        if has_template:
            tagged_templates += 1
            print("\nTagged template call:")
            print(f"  • {call.text.decode('utf-8')[:60]}...")

    print(f"\n✓ Found {tagged_templates} tagged template expressions")


def test_styled_components_pattern():
    """Test styled-components pattern (common in React)."""
    parsers, queries = load_parsers()

    code = """
    import styled from 'styled-components';

    const Button = styled.button`
        color: ${props => props.theme.primary};
        background: ${props => getColor(props)};
    `;
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("STYLED-COMPONENTS PATTERN")
    print("=" * 60)

    language_queries = queries[cs.SupportedLanguage.TS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    cursor = QueryCursor(call_query)
    captures = cursor.captures(root_node)
    calls = captures.get(cs.CAPTURE_CALL, [])

    print(f"\nFound {len(calls)} calls:")
    for call in calls:
        text = call.text.decode("utf-8")
        print(f"  • {text[:60]}{'...' if len(text) > 60 else ''}")

    has_getColor = any(b"getColor" in call.text for call in calls)
    assert has_getColor, "Should find getColor call inside template"

    print("\n✅ TEST PASSED: Styled-components pattern calls tracked")


def test_nested_template_literals():
    """Test nested template literals."""
    parsers, queries = load_parsers()

    code = """
    const outer = `Outer: ${`Inner: ${getValue()}`}`;
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("NESTED TEMPLATE LITERALS")
    print("=" * 60)

    language_queries = queries[cs.SupportedLanguage.TS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    cursor = QueryCursor(call_query)
    captures = cursor.captures(root_node)
    calls = captures.get(cs.CAPTURE_CALL, [])

    print(f"\nFound {len(calls)} calls in nested templates:")
    for call in calls:
        print(f"  • {call.text.decode('utf-8')}")

    assert len(calls) >= 1, f"Should find getValue() call, found {len(calls)}"
    print("\n✅ TEST PASSED: Nested template calls tracked")


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
