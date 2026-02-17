from __future__ import annotations

import importlib.util

import pytest
from tree_sitter import Language, Parser

from codebase_rag.parsers.hash_generator import (
    generate_content_hash,
    generate_unique_hash,
)

JS_AVAILABLE = importlib.util.find_spec("tree_sitter_javascript") is not None

if JS_AVAILABLE:
    import tree_sitter_javascript as tsjs


@pytest.fixture
def js_parser() -> Parser | None:
    if not JS_AVAILABLE:
        return None
    language = Language(tsjs.language())
    return Parser(language)


@pytest.mark.skipif(not JS_AVAILABLE, reason="tree-sitter-javascript not available")
def test_identical_bodies_same_hash(js_parser: Parser) -> None:
    code1 = b"const x = () => console.log('hello');"
    code2 = b"const x = () => console.log('hello');"

    tree1 = js_parser.parse(code1)
    tree2 = js_parser.parse(code2)

    root1 = tree1.root_node
    root2 = tree2.root_node

    node1 = root1.child(0)
    node2 = root2.child(0)

    hash1 = generate_content_hash(node1)
    hash2 = generate_content_hash(node2)

    assert hash1 == hash2


@pytest.mark.skipif(not JS_AVAILABLE, reason="tree-sitter-javascript not available")
def test_different_bodies_different_hash(js_parser: Parser) -> None:
    code1 = b"const x = () => console.log('hello');"
    code2 = b"const x = () => console.log('world');"

    tree1 = js_parser.parse(code1)
    tree2 = js_parser.parse(code2)

    root1 = tree1.root_node
    root2 = tree2.root_node

    node1 = root1.child(0)
    node2 = root2.child(0)

    hash1 = generate_content_hash(node1)
    hash2 = generate_content_hash(node2)

    assert hash1 != hash2


@pytest.mark.skipif(not JS_AVAILABLE, reason="tree-sitter-javascript not available")
def test_whitespace_changes_same_hash(js_parser: Parser) -> None:
    code1 = b"const x = () => console.log('hello');"
    code2 = b"""const x = () =>
    console.log('hello');"""

    tree1 = js_parser.parse(code1)
    tree2 = js_parser.parse(code2)

    def find_arrow(node):
        if node.type == "arrow_function":
            return node
        for child in node.children:
            result = find_arrow(child)
            if result:
                return result
        return None

    arrow1 = find_arrow(tree1.root_node)
    arrow2 = find_arrow(tree2.root_node)

    assert arrow1 is not None
    assert arrow2 is not None

    hash1 = generate_content_hash(arrow1)
    hash2 = generate_content_hash(arrow2)

    assert hash1 == hash2


@pytest.mark.skipif(not JS_AVAILABLE, reason="tree-sitter-javascript not available")
def test_collision_appends_number(js_parser: Parser) -> None:
    code = b"const x = () => console.log('hello');"
    tree = js_parser.parse(code)
    root = tree.root_node

    node = root.child(0)

    base_hash = generate_content_hash(node)
    existing_hashes = {base_hash}

    unique_hash = generate_unique_hash(node, existing_hashes)

    assert unique_hash == f"{base_hash}_1"
    assert unique_hash not in {base_hash}


@pytest.mark.skipif(not JS_AVAILABLE, reason="tree-sitter-javascript not available")
def test_empty_node_fallback(js_parser: Parser) -> None:
    code = b"const x = () => {};"
    tree = js_parser.parse(code)
    root = tree.root_node

    node = root.child(0)

    if node and node.text:
        hash_result = generate_content_hash(node)
        assert len(hash_result) > 0
        assert isinstance(hash_result, str)
    else:
        hash_result = generate_content_hash(node)
        assert hash_result.startswith("pos")
