from __future__ import annotations

import hashlib
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..types_defs import ASTNode


def generate_content_hash(node: ASTNode, prefix_length: int = 8) -> str:
    """
    Generate deterministic hash from tree-sitter node body.

    Args:
        node: Tree-sitter AST node (arrow_function, function_expression, etc.)
        prefix_length: Number of characters to take from SHA256 hash

    Returns:
        Hash string (e.g., "a1b2c3d4" for prefix_length=8)
    """
    if not node.text:
        return f"pos{node.start_point[0]}_{node.start_point[1]}"

    text = node.text.decode("utf-8", errors="replace")
    normalized = re.sub(r"\s+", " ", text).strip()

    hash_obj = hashlib.sha256(normalized.encode("utf-8"))
    full_hash = hash_obj.hexdigest()

    return full_hash[:prefix_length]


def generate_unique_hash(
    node: ASTNode, existing_hashes: set[str], prefix_length: int = 8
) -> str:
    """
    Generate hash with collision detection.

    If hash already exists, append _1, _2, etc.

    Args:
        node: Tree-sitter AST node
        existing_hashes: Set of hashes already used in this context
        prefix_length: Hash prefix length

    Returns:
        Unique hash string (e.g., "a1b2c3d4" or "a1b2c3d4_1")
    """
    base_hash = generate_content_hash(node, prefix_length)

    if base_hash not in existing_hashes:
        return base_hash

    counter = 1
    while f"{base_hash}_{counter}" in existing_hashes:
        counter += 1

    return f"{base_hash}_{counter}"
