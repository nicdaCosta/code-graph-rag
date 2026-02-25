import pytest
from tree_sitter import QueryCursor

from codebase_rag import constants as cs
from codebase_rag.parser_loader import load_parsers


def test_class_with_constructor():
    """Test class with constructor and method calls."""
    parsers, queries = load_parsers()

    code = """
    class UserService {
        constructor() {
            this.init();
            this.loadConfig();
        }

        init() {
            return this.setup();
        }

        loadConfig() {
            return this.fetchConfig();
        }
    }
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("CLASS WITH CONSTRUCTOR - CALL EXTRACTION")
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

    language_queries = queries[cs.SupportedLanguage.TS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    total_calls = 0
    for method in methods:
        name_node = method.child_by_field_name(cs.FIELD_NAME)
        method_name = (
            name_node.text.decode("utf-8")
            if name_node and name_node.text
            else "unknown"
        )

        cursor = QueryCursor(call_query)
        captures = cursor.captures(method)
        calls = captures.get(cs.CAPTURE_CALL, [])
        total_calls += len(calls)

        print(f"\nMethod '{method_name}': {len(calls)} calls")
        for call in calls:
            print(f"  • {call.text.decode('utf-8')}")

    assert total_calls >= 4, f"Should find at least 4 calls total, found {total_calls}"
    print(f"\n✅ TEST PASSED: Found {total_calls} calls in class methods")


def test_class_with_super_calls():
    """Test class inheritance with super calls."""
    parsers, queries = load_parsers()

    code = """
    class Base {
        initialize() {
            return this.setup();
        }
    }

    class Derived extends Base {
        constructor() {
            super();
            this.configure();
        }

        initialize() {
            super.initialize();
            return this.postInit();
        }
    }
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("CLASS INHERITANCE WITH SUPER CALLS")
    print("=" * 60)

    def find_all_nodes_by_type(node, node_type, results=None):
        if results is None:
            results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            find_all_nodes_by_type(child, node_type, results)
        return results

    classes = find_all_nodes_by_type(root_node, cs.TS_CLASS_DECLARATION)
    print(f"\nFound {len(classes)} classes")

    super_calls = find_all_nodes_by_type(root_node, cs.TS_SUPER)
    print(f"Found {len(super_calls)} super references")

    for super_node in super_calls:
        parent = super_node.parent
        print(f"\nSuper usage: type={parent.type if parent else 'None'}")
        if parent and parent.type == cs.TS_CALL_EXPRESSION:
            print("  • super() constructor call")
        elif parent and parent.type == cs.TS_MEMBER_EXPRESSION:
            print("  • super.method() call")

    assert len(super_calls) >= 2, (
        f"Should find at least 2 super references, found {len(super_calls)}"
    )
    print("\n✅ TEST PASSED: Super calls detected")


def test_class_static_methods():
    """Test static methods in classes."""
    parsers, queries = load_parsers()

    code = """
    class MathUtils {
        static add(a, b) {
            return this.calculate(a, b);
        }

        static calculate(a, b) {
            return a + b;
        }

        instanceMethod() {
            return MathUtils.add(1, 2);
        }
    }
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("CLASS STATIC METHODS")
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
    print(f"\nFound {len(methods)} methods")

    static_methods = []
    for method in methods:
        is_static = any(child.type == cs.TS_STATIC for child in method.children)
        name_node = method.child_by_field_name(cs.FIELD_NAME)
        method_name = (
            name_node.text.decode("utf-8")
            if name_node and name_node.text
            else "unknown"
        )

        if is_static:
            static_methods.append(method_name)
            print(f"  • static {method_name}")
        else:
            print(f"  • {method_name}")

    assert len(static_methods) >= 2, (
        f"Should find at least 2 static methods, found {len(static_methods)}"
    )
    print("\n✅ TEST PASSED: Static methods detected")


def test_class_getter_setter_comprehensive():
    """Test class getters/setters comprehensively (ES2015 vs ES5)."""
    parsers, queries = load_parsers()

    code = """
    class User {
        constructor() {
            this._firstName = '';
            this._lastName = '';
        }

        get fullName() {
            return this.computeFullName();
        }

        set fullName(value) {
            this.parseAndSet(value);
        }

        computeFullName() {
            return this._firstName + ' ' + this._lastName;
        }

        parseAndSet(value) {
            const [first, last] = this.splitName(value);
            this._firstName = first;
            this._lastName = last;
        }

        splitName(value) {
            return value.split(' ');
        }
    }
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("CLASS GETTER/SETTER COMPREHENSIVE")
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

    getter = None
    setter = None

    for method in methods:
        has_get = any(child.type == "get" for child in method.children)
        has_set = any(child.type == "set" for child in method.children)

        if has_get:
            getter = method
            print("\nFound GETTER")
        elif has_set:
            setter = method
            print("Found SETTER")

    assert getter is not None, "Should find getter"
    assert setter is not None, "Should find setter"

    language_queries = queries[cs.SupportedLanguage.TS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    cursor = QueryCursor(call_query)
    captures = cursor.captures(getter)
    getter_calls = captures.get(cs.CAPTURE_CALL, [])

    cursor = QueryCursor(call_query)
    captures = cursor.captures(setter)
    setter_calls = captures.get(cs.CAPTURE_CALL, [])

    print(f"\nGetter has {len(getter_calls)} calls:")
    for call in getter_calls:
        print(f"  • {call.text.decode('utf-8')}")

    print(f"\nSetter has {len(setter_calls)} calls:")
    for call in setter_calls:
        print(f"  • {call.text.decode('utf-8')}")

    assert len(getter_calls) >= 1, "Getter should have at least 1 call"
    assert len(setter_calls) >= 1, "Setter should have at least 1 call"

    print("\n✅ TEST PASSED: Getter/setter calls tracked correctly")


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
