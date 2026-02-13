import pytest

from codebase_rag import constants as cs
from codebase_rag.parser_loader import load_parsers


def test_object_destructuring_structure():
    """Test object destructuring AST structure."""
    parsers, queries = load_parsers()

    code = """
    const { getUserById, saveUser, deleteUser } = userService;
    getUserById(123);
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("OBJECT DESTRUCTURING AST STRUCTURE")
    print("=" * 60)

    def print_tree(node, depth=0):
        indent = "  " * depth
        text_preview = (
            node.text.decode("utf-8")[:40]
            if node.text and len(node.text) < 100
            else "None"
        )
        print(f"{indent}{node.type}: {text_preview}...")
        for child in node.children:
            if child.is_named:
                print_tree(child, depth + 1)

    print_tree(root_node)

    def find_node_by_type(node, node_type):
        if node.type == node_type:
            return node
        for child in node.children:
            if result := find_node_by_type(child, node_type):
                return result
        return None

    obj_pattern = find_node_by_type(root_node, cs.TS_OBJECT_PATTERN)
    print(
        f"\n{'✅' if obj_pattern else '❌'} Found object_pattern: {obj_pattern is not None}"
    )

    if obj_pattern:
        print("\nObject pattern children:")
        for i, child in enumerate(obj_pattern.children):
            if child.is_named:
                print(
                    f"  [{i}] {child.type}: {child.text.decode('utf-8') if child.text else 'None'}"
                )

    assert obj_pattern is not None, "Should find object_pattern for destructuring"


def test_object_destructuring_with_rename():
    """Test object destructuring with property renaming."""
    parsers, queries = load_parsers()

    code = """
    const { id: userId, name: userName } = user;
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("OBJECT DESTRUCTURING WITH RENAME")
    print("=" * 60)

    def print_tree(node, depth=0):
        indent = "  " * depth
        text_preview = node.text.decode("utf-8")[:40] if node.text else "None"
        print(f"{indent}{node.type}: {text_preview}...")
        for child in node.children:
            if child.is_named:
                print_tree(child, depth + 1)

    print_tree(root_node)


def test_array_destructuring_structure():
    """Test array destructuring AST structure."""
    parsers, queries = load_parsers()

    code = """
    const [first, second, third] = functions;
    first();
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("ARRAY DESTRUCTURING AST STRUCTURE")
    print("=" * 60)

    def print_tree(node, depth=0):
        indent = "  " * depth
        text_preview = node.text.decode("utf-8")[:40] if node.text else "None"
        print(f"{indent}{node.type}: {text_preview}...")
        for child in node.children:
            if child.is_named:
                print_tree(child, depth + 1)

    print_tree(root_node)

    def find_node_by_type(node, node_type):
        if node.type == node_type:
            return node
        for child in node.children:
            if result := find_node_by_type(child, node_type):
                return result
        return None

    array_pattern = find_node_by_type(root_node, cs.TS_ARRAY_PATTERN)
    print(
        f"\n{'✅' if array_pattern else '❌'} Found array_pattern: {array_pattern is not None}"
    )

    if array_pattern:
        print("\nArray pattern children:")
        for i, child in enumerate(array_pattern.children):
            if child.is_named:
                print(
                    f"  [{i}] {child.type}: {child.text.decode('utf-8') if child.text else 'None'}"
                )

    assert array_pattern is not None, "Should find array_pattern for destructuring"


def test_rest_element_in_destructuring():
    """Test rest element (...rest) in destructuring."""
    parsers, queries = load_parsers()

    code = """
    const { x, y, ...rest } = obj;
    const [head, ...tail] = array;
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("REST ELEMENT DESTRUCTURING")
    print("=" * 60)

    def print_tree(node, depth=0):
        indent = "  " * depth
        text_preview = node.text.decode("utf-8")[:40] if node.text else "None"
        print(f"{indent}{node.type}: {text_preview}...")
        for child in node.children:
            if child.is_named:
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

    rest_patterns = find_all_nodes_by_type(root_node, "rest_pattern")
    print(
        f"\n{'✅' if rest_patterns else '❌'} Found {len(rest_patterns)} rest_pattern nodes"
    )

    assert len(rest_patterns) >= 1, "Should find at least one rest_pattern"


def test_assignment_pattern_defaults():
    """Test default values in destructuring (AssignmentPattern)."""
    parsers, queries = load_parsers()

    code = """
    const { name = 'default', age = 0 } = user;
    const [first = null, second = undefined] = array;
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("ASSIGNMENT PATTERN (DEFAULT VALUES)")
    print("=" * 60)

    def print_tree(node, depth=0):
        indent = "  " * depth
        text_preview = node.text.decode("utf-8")[:40] if node.text else "None"
        print(f"{indent}{node.type}: {text_preview}...")
        for child in node.children:
            if child.is_named:
                print_tree(child, depth + 1)

    print_tree(root_node)


def test_function_parameter_destructuring():
    """Test destructuring in function parameters."""
    parsers, queries = load_parsers()

    code = """
    function process({ id, name }) {
        console.log(id, name);
    }

    const arrow = ([first, second]) => {
        return first + second;
    };
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    print("\n" + "=" * 60)
    print("FUNCTION PARAMETER DESTRUCTURING")
    print("=" * 60)

    def print_tree(node, depth=0):
        indent = "  " * depth
        text_preview = node.text.decode("utf-8")[:40] if node.text else "None"
        print(f"{indent}{node.type}: {text_preview}...")
        for child in node.children:
            if child.is_named:
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

    obj_patterns = find_all_nodes_by_type(root_node, cs.TS_OBJECT_PATTERN)
    array_patterns = find_all_nodes_by_type(root_node, cs.TS_ARRAY_PATTERN)

    print(f"\n✓ Found {len(obj_patterns)} object patterns in parameters")
    print(f"✓ Found {len(array_patterns)} array patterns in parameters")

    assert len(obj_patterns) >= 1, "Should find object pattern in function params"
    assert len(array_patterns) >= 1, (
        "Should find array pattern in arrow function params"
    )


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
