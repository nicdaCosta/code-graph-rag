import pytest
from tree_sitter import QueryCursor

from codebase_rag import constants as cs
from codebase_rag.parser_loader import load_parsers


def test_getter_setter_structure():
    """Test that getter/setter properties are correctly parsed."""
    parsers, queries = load_parsers()

    code = """
    var obj = {
        _value: 0,

        get value() {
            return this.getValue();
        },

        set value(v) {
            this.setValue(v);
        }
    };
    """

    parser = parsers[cs.SupportedLanguage.JS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("GETTER/SETTER AST STRUCTURE")
    print("=" * 60)

    def find_node_by_type(node, node_type):
        if node.type == node_type:
            return node
        for child in node.children:
            if result := find_node_by_type(child, node_type):
                return result
        return None

    obj = find_node_by_type(root_node, cs.TS_OBJECT)
    assert obj is not None, "Should find object"

    print("\nObject structure:")
    for i, child in enumerate(obj.children):
        if child.is_named:
            print(f"  [{i}] {child.type}")
            for j, subchild in enumerate(child.children):
                print(
                    f"      [{j}] {subchild.type}: {subchild.text.decode('utf-8')[:30] if subchild.text else 'None'}..."
                )

    methods = [child for child in obj.children if child.type == cs.TS_METHOD_DEFINITION]
    print(f"\nFound {len(methods)} method definitions")

    getter = None
    setter = None

    for method in methods:
        for child in method.children:
            if child.type == "get":
                getter = method
                print(f"\n✓ Found GETTER at line {method.start_point[0] + 1}")
            elif child.type == "set":
                setter = method
                print(f"\n✓ Found SETTER at line {method.start_point[0] + 1}")

    assert getter is not None, "Should find getter property"
    assert setter is not None, "Should find setter property"

    print("\n" + "=" * 60)
    print("CALL EXTRACTION FROM GETTER/SETTER")
    print("=" * 60)

    language_queries = queries[cs.SupportedLanguage.JS]
    call_query = language_queries.get(cs.QUERY_CALLS)
    assert call_query is not None

    cursor = QueryCursor(call_query)
    captures = cursor.captures(getter)
    getter_calls = captures.get(cs.CAPTURE_CALL, [])

    print(f"\nGetter calls found: {len(getter_calls)}")
    for call in getter_calls:
        print(f"  • {call.text.decode('utf-8')}")

    cursor = QueryCursor(call_query)
    captures = cursor.captures(setter)
    setter_calls = captures.get(cs.CAPTURE_CALL, [])

    print(f"\nSetter calls found: {len(setter_calls)}")
    for call in setter_calls:
        print(f"  • {call.text.decode('utf-8')}")

    assert len(getter_calls) == 1, (
        f"Getter should have 1 call (getValue), found {len(getter_calls)}"
    )
    assert b"getValue" in getter_calls[0].text, "Should find getValue call"

    assert len(setter_calls) == 1, (
        f"Setter should have 1 call (setValue), found {len(setter_calls)}"
    )
    assert b"setValue" in setter_calls[0].text, "Should find setValue call"

    print("\n✅ TEST PASSED: Getter/setter calls are correctly extracted!")


def test_getter_setter_in_class():
    parsers, queries = load_parsers()

    code = """
    class User {
        get fullName() {
            return this.getFirst() + this.getLast();
        }

        set fullName(name) {
            this.setName(parseName(name));
        }
    }
    """

    parser = parsers[cs.SupportedLanguage.JS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("CLASS GETTER/SETTER CALL EXTRACTION")
    print("=" * 60)

    def find_all_nodes_by_type(node, node_type, results=None):
        if results is None:
            results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            find_all_nodes_by_type(child, node_type, results)
        return results

    methods = find_all_nodes_by_type(root_node, cs.TS_METHOD_DEFINITION)
    print(f"\nFound {len(methods)} method definitions")

    language_queries = queries[cs.SupportedLanguage.JS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    total_calls = 0
    for method in methods:
        cursor = QueryCursor(call_query)
        captures = cursor.captures(method)
        calls = captures.get(cs.CAPTURE_CALL, [])
        total_calls += len(calls)

        print(f"\nMethod at line {method.start_point[0] + 1}: {len(calls)} calls")
        for call in calls:
            print(f"  • {call.text.decode('utf-8')}")

    assert total_calls >= 3, f"Should find at least 3 calls total, found {total_calls}"

    print("\n✅ TEST PASSED: Class getter/setter calls are extracted!")


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
