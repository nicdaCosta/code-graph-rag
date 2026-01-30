from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from loguru import logger

from ... import constants as cs
from ..utils import safe_decode_text
from .base import ComponentRelationship

if TYPE_CHECKING:
    from pathlib import Path

    from ...services import IngestorProtocol
    from ...types_defs import ASTNode, LanguageQueries, PropertyDict

STYLED_COMPONENT_IMPORTS = frozenset(
    {
        "styled-components",
        "@emotion/styled",
        "@emotion/react",
        "styled-jsx",
        "linaria",
        "@stitches/react",
    }
)

CSS_MODULE_PATTERNS = frozenset({".module.css", ".module.scss", ".module.sass"})


@dataclass
class StyledComponentInfo:
    name: str
    qualified_name: str
    base_element: str
    start_line: int
    end_line: int
    css_content: str | None = None
    library: str = "styled-components"
    is_exported: bool = False


@dataclass
class CssInJsRule:
    qualified_name: str
    selector: str
    start_line: int
    end_line: int
    properties: dict[str, str] = field(default_factory=dict)


class CssInJsIngestMixin:
    ingestor: IngestorProtocol
    repo_path: Path
    project_name: str

    def _ingest_css_in_js(
        self,
        root_node: ASTNode,
        module_qn: str,
        file_path: Path,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        if language not in cs.JS_TS_LANGUAGES:
            return

        imports = self._collect_css_in_js_imports(root_node)
        if not imports & STYLED_COMPONENT_IMPORTS:
            return

        library = self._detect_css_in_js_library(imports)
        styled_components = self._extract_styled_components(
            root_node, module_qn, library
        )
        relationships = self._extract_css_in_js_relationships(
            root_node, module_qn, styled_components
        )

        for sc in styled_components:
            props: PropertyDict = {
                cs.KEY_QUALIFIED_NAME: sc.qualified_name,
                cs.KEY_NAME: sc.name,
                "base_element": sc.base_element,
                "library": sc.library,
                cs.KEY_START_LINE: sc.start_line,
                cs.KEY_END_LINE: sc.end_line,
            }
            if sc.css_content:
                props["css_content"] = sc.css_content[:500]
            if sc.is_exported:
                props[cs.KEY_IS_EXPORTED] = True

            logger.debug(
                f"Styled component found: {sc.name} (extends {sc.base_element})"
            )
            self.ingestor.ensure_node_batch(cs.NodeLabel.STYLED_COMPONENT, props)

            self.ingestor.ensure_relationship_batch(
                (cs.NodeLabel.MODULE, cs.KEY_QUALIFIED_NAME, module_qn),
                cs.RelationshipType.DEFINES,
                (
                    cs.NodeLabel.STYLED_COMPONENT,
                    cs.KEY_QUALIFIED_NAME,
                    sc.qualified_name,
                ),
            )

        for rel in relationships:
            logger.debug(
                f"CSS-in-JS relationship: {rel.source_qn} -[{rel.relationship_type}]-> {rel.target_qn}"
            )
            self.ingestor.ensure_relationship_batch(
                (rel.source_label, cs.KEY_QUALIFIED_NAME, rel.source_qn),
                rel.relationship_type,
                (rel.target_label, cs.KEY_QUALIFIED_NAME, rel.target_qn),
            )

    def _collect_css_in_js_imports(self, root_node: ASTNode) -> set[str]:
        imports: set[str] = set()
        stack: list[ASTNode] = [root_node]

        while stack:
            node = stack.pop()

            if node.type == cs.TS_IMPORT_STATEMENT:
                source_node = node.child_by_field_name("source")
                if source_node and source_node.text:
                    import_path = source_node.text.decode(cs.ENCODING_UTF8)
                    import_path = import_path.strip("'\"")
                    imports.add(import_path)

            stack.extend(reversed(node.children))

        return imports

    def _detect_css_in_js_library(self, imports: set[str]) -> str:
        for imp in imports:
            if "emotion" in imp:
                return "emotion"
            if "styled-components" in imp:
                return "styled-components"
            if "styled-jsx" in imp:
                return "styled-jsx"
            if "linaria" in imp:
                return "linaria"
            if "stitches" in imp:
                return "stitches"
        return "styled-components"

    def _extract_styled_components(
        self, root_node: ASTNode, module_qn: str, library: str
    ) -> list[StyledComponentInfo]:
        styled_components: list[StyledComponentInfo] = []
        stack: list[ASTNode] = [root_node]

        while stack:
            node = stack.pop()

            if node.type == cs.TS_VARIABLE_DECLARATOR:
                if sc := self._extract_single_styled_component(
                    node, module_qn, library
                ):
                    styled_components.append(sc)

            stack.extend(reversed(node.children))

        logger.debug(f"Found {len(styled_components)} styled components in {module_qn}")
        return styled_components

    def _extract_single_styled_component(
        self, node: ASTNode, module_qn: str, library: str
    ) -> StyledComponentInfo | None:
        name_node = node.child_by_field_name(cs.FIELD_NAME)
        value_node = node.child_by_field_name(cs.FIELD_VALUE)

        if not name_node or not name_node.text or not value_node:
            return None

        name = safe_decode_text(name_node)
        if not name:
            return None

        if value_node.type == "tagged_template_expression":
            tag_node = value_node.child_by_field_name("tag")
            template_node = value_node.child_by_field_name("template")

            if not tag_node:
                return None

            base_element = self._extract_styled_base(tag_node)
            if not base_element:
                return None

            css_content = None
            if template_node and template_node.text:
                css_content = safe_decode_text(template_node)

            is_exported = self._is_node_exported(node)

            return StyledComponentInfo(
                name=name,
                qualified_name=f"{module_qn}{cs.SEPARATOR_DOT}{name}",
                base_element=base_element,
                start_line=node.start_point[0] + 1,
                end_line=node.end_point[0] + 1,
                css_content=css_content,
                library=library,
                is_exported=is_exported,
            )

        elif value_node.type == cs.TS_CALL_EXPRESSION:
            base_element = self._extract_styled_call_base(value_node)
            if base_element:
                is_exported = self._is_node_exported(node)
                return StyledComponentInfo(
                    name=name,
                    qualified_name=f"{module_qn}{cs.SEPARATOR_DOT}{name}",
                    base_element=base_element,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    library=library,
                    is_exported=is_exported,
                )

        return None

    def _extract_styled_base(self, tag_node: ASTNode) -> str | None:
        if tag_node.type == cs.TS_MEMBER_EXPRESSION:
            object_node = tag_node.child_by_field_name(cs.FIELD_OBJECT)
            property_node = tag_node.child_by_field_name(cs.FIELD_PROPERTY)

            if object_node and property_node:
                obj_text = safe_decode_text(object_node) if object_node.text else None
                prop_text = (
                    safe_decode_text(property_node) if property_node.text else None
                )

                if obj_text == "styled" and prop_text:
                    return prop_text

        elif tag_node.type == cs.TS_CALL_EXPRESSION:
            func_node = tag_node.child_by_field_name(cs.FIELD_FUNCTION)
            if func_node and func_node.type == cs.TS_MEMBER_EXPRESSION:
                return self._extract_styled_base(func_node)

        return None

    def _extract_styled_call_base(self, call_node: ASTNode) -> str | None:
        func_node = call_node.child_by_field_name(cs.FIELD_FUNCTION)
        if not func_node:
            return None

        func_text = safe_decode_text(func_node) if func_node.text else None
        if func_text and func_text.startswith("styled("):
            return None

        if func_node.type == cs.TS_CALL_EXPRESSION:
            inner_func = func_node.child_by_field_name(cs.FIELD_FUNCTION)
            if inner_func and inner_func.text:
                text = safe_decode_text(inner_func)
                if text == "styled":
                    args = func_node.child_by_field_name(cs.FIELD_ARGUMENTS)
                    if args and args.children:
                        for arg in args.children:
                            if arg.type == cs.TS_IDENTIFIER and arg.text:
                                return safe_decode_text(arg)

        return None

    def _is_node_exported(self, node: ASTNode) -> bool:
        parent = node.parent
        while parent:
            if parent.type == cs.TS_EXPORT_STATEMENT:
                return True
            if parent.type in (cs.TS_PROGRAM, "module"):
                break
            parent = parent.parent
        return False

    def _extract_css_in_js_relationships(
        self,
        root_node: ASTNode,
        module_qn: str,
        styled_components: list[StyledComponentInfo],
    ) -> list[ComponentRelationship]:
        relationships: list[ComponentRelationship] = []
        styled_names = {sc.name for sc in styled_components}
        styled_qns = {sc.name: sc.qualified_name for sc in styled_components}

        stack: list[ASTNode] = [root_node]
        while stack:
            node = stack.pop()

            if node.type in ("jsx_element", "jsx_self_closing_element"):
                tag_name = self._extract_jsx_tag_name(node)
                if tag_name and tag_name in styled_names:
                    parent_component = self._find_parent_react_component(
                        node, module_qn
                    )
                    if parent_component:
                        relationships.append(
                            ComponentRelationship(
                                source_qn=parent_component,
                                source_label=cs.NodeLabel.REACT_COMPONENT,
                                relationship_type=cs.RelationshipType.STYLED_WITH,
                                target_qn=styled_qns[tag_name],
                                target_label=cs.NodeLabel.STYLED_COMPONENT,
                            )
                        )

            stack.extend(reversed(node.children))

        return relationships

    def _extract_jsx_tag_name(self, node: ASTNode) -> str | None:
        for child in node.children:
            if child.type in ("jsx_opening_element", "jsx_self_closing_element"):
                for subchild in child.children:
                    if subchild.type == "identifier" and subchild.text:
                        return safe_decode_text(subchild)
            if child.type == "identifier" and child.text:
                return safe_decode_text(child)
        return None

    def _find_parent_react_component(self, node: ASTNode, module_qn: str) -> str | None:
        current = node.parent
        while current:
            if current.type == cs.TS_FUNCTION_DECLARATION:
                name_node = current.child_by_field_name(cs.FIELD_NAME)
                if name_node and name_node.text:
                    name = safe_decode_text(name_node)
                    if name and name[0].isupper():
                        return f"{module_qn}{cs.SEPARATOR_DOT}{name}"

            elif current.type == cs.TS_VARIABLE_DECLARATOR:
                name_node = current.child_by_field_name(cs.FIELD_NAME)
                if name_node and name_node.text:
                    name = safe_decode_text(name_node)
                    if name and name[0].isupper():
                        return f"{module_qn}{cs.SEPARATOR_DOT}{name}"

            current = current.parent

        return None
