import pytest

from codebase_rag import constants as cs
from codebase_rag.parser_loader import load_parsers


def test_arrow_function_name_field():
    """Test that arrow functions don't have a 'name' field."""
    parsers, queries = load_parsers()

    code = """
    const mapStateToProps = (state) => ({
        itineraryIds: getAllValidItineraryIds(state),
    });
    """

    parser = parsers[cs.SupportedLanguage.TS]
    tree = parser.parse(bytes(code, "utf-8"))
    root_node = tree.root_node

    def find_nodes_by_type(node, node_type):
        results = []
        if node.type == node_type:
            results.append(node)
        for child in node.children:
            results.extend(find_nodes_by_type(child, node_type))
        return results

    arrow_functions = find_nodes_by_type(root_node, cs.TS_ARROW_FUNCTION)
    assert len(arrow_functions) == 1, "Should find one arrow function"

    arrow_fn = arrow_functions[0]

    print("\n" + "=" * 60)
    print("ARROW FUNCTION NODE ANALYSIS")
    print("=" * 60)
    print(f"Arrow function type: {arrow_fn.type}")
    print("\nLooking for 'name' field...")
    name_node = arrow_fn.child_by_field_name(cs.FIELD_NAME)
    print(f"Result: {name_node}")

    if name_node is None:
        print("❌ Arrow function has NO 'name' field!")
    else:
        print(f"✓ Found name: {name_node.text.decode('utf-8')}")

    print("\nArrow function fields:")
    for child in arrow_fn.children:
        if child.is_named:
            field_name = None
            for field in ["name", "parameters", "body", "return_type"]:
                if arrow_fn.child_by_field_name(field) == child:
                    field_name = field
                    break
            print(f"  - {child.type:30s} field={field_name}")

    print("\nParent chain:")
    current = arrow_fn.parent
    depth = 1
    while current and depth < 5:
        print(f"  {depth}. {current.type}")
        if current.type == cs.TS_VARIABLE_DECLARATOR:
            print("     ^ This is the variable_declarator!")
            name_node = current.child_by_field_name(cs.FIELD_NAME)
            if name_node:
                print(f"     Name field: {name_node.text.decode('utf-8')}")
        current = current.parent
        depth += 1

    assert arrow_fn.child_by_field_name(cs.FIELD_NAME) is None, (
        "Arrow function should NOT have a 'name' field"
    )

    parent = arrow_fn.parent
    assert parent.type == cs.TS_VARIABLE_DECLARATOR, (
        f"Parent should be variable_declarator, got {parent.type}"
    )

    parent_name = parent.child_by_field_name(cs.FIELD_NAME)
    assert parent_name is not None, "Parent should have a 'name' field"
    assert parent_name.text.decode("utf-8") == "mapStateToProps", (
        f"Name should be 'mapStateToProps', got {parent_name.text.decode('utf-8')}"
    )

    print(
        "\n✅ TEST PASSED: Arrow function has no name field, parent variable_declarator does!"
    )


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v", "-s"]))
