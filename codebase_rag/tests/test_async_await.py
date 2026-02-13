import pytest
from tree_sitter import QueryCursor

from codebase_rag import constants as cs
from codebase_rag.parser_loader import load_parsers


def test_async_function_declaration():
    """Test async function declarations."""
    parsers, queries = load_parsers()

    code = """
    async function fetchUser(id) {
        const user = await getUser(id);
        return user;
    }
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("ASYNC FUNCTION DECLARATION")
    print("=" * 60)

    def print_tree(node, depth=0):
        indent = "  " * depth
        text_preview = node.text.decode("utf-8")[:40] if node.text else "None"
        print(f"{indent}{node.type}: {text_preview}...")
        for child in node.children:
            if child.is_named and depth < 3:
                print_tree(child, depth + 1)

    print_tree(root_node)

    def find_all_nodes_by_type(node, node_type, results=None):
        if results is None:
            results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            find_all_nodes_by_type(child, node_type, results)
        return results

    funcs = find_all_nodes_by_type(root_node, cs.TS_FUNCTION_DECLARATION)
    assert len(funcs) == 1, "Should find one function"

    func = funcs[0]
    has_async = any(child.type == "async" for child in func.children)
    print(f"\n✓ Function has async keyword: {has_async}")

    await_exprs = find_all_nodes_by_type(root_node, "await_expression")
    print(f"✓ Found {len(await_exprs)} await expressions")

    assert has_async, "Function should be async"
    assert len(await_exprs) >= 1, "Should find await expression"

    language_queries = queries[cs.SupportedLanguage.TS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    cursor = QueryCursor(call_query)
    captures = cursor.captures(func)
    calls = captures.get(cs.CAPTURE_CALL, [])

    print(f"\nCalls found in async function: {len(calls)}")
    for call in calls:
        print(f"  • {call.text.decode('utf-8')}")

    assert len(calls) >= 1, "Should find getUser() call"
    print("\n✅ TEST PASSED: Async function calls tracked")


def test_async_arrow_function():
    """Test async arrow functions."""
    parsers, queries = load_parsers()

    code = """
    const fetchData = async () => {
        const data = await getData();
        return data;
    };

    const fetchUser = async (id) => {
        return await getUser(id);
    };
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("ASYNC ARROW FUNCTIONS")
    print("=" * 60)

    def find_all_nodes_by_type(node, node_type, results=None):
        if results is None:
            results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            find_all_nodes_by_type(child, node_type, results)
        return results

    arrow_funcs = find_all_nodes_by_type(root_node, cs.TS_ARROW_FUNCTION)
    print(f"\nFound {len(arrow_funcs)} arrow functions")

    async_count = 0
    for arrow in arrow_funcs:
        parent = arrow.parent
        if parent and parent.type == cs.TS_VARIABLE_DECLARATOR:
            grandparent = parent.parent
            if grandparent:
                has_async = any(child.type == "async" for child in grandparent.children)
                if has_async:
                    async_count += 1
                    print("  ✓ Async arrow function found")

    async_arrows = []
    for arrow in arrow_funcs:
        current = arrow
        while current and current.type != "program":
            parent_children = current.parent.children if current.parent else []
            if any(child.type == "async" for child in parent_children):
                async_arrows.append(arrow)
                break
            current = current.parent

    print(f"\nAsync arrow functions detected: {max(async_count, len(async_arrows))}")

    await_exprs = find_all_nodes_by_type(root_node, "await_expression")
    print(f"Await expressions found: {len(await_exprs)}")

    assert len(await_exprs) >= 2, (
        f"Should find at least 2 await expressions, found {len(await_exprs)}"
    )

    language_queries = queries[cs.SupportedLanguage.TS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    cursor = QueryCursor(call_query)
    captures = cursor.captures(root_node)
    calls = captures.get(cs.CAPTURE_CALL, [])

    print(f"\nTotal calls found: {len(calls)}")
    for call in calls:
        print(f"  • {call.text.decode('utf-8')}")

    assert len(calls) >= 2, "Should find getData() and getUser() calls"
    print("\n✅ TEST PASSED: Async arrow function calls tracked")


def test_await_in_various_contexts():
    """Test await expressions in different contexts."""
    parsers, queries = load_parsers()

    code = """
    async function test() {
        const result = await fetch();

        await process(await getData());

        return await finalize();

        const sum = (await getA()) + (await getB());

        const arr = [await first(), await second()];

        const obj = {
            a: await getA(),
            b: await getB()
        };
    }
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("AWAIT IN VARIOUS CONTEXTS")
    print("=" * 60)

    def find_all_nodes_by_type(node, node_type, results=None):
        if results is None:
            results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            find_all_nodes_by_type(child, node_type, results)
        return results

    await_exprs = find_all_nodes_by_type(root_node, "await_expression")
    print(f"\nFound {len(await_exprs)} await expressions:")

    for i, await_expr in enumerate(await_exprs):
        context = await_expr.parent.type if await_expr.parent else "unknown"
        print(f"  {i + 1}. Context: {context}")

    language_queries = queries[cs.SupportedLanguage.TS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    cursor = QueryCursor(call_query)
    captures = cursor.captures(root_node)
    calls = captures.get(cs.CAPTURE_CALL, [])

    print(f"\nTotal calls found: {len(calls)}")

    assert len(calls) >= 9, f"Should find at least 9 calls, found {len(calls)}"
    print("\n✅ TEST PASSED: Await contexts handled correctly")


def test_async_class_methods():
    """Test async methods in classes."""
    parsers, queries = load_parsers()

    code = """
    class UserService {
        async fetchUser(id) {
            return await this.api.getUser(id);
        }

        async saveUser(user) {
            await this.validate(user);
            return await this.api.saveUser(user);
        }
    }
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("ASYNC CLASS METHODS")
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

    async_methods = []
    for method in methods:
        has_async = any(child.type == "async" for child in method.children)
        if has_async:
            name_node = method.child_by_field_name(cs.FIELD_NAME)
            method_name = (
                name_node.text.decode("utf-8")
                if name_node and name_node.text
                else "unknown"
            )
            async_methods.append(method_name)
            print(f"  ✓ Async method: {method_name}")

    assert len(async_methods) >= 2, (
        f"Should find 2 async methods, found {len(async_methods)}"
    )

    language_queries = queries[cs.SupportedLanguage.TS]
    call_query = language_queries.get(cs.QUERY_CALLS)

    total_calls = 0
    for method in methods:
        cursor = QueryCursor(call_query)
        captures = cursor.captures(method)
        calls = captures.get(cs.CAPTURE_CALL, [])
        total_calls += len(calls)

    print(f"\nTotal calls in async methods: {total_calls}")
    assert total_calls >= 3, f"Should find at least 3 calls, found {total_calls}"
    print("\n✅ TEST PASSED: Async class method calls tracked")


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
