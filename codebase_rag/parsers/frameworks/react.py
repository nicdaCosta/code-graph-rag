from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from ... import constants as cs
from ..utils import safe_decode_text
from .base import ComponentInfo, ComponentRelationship, FrameworkHandler, HookUsage

if TYPE_CHECKING:
    from pathlib import Path

    from ...types_defs import ASTNode

REACT_IMPORTS = frozenset(
    {
        "react",
        "React",
        "@types/react",
        "react-dom",
        "react/jsx-runtime",
        "react/jsx-dev-runtime",
    }
)

REACT_BUILTIN_HOOKS = frozenset(
    {
        "useState",
        "useEffect",
        "useContext",
        "useReducer",
        "useCallback",
        "useMemo",
        "useRef",
        "useImperativeHandle",
        "useLayoutEffect",
        "useDebugValue",
        "useDeferredValue",
        "useTransition",
        "useId",
        "useSyncExternalStore",
        "useInsertionEffect",
    }
)

JSX_ELEMENT_TYPES = frozenset(
    {
        "jsx_element",
        "jsx_self_closing_element",
    }
)


class ReactFrameworkHandler(FrameworkHandler):
    @property
    def framework_name(self) -> str:
        return "react"

    def detect_framework(self, imports: set[str]) -> bool:
        return bool(imports & REACT_IMPORTS)

    def extract_components(
        self,
        root_node: ASTNode,
        module_qn: str,
        file_path: Path,
    ) -> list[ComponentInfo]:
        components: list[ComponentInfo] = []

        stack: list[ASTNode] = [root_node]
        while stack:
            node = stack.pop()

            if self._is_function_component(node):
                if component := self._extract_function_component(node, module_qn):
                    components.append(component)
            elif self._is_class_component(node):
                if component := self._extract_class_component(node, module_qn):
                    components.append(component)
            elif self._is_arrow_function_component(node):
                if component := self._extract_arrow_component(node, module_qn):
                    components.append(component)

            stack.extend(reversed(node.children))

        logger.debug(f"Found {len(components)} React components in {module_qn}")
        return components

    def extract_hooks(
        self,
        root_node: ASTNode,
        module_qn: str,
        components: list[ComponentInfo],
    ) -> list[HookUsage]:
        hooks: list[HookUsage] = []
        component_ranges = {
            c.qualified_name: (c.start_line, c.end_line) for c in components
        }

        stack: list[ASTNode] = [root_node]
        while stack:
            node = stack.pop()

            if node.type == cs.TS_CALL_EXPRESSION:
                if hook := self._extract_hook_call(node, module_qn, component_ranges):
                    hooks.append(hook)

            stack.extend(reversed(node.children))

        logger.debug(f"Found {len(hooks)} hook usages in {module_qn}")
        return hooks

    def extract_relationships(
        self,
        root_node: ASTNode,
        module_qn: str,
        components: list[ComponentInfo],
    ) -> list[ComponentRelationship]:
        relationships: list[ComponentRelationship] = []
        component_names = {c.name for c in components}
        component_qns = {c.name: c.qualified_name for c in components}
        component_ranges = {
            c.qualified_name: (c.start_line, c.end_line) for c in components
        }

        stack: list[ASTNode] = [root_node]
        while stack:
            node = stack.pop()

            if node.type in JSX_ELEMENT_TYPES:
                rel = self._extract_renders_relationship(
                    node, module_qn, component_names, component_qns, component_ranges
                )
                if rel:
                    relationships.append(rel)

            stack.extend(reversed(node.children))

        logger.debug(
            f"Found {len(relationships)} component relationships in {module_qn}"
        )
        return relationships

    def _is_function_component(self, node: ASTNode) -> bool:
        if node.type != cs.TS_FUNCTION_DECLARATION:
            return False

        name_node = node.child_by_field_name(cs.FIELD_NAME)
        if not name_node or not name_node.text:
            return False

        name = safe_decode_text(name_node)
        if not name or not name[0].isupper():
            return False

        return self._returns_jsx(node)

    def _is_class_component(self, node: ASTNode) -> bool:
        if node.type != cs.TS_CLASS_DECLARATION:
            return False

        heritage_node = None
        for child in node.children:
            if child.type == cs.TS_CLASS_HERITAGE:
                heritage_node = child
                break

        if not heritage_node:
            return False

        heritage_text = safe_decode_text(heritage_node) if heritage_node.text else None
        if not heritage_text:
            return False
        return "React.Component" in heritage_text or "Component" in heritage_text

    def _is_arrow_function_component(self, node: ASTNode) -> bool:
        if node.type != cs.TS_VARIABLE_DECLARATOR:
            return False

        name_node = node.child_by_field_name(cs.FIELD_NAME)
        if not name_node or not name_node.text:
            return False

        name = safe_decode_text(name_node)
        if not name or not name[0].isupper():
            return False

        value_node = node.child_by_field_name(cs.FIELD_VALUE)
        if not value_node:
            return False

        if value_node.type != cs.TS_ARROW_FUNCTION:
            return False

        return self._returns_jsx(value_node)

    def _returns_jsx(self, node: ASTNode) -> bool:
        stack: list[ASTNode] = [node]
        while stack:
            current = stack.pop()

            if current.type in (
                "jsx_element",
                "jsx_self_closing_element",
                "jsx_fragment",
            ):
                return True

            if current.type == cs.TS_RETURN_STATEMENT:
                for child in current.children:
                    if child.type in (
                        "jsx_element",
                        "jsx_self_closing_element",
                        "jsx_fragment",
                        "parenthesized_expression",
                    ):
                        stack.append(child)

            stack.extend(reversed(current.children))

        return False

    def _extract_function_component(
        self, node: ASTNode, module_qn: str
    ) -> ComponentInfo | None:
        name_node = node.child_by_field_name(cs.FIELD_NAME)
        if not name_node or not name_node.text:
            return None

        name = safe_decode_text(name_node)
        if not name:
            return None

        qualified_name = f"{module_qn}{cs.SEPARATOR_DOT}{name}"
        props_interface = self._extract_props_interface(node)
        is_exported = self._is_exported(node)

        return ComponentInfo(
            name=name,
            qualified_name=qualified_name,
            component_type="function",
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            props_interface=props_interface,
            is_exported=is_exported,
        )

    def _extract_class_component(
        self, node: ASTNode, module_qn: str
    ) -> ComponentInfo | None:
        name_node = node.child_by_field_name(cs.FIELD_NAME)
        if not name_node or not name_node.text:
            return None

        name = safe_decode_text(name_node)
        if not name:
            return None

        qualified_name = f"{module_qn}{cs.SEPARATOR_DOT}{name}"
        is_exported = self._is_exported(node)

        return ComponentInfo(
            name=name,
            qualified_name=qualified_name,
            component_type="class",
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            is_exported=is_exported,
        )

    def _extract_arrow_component(
        self, node: ASTNode, module_qn: str
    ) -> ComponentInfo | None:
        name_node = node.child_by_field_name(cs.FIELD_NAME)
        if not name_node or not name_node.text:
            return None

        name = safe_decode_text(name_node)
        if not name:
            return None

        qualified_name = f"{module_qn}{cs.SEPARATOR_DOT}{name}"
        value_node = node.child_by_field_name(cs.FIELD_VALUE)
        props_interface = (
            self._extract_props_interface(value_node) if value_node else None
        )

        parent = node.parent
        is_exported = False
        while parent:
            if parent.type == cs.TS_EXPORT_STATEMENT:
                is_exported = True
                break
            if parent.type in (cs.TS_PROGRAM, "module"):
                break
            parent = parent.parent

        return ComponentInfo(
            name=name,
            qualified_name=qualified_name,
            component_type="arrow",
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            props_interface=props_interface,
            is_exported=is_exported,
        )

    def _extract_props_interface(self, node: ASTNode) -> str | None:
        params_node = node.child_by_field_name(cs.FIELD_PARAMETERS)
        if not params_node:
            return None

        for child in params_node.children:
            if child.type == "required_parameter":
                type_ann = child.child_by_field_name(cs.FIELD_TYPE)
                if type_ann and type_ann.text:
                    type_text = safe_decode_text(type_ann)
                    if type_text and type_text.startswith(":"):
                        return type_text[1:].strip()
                    return type_text

        return None

    def _is_exported(self, node: ASTNode) -> bool:
        parent = node.parent
        while parent:
            if parent.type == cs.TS_EXPORT_STATEMENT:
                return True
            if parent.type in (cs.TS_PROGRAM, "module"):
                break
            parent = parent.parent
        return False

    def _extract_hook_call(
        self,
        node: ASTNode,
        module_qn: str,
        component_ranges: dict[str, tuple[int, int]],
    ) -> HookUsage | None:
        func_node = node.child_by_field_name(cs.FIELD_FUNCTION)
        if not func_node or not func_node.text:
            return None

        func_name = safe_decode_text(func_node)
        if not func_name:
            return None

        if not func_name.startswith("use"):
            return None

        line = node.start_point[0] + 1
        containing_component = None
        for comp_qn, (start, end) in component_ranges.items():
            if start <= line <= end:
                containing_component = comp_qn
                break

        if not containing_component:
            return None

        is_builtin = func_name in REACT_BUILTIN_HOOKS
        hook_qn = f"react.{func_name}" if is_builtin else f"{module_qn}.{func_name}"

        return HookUsage(
            hook_name=func_name,
            qualified_name=hook_qn,
            component_qn=containing_component,
            start_line=line,
            is_builtin=is_builtin,
        )

    def _extract_renders_relationship(
        self,
        node: ASTNode,
        module_qn: str,
        component_names: set[str],
        component_qns: dict[str, str],
        component_ranges: dict[str, tuple[int, int]],
    ) -> ComponentRelationship | None:
        tag_name = self._extract_jsx_tag_name(node)
        if not tag_name:
            return None

        if not tag_name[0].isupper():
            return None

        if tag_name not in component_names:
            return None

        line = node.start_point[0] + 1
        source_component = None
        for comp_qn, (start, end) in component_ranges.items():
            if start <= line <= end:
                source_component = comp_qn
                break

        if not source_component:
            return None

        target_qn = component_qns.get(tag_name)
        if not target_qn or source_component == target_qn:
            return None

        return ComponentRelationship(
            source_qn=source_component,
            source_label=cs.NodeLabel.REACT_COMPONENT,
            relationship_type=cs.RelationshipType.RENDERS,
            target_qn=target_qn,
            target_label=cs.NodeLabel.REACT_COMPONENT,
        )

    def _extract_jsx_tag_name(self, node: ASTNode) -> str | None:
        for child in node.children:
            if child.type in ("jsx_opening_element", "jsx_self_closing_element"):
                for subchild in child.children:
                    if subchild.type == "identifier" and subchild.text:
                        return safe_decode_text(subchild)
            if child.type == "identifier" and child.text:
                return safe_decode_text(child)
        return None
