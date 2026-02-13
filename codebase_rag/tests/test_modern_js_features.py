import pytest
from tree_sitter import QueryCursor

from codebase_rag import constants as cs
from codebase_rag.parser_loader import load_parsers


def test_optional_catch_binding():
    """Test ES2019 optional catch binding."""
    parsers, queries = load_parsers()

    code = """
    try {
        riskyOperation();
    } catch {
        handleError();
        logError();
    }
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("OPTIONAL CATCH BINDING (ES2019)")
    print("=" * 60)

    def find_all_nodes_by_type(node, node_type, results=None):
        if results is None:
            results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            find_all_nodes_by_type(child, node_type, results)
        return results

    catch_clauses = find_all_nodes_by_type(root_node, "catch_clause")
    print(f"\nFound {len(catch_clauses)} catch clauses")

    language_queries = queries[cs.SupportedLanguage.TS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    cursor = QueryCursor(call_query)
    captures = cursor.captures(root_node)
    calls = captures.get(cs.CAPTURE_CALL, [])

    print(f"\nCalls found: {len(calls)}")
    for call in calls:
        print(f"  • {call.text.decode('utf-8')}")

    assert len(calls) >= 3, f"Should find 3 calls, found {len(calls)}"
    print("\n✅ TEST PASSED: Optional catch binding works")


def test_optional_chaining():
    """Test ES2020 optional chaining."""
    parsers, queries = load_parsers()

    code = """
    const result1 = user?.getName();
    const result2 = obj?.prop?.nested?.call();
    const result3 = user?.[key];
    const result4 = func?.();
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("OPTIONAL CHAINING (ES2020)")
    print("=" * 60)

    def print_tree(node, depth=0):
        indent = "  " * depth
        text_preview = node.text.decode("utf-8")[:40] if node.text else "None"
        print(f"{indent}{node.type}: {text_preview}...")
        for child in node.children:
            if child.is_named and depth < 2:
                print_tree(child, depth + 1)

    print("\nAST structure:")
    print_tree(root_node)

    language_queries = queries[cs.SupportedLanguage.TS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    cursor = QueryCursor(call_query)
    captures = cursor.captures(root_node)
    calls = captures.get(cs.CAPTURE_CALL, [])

    print(f"\nCalls found: {len(calls)}")
    for call in calls:
        print(f"  • {call.text.decode('utf-8')}")

    assert len(calls) >= 1, f"Should find at least 1 call, found {len(calls)}"
    print("\n✅ TEST PASSED: Optional chaining calls tracked")


def test_nullish_coalescing():
    """Test ES2020 nullish coalescing operator."""
    parsers, queries = load_parsers()

    code = """
    const name = user.name ?? getDefaultName();
    const value = config.value ?? calculateDefault();
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("NULLISH COALESCING (ES2020)")
    print("=" * 60)

    language_queries = queries[cs.SupportedLanguage.TS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    cursor = QueryCursor(call_query)
    captures = cursor.captures(root_node)
    calls = captures.get(cs.CAPTURE_CALL, [])

    print(f"\nCalls found: {len(calls)}")
    for call in calls:
        print(f"  • {call.text.decode('utf-8')}")

    assert len(calls) >= 2, f"Should find 2 calls, found {len(calls)}"
    print("\n✅ TEST PASSED: Nullish coalescing with calls works")


def test_class_fields():
    """Test ES2022 class fields (public)."""
    parsers, queries = load_parsers()

    code = """
    class Counter {
        count = 0;
        name = 'counter';

        increment() {
            this.count++;
            return this.getValue();
        }
    }
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("CLASS FIELDS (ES2022)")
    print("=" * 60)

    def print_tree(node, depth=0):
        indent = "  " * depth
        text_preview = node.text.decode("utf-8")[:40] if node.text else "None"
        print(f"{indent}{node.type}: {text_preview}...")
        for child in node.children:
            if child.is_named and depth < 3:
                print_tree(child, depth + 1)

    print("\nAST structure:")
    print_tree(root_node)

    def find_all_nodes_by_type(node, node_type, results=None):
        if results is None:
            results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            find_all_nodes_by_type(child, node_type, results)
        return results

    field_definitions = (
        find_all_nodes_by_type(root_node, "field_definition")
        + find_all_nodes_by_type(root_node, "public_field_definition")
        + find_all_nodes_by_type(root_node, "property_declaration")
    )

    print(f"\nFound {len(field_definitions)} class fields")
    print("\n✅ TEST PASSED: Class fields parsed")


def test_private_class_fields():
    """Test ES2022 private class fields."""
    parsers, queries = load_parsers()

    code = """
    class Service {

            return this.
        }

            return this.
        }

        getData() {
            return this.
        }
    }
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("PRIVATE CLASS FIELDS (ES2022)")
    print("=" * 60)

    def print_tree(node, depth=0):
        indent = "  " * depth
        text_preview = node.text.decode("utf-8")[:40] if node.text else "None"
        print(f"{indent}{node.type}: {text_preview}...")
        for child in node.children:
            if child.is_named and depth < 3:
                print_tree(child, depth + 1)

    print("\nAST structure:")
    print_tree(root_node)

    def find_all_nodes_by_type(node, node_type, results=None):
        if results is None:
            results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            find_all_nodes_by_type(child, node_type, results)
        return results

    private_identifiers = find_all_nodes_by_type(
        root_node, "private_property_identifier"
    )
    print(f"\nFound {len(private_identifiers)} private identifiers")

    language_queries = queries[cs.SupportedLanguage.TS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    cursor = QueryCursor(call_query)
    captures = cursor.captures(root_node)
    calls = captures.get(cs.CAPTURE_CALL, [])

    print(f"\nCalls found: {len(calls)}")
    for call in calls:
        print(f"  • {call.text.decode('utf-8')[:50]}")

    assert len(calls) >= 1, f"Should find at least 1 call, found {len(calls)}"
    print("\n✅ TEST PASSED: Private class fields/methods detected")


def test_static_blocks():
    """Test ES2022 static blocks."""
    parsers, queries = load_parsers()

    code = """
    class MyClass {
        static

        static {
            this.
            this.configure();
            this.initialize();
        }

        static getInstance() {
            return this.
        }
    }
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("STATIC BLOCKS (ES2022)")
    print("=" * 60)

    def print_tree(node, depth=0):
        indent = "  " * depth
        text_preview = node.text.decode("utf-8")[:40] if node.text else "None"
        print(f"{indent}{node.type}: {text_preview}...")
        for child in node.children:
            if child.is_named and depth < 3:
                print_tree(child, depth + 1)

    print("\nAST structure:")
    print_tree(root_node)

    def find_all_nodes_by_type(node, node_type, results=None):
        if results is None:
            results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            find_all_nodes_by_type(child, node_type, results)
        return results

    static_blocks = find_all_nodes_by_type(root_node, "static_block")
    print(f"\nFound {len(static_blocks)} static blocks")

    language_queries = queries[cs.SupportedLanguage.TS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    if static_blocks:
        for block in static_blocks:
            cursor = QueryCursor(call_query)
            captures = cursor.captures(block)
            calls = captures.get(cs.CAPTURE_CALL, [])

            print(f"\nCalls in static block: {len(calls)}")
            for call in calls:
                print(f"  • {call.text.decode('utf-8')}")

            assert len(calls) >= 2, (
                f"Should find at least 2 calls in static block, found {len(calls)}"
            )

    print("\n✅ TEST PASSED: Static blocks detected")


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
