from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from ... import constants as cs
from ...types_defs import ASTNode, PropertyDict

if TYPE_CHECKING:
    from ...services import IngestorProtocol
    from ...types_defs import LanguageQueries


class HtmlIngestMixin:
    ingestor: IngestorProtocol
    repo_path: Path
    project_name: str

    def _ingest_html_elements(
        self,
        root_node: ASTNode,
        module_qn: str,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        if language != cs.SupportedLanguage.HTML:
            return

        self._process_html_elements_recursive(root_node, module_qn, 0)

    def _process_html_elements_recursive(
        self, node: ASTNode, module_qn: str, element_index: int
    ) -> int:
        for child in node.children:
            if child.type == "element":
                element_index = self._process_html_element(
                    child, module_qn, element_index
                )
            element_index = self._process_html_elements_recursive(
                child, module_qn, element_index
            )
        return element_index

    def _process_html_element(
        self, element_node: ASTNode, module_qn: str, element_index: int
    ) -> int:
        start_tag = None
        for child in element_node.children:
            if child.type == "start_tag":
                start_tag = child
                break

        if not start_tag:
            return element_index

        tag_name = self._extract_tag_name(start_tag)
        if not tag_name:
            return element_index

        element_id = self._extract_attribute(start_tag, "id")
        element_classes = self._extract_attribute(start_tag, "class")

        if not element_id and not element_classes:
            return element_index

        element_qn = f"{module_qn}.{tag_name}_{element_index}"
        if element_id:
            element_qn = f"{module_qn}.{tag_name}#{element_id}"

        element_props: PropertyDict = {
            cs.KEY_QUALIFIED_NAME: element_qn,
            cs.KEY_NAME: tag_name,
            "tag_name": tag_name,
            cs.KEY_START_LINE: element_node.start_point[0] + 1,
            cs.KEY_END_LINE: element_node.end_point[0] + 1,
        }

        if element_id:
            element_props["element_id"] = element_id
        if element_classes:
            element_props["element_classes"] = element_classes

        logger.debug(
            f"HTML element found: <{tag_name}> id={element_id} class={element_classes}"
        )
        self.ingestor.ensure_node_batch(cs.NodeLabel.HTML_ELEMENT, element_props)

        self.ingestor.ensure_relationship_batch(
            (cs.NodeLabel.MODULE, cs.KEY_QUALIFIED_NAME, module_qn),
            cs.RelationshipType.DEFINES,
            (cs.NodeLabel.HTML_ELEMENT, cs.KEY_QUALIFIED_NAME, element_qn),
        )

        return element_index + 1

    def _extract_tag_name(self, start_tag: ASTNode) -> str | None:
        for child in start_tag.children:
            if child.type == "tag_name":
                return child.text.decode(cs.ENCODING_UTF8) if child.text else None
        return None

    def _extract_attribute(self, start_tag: ASTNode, attr_name: str) -> str | None:
        for child in start_tag.children:
            if child.type == "attribute":
                name_node = None
                value_node = None
                for attr_child in child.children:
                    if attr_child.type == "attribute_name":
                        name_node = attr_child
                    elif attr_child.type in (
                        "attribute_value",
                        "quoted_attribute_value",
                    ):
                        value_node = attr_child

                if name_node and name_node.text:
                    name = name_node.text.decode(cs.ENCODING_UTF8)
                    if name == attr_name and value_node and value_node.text:
                        value = value_node.text.decode(cs.ENCODING_UTF8)
                        return value.strip("'\"")
        return None

    def _ingest_stylesheet_references(
        self,
        root_node: ASTNode,
        module_qn: str,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        if language != cs.SupportedLanguage.HTML:
            return

        self._process_link_tags_recursive(root_node, module_qn)

    def _process_link_tags_recursive(self, node: ASTNode, module_qn: str) -> None:
        for child in node.children:
            if child.type == "element":
                self._check_for_stylesheet_link(child, module_qn)
            self._process_link_tags_recursive(child, module_qn)

    def _check_for_stylesheet_link(self, element_node: ASTNode, module_qn: str) -> None:
        start_tag = None
        for child in element_node.children:
            if child.type == "start_tag":
                start_tag = child
                break

        if not start_tag:
            return

        tag_name = self._extract_tag_name(start_tag)
        if tag_name != "link":
            return

        rel = self._extract_attribute(start_tag, "rel")
        href = self._extract_attribute(start_tag, "href")

        if rel == "stylesheet" and href:
            logger.debug(f"Stylesheet reference found: {href}")

            self.ingestor.ensure_relationship_batch(
                (cs.NodeLabel.MODULE, cs.KEY_QUALIFIED_NAME, module_qn),
                cs.RelationshipType.REFERENCES_STYLESHEET,
                (cs.NodeLabel.MODULE, cs.KEY_NAME, href),
            )
