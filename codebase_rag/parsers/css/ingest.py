from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from ... import constants as cs
from ...types_defs import ASTNode, PropertyDict

if TYPE_CHECKING:
    from ...services import IngestorProtocol
    from ...types_defs import LanguageQueries


class CssIngestMixin:
    ingestor: IngestorProtocol
    repo_path: Path
    project_name: str

    def _ingest_css_rules(
        self,
        root_node: ASTNode,
        module_qn: str,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        if language not in (cs.SupportedLanguage.CSS, cs.SupportedLanguage.SCSS):
            return

        self._process_css_rule_sets(root_node, module_qn)

    def _process_css_rule_sets(self, root_node: ASTNode, module_qn: str) -> None:
        for child in root_node.children:
            if child.type == "rule_set":
                self._process_single_rule_set(child, module_qn)
            elif child.type in ("stylesheet", "block"):
                self._process_css_rule_sets(child, module_qn)

    def _process_single_rule_set(self, rule_node: ASTNode, module_qn: str) -> None:
        selectors_node = rule_node.child_by_field_name("selectors")
        if not selectors_node:
            for child in rule_node.children:
                if child.type == "selectors":
                    selectors_node = child
                    break

        if not selectors_node:
            return

        selector_text = (
            selectors_node.text.decode(cs.ENCODING_UTF8)
            if selectors_node.text
            else None
        )
        if not selector_text:
            return

        rule_qn = f"{module_qn}.{selector_text.replace(' ', '_').replace(',', '_')}"

        rule_props: PropertyDict = {
            cs.KEY_QUALIFIED_NAME: rule_qn,
            cs.KEY_NAME: selector_text,
            cs.KEY_START_LINE: rule_node.start_point[0] + 1,
            cs.KEY_END_LINE: rule_node.end_point[0] + 1,
        }

        logger.debug(f"CSS rule found: {selector_text}")
        self.ingestor.ensure_node_batch(cs.NodeLabel.CSS_RULE, rule_props)

        self.ingestor.ensure_relationship_batch(
            (cs.NodeLabel.MODULE, cs.KEY_QUALIFIED_NAME, module_qn),
            cs.RelationshipType.DEFINES_STYLE,
            (cs.NodeLabel.CSS_RULE, cs.KEY_QUALIFIED_NAME, rule_qn),
        )

        self._extract_and_store_selectors(selectors_node, rule_qn)

    def _extract_and_store_selectors(
        self, selectors_node: ASTNode, rule_qn: str
    ) -> None:
        for child in selectors_node.children:
            self._process_selector_node(child, rule_qn)

    def _process_selector_node(self, node: ASTNode, rule_qn: str) -> None:
        if node.type == "class_selector":
            self._store_selector(node, rule_qn, "class")
        elif node.type == "id_selector":
            self._store_selector(node, rule_qn, "id")
        elif node.type in ("tag_name", "type_selector"):
            self._store_selector(node, rule_qn, "tag")
        elif node.type in ("descendant_selector", "child_selector", "selector"):
            for child in node.children:
                self._process_selector_node(child, rule_qn)

    def _store_selector(self, node: ASTNode, rule_qn: str, selector_type: str) -> None:
        selector_text = node.text.decode(cs.ENCODING_UTF8) if node.text else None
        if not selector_text:
            return

        selector_props: PropertyDict = {
            cs.KEY_NAME: selector_text,
            "selector_type": selector_type,
            cs.KEY_START_LINE: node.start_point[0] + 1,
            cs.KEY_END_LINE: node.end_point[0] + 1,
        }

        logger.debug(f"CSS selector found: {selector_text} (type: {selector_type})")
        self.ingestor.ensure_node_batch(cs.NodeLabel.CSS_SELECTOR, selector_props)

        self.ingestor.ensure_relationship_batch(
            (cs.NodeLabel.CSS_RULE, cs.KEY_QUALIFIED_NAME, rule_qn),
            cs.RelationshipType.HAS_SELECTOR,
            (cs.NodeLabel.CSS_SELECTOR, cs.KEY_NAME, selector_text),
        )

    def _ingest_scss_variables(
        self,
        root_node: ASTNode,
        module_qn: str,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        if language != cs.SupportedLanguage.SCSS:
            return

        self._process_scss_variables_recursive(root_node, module_qn)

    def _process_scss_variables_recursive(self, node: ASTNode, module_qn: str) -> None:
        for child in node.children:
            if child.type == "declaration" and child.text:
                text = child.text.decode(cs.ENCODING_UTF8)
                if text.startswith("$"):
                    self._process_scss_variable(child, module_qn)
            self._process_scss_variables_recursive(child, module_qn)

    def _process_scss_variable(self, node: ASTNode, module_qn: str) -> None:
        if not node.text:
            return

        text = node.text.decode(cs.ENCODING_UTF8)
        if ":" not in text:
            return

        var_name = text.split(":")[0].strip()
        var_value = text.split(":", 1)[1].strip().rstrip(";")
        var_qn = f"{module_qn}.{var_name}"

        var_props: PropertyDict = {
            cs.KEY_QUALIFIED_NAME: var_qn,
            cs.KEY_NAME: var_name,
            "value": var_value,
            cs.KEY_START_LINE: node.start_point[0] + 1,
            cs.KEY_END_LINE: node.end_point[0] + 1,
        }

        logger.debug(f"SCSS variable found: {var_name} = {var_value}")
        self.ingestor.ensure_node_batch(cs.NodeLabel.SCSS_VARIABLE, var_props)

        self.ingestor.ensure_relationship_batch(
            (cs.NodeLabel.MODULE, cs.KEY_QUALIFIED_NAME, module_qn),
            cs.RelationshipType.DEFINES,
            (cs.NodeLabel.SCSS_VARIABLE, cs.KEY_QUALIFIED_NAME, var_qn),
        )

    def _ingest_scss_at_rules(
        self,
        root_node: ASTNode,
        module_qn: str,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        if language != cs.SupportedLanguage.SCSS:
            return

        self._process_at_rules_recursive(root_node, module_qn)

    def _process_at_rules_recursive(self, node: ASTNode, module_qn: str) -> None:
        for child in node.children:
            if child.type == "at_rule":
                self._process_at_rule(child, module_qn)
            self._process_at_rules_recursive(child, module_qn)

    def _process_at_rule(self, node: ASTNode, module_qn: str) -> None:
        if not node.text:
            return

        text = node.text.decode(cs.ENCODING_UTF8)

        if text.startswith("@mixin"):
            self._process_mixin_definition(node, module_qn, text)
        elif text.startswith("@function"):
            self._process_function_definition(node, module_qn, text)
        elif text.startswith("@import") or text.startswith("@use"):
            self._process_scss_import(node, module_qn, text)

    def _process_mixin_definition(
        self, node: ASTNode, module_qn: str, text: str
    ) -> None:
        parts = text.split("(")[0].split()
        if len(parts) < 2:
            return

        mixin_name = parts[1]
        mixin_qn = f"{module_qn}.{mixin_name}"

        params = ""
        if "(" in text and ")" in text:
            params = text.split("(")[1].split(")")[0]

        mixin_props: PropertyDict = {
            cs.KEY_QUALIFIED_NAME: mixin_qn,
            cs.KEY_NAME: mixin_name,
            cs.KEY_PARAMETERS: params,
            cs.KEY_START_LINE: node.start_point[0] + 1,
            cs.KEY_END_LINE: node.end_point[0] + 1,
        }

        logger.debug(f"SCSS mixin found: {mixin_name}")
        self.ingestor.ensure_node_batch(cs.NodeLabel.SCSS_MIXIN, mixin_props)

        self.ingestor.ensure_relationship_batch(
            (cs.NodeLabel.MODULE, cs.KEY_QUALIFIED_NAME, module_qn),
            cs.RelationshipType.DEFINES,
            (cs.NodeLabel.SCSS_MIXIN, cs.KEY_QUALIFIED_NAME, mixin_qn),
        )

    def _process_function_definition(
        self, node: ASTNode, module_qn: str, text: str
    ) -> None:
        parts = text.split("(")[0].split()
        if len(parts) < 2:
            return

        func_name = parts[1]
        func_qn = f"{module_qn}.{func_name}"

        params = ""
        if "(" in text and ")" in text:
            params = text.split("(")[1].split(")")[0]

        func_props: PropertyDict = {
            cs.KEY_QUALIFIED_NAME: func_qn,
            cs.KEY_NAME: func_name,
            cs.KEY_PARAMETERS: params,
            cs.KEY_START_LINE: node.start_point[0] + 1,
            cs.KEY_END_LINE: node.end_point[0] + 1,
        }

        logger.debug(f"SCSS function found: {func_name}")
        self.ingestor.ensure_node_batch(cs.NodeLabel.SCSS_FUNCTION, func_props)

        self.ingestor.ensure_relationship_batch(
            (cs.NodeLabel.MODULE, cs.KEY_QUALIFIED_NAME, module_qn),
            cs.RelationshipType.DEFINES,
            (cs.NodeLabel.SCSS_FUNCTION, cs.KEY_QUALIFIED_NAME, func_qn),
        )

    def _process_scss_import(self, node: ASTNode, module_qn: str, text: str) -> None:
        if "@import" in text:
            import_path = text.replace("@import", "").strip().strip("'\"").rstrip(";")
        elif "@use" in text:
            import_path = text.replace("@use", "").strip().strip("'\"").rstrip(";")
            if " as " in import_path:
                import_path = import_path.split(" as ")[0].strip()
        else:
            return

        logger.debug(f"SCSS import found: {import_path}")

        self.ingestor.ensure_relationship_batch(
            (cs.NodeLabel.MODULE, cs.KEY_QUALIFIED_NAME, module_qn),
            cs.RelationshipType.SCSS_IMPORTS,
            (cs.NodeLabel.MODULE, cs.KEY_NAME, import_path),
        )

    def _ingest_css_variables(
        self,
        root_node: ASTNode,
        module_qn: str,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        if language not in (cs.SupportedLanguage.CSS, cs.SupportedLanguage.SCSS):
            return

        self._process_css_variables_recursive(root_node, module_qn)

    def _process_css_variables_recursive(self, node: ASTNode, module_qn: str) -> None:
        for child in node.children:
            if child.type == "declaration":
                self._check_css_variable_declaration(child, module_qn)
            self._process_css_variables_recursive(child, module_qn)

    def _check_css_variable_declaration(self, node: ASTNode, module_qn: str) -> None:
        property_node = node.child_by_field_name("property")
        if not property_node:
            for child in node.children:
                if child.type == "property_name":
                    property_node = child
                    break

        if not property_node or not property_node.text:
            return

        prop_name = property_node.text.decode(cs.ENCODING_UTF8)
        if not prop_name.startswith("--"):
            return

        value_node = node.child_by_field_name("value")
        if not value_node:
            for child in node.children:
                if child.type not in ("property_name", ":"):
                    value_node = child
                    break

        var_value = ""
        if value_node and value_node.text:
            var_value = value_node.text.decode(cs.ENCODING_UTF8).rstrip(";")

        var_qn = f"{module_qn}.{prop_name}"

        var_props: PropertyDict = {
            cs.KEY_QUALIFIED_NAME: var_qn,
            cs.KEY_NAME: prop_name,
            "value": var_value,
            cs.KEY_START_LINE: node.start_point[0] + 1,
            cs.KEY_END_LINE: node.end_point[0] + 1,
        }

        logger.debug(f"CSS variable found: {prop_name} = {var_value}")
        self.ingestor.ensure_node_batch(cs.NodeLabel.CSS_VARIABLE, var_props)

        self.ingestor.ensure_relationship_batch(
            (cs.NodeLabel.MODULE, cs.KEY_QUALIFIED_NAME, module_qn),
            cs.RelationshipType.DEFINES_VARIABLE,
            (cs.NodeLabel.CSS_VARIABLE, cs.KEY_QUALIFIED_NAME, var_qn),
        )

    def _ingest_media_queries(
        self,
        root_node: ASTNode,
        module_qn: str,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        if language not in (cs.SupportedLanguage.CSS, cs.SupportedLanguage.SCSS):
            return

        self._process_media_queries_recursive(root_node, module_qn, 0)

    def _process_media_queries_recursive(
        self, node: ASTNode, module_qn: str, counter: int
    ) -> int:
        for child in node.children:
            if child.type == "media_statement":
                counter = self._process_media_statement(child, module_qn, counter)
            counter = self._process_media_queries_recursive(child, module_qn, counter)
        return counter

    def _process_media_statement(
        self, node: ASTNode, module_qn: str, counter: int
    ) -> int:
        if not node.text:
            return counter

        text = node.text.decode(cs.ENCODING_UTF8)
        condition = ""

        for child in node.children:
            if child.type in ("media_feature", "media_query_list", "keyword_query"):
                if child.text:
                    condition = child.text.decode(cs.ENCODING_UTF8)
                    break

        if not condition:
            paren_start = text.find("(")
            paren_end = text.find(")")
            if paren_start != -1 and paren_end != -1:
                condition = text[paren_start : paren_end + 1]
            else:
                parts = text.split("{")[0].replace("@media", "").strip()
                condition = parts if parts else f"query_{counter}"

        media_name = f"media_{counter}"
        media_qn = f"{module_qn}.{media_name}"

        media_props: PropertyDict = {
            cs.KEY_QUALIFIED_NAME: media_qn,
            cs.KEY_NAME: media_name,
            "condition": condition,
            cs.KEY_START_LINE: node.start_point[0] + 1,
            cs.KEY_END_LINE: node.end_point[0] + 1,
        }

        logger.debug(f"Media query found: {condition}")
        self.ingestor.ensure_node_batch(cs.NodeLabel.MEDIA_QUERY, media_props)

        self.ingestor.ensure_relationship_batch(
            (cs.NodeLabel.MODULE, cs.KEY_QUALIFIED_NAME, module_qn),
            cs.RelationshipType.DEFINES_MEDIA_QUERY,
            (cs.NodeLabel.MEDIA_QUERY, cs.KEY_QUALIFIED_NAME, media_qn),
        )

        return counter + 1

    def _ingest_keyframe_animations(
        self,
        root_node: ASTNode,
        module_qn: str,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        if language not in (cs.SupportedLanguage.CSS, cs.SupportedLanguage.SCSS):
            return

        self._process_keyframes_recursive(root_node, module_qn)

    def _process_keyframes_recursive(self, node: ASTNode, module_qn: str) -> None:
        for child in node.children:
            if child.type == "keyframes_statement":
                self._process_keyframes_statement(child, module_qn)
            self._process_keyframes_recursive(child, module_qn)

    def _process_keyframes_statement(self, node: ASTNode, module_qn: str) -> None:
        if not node.text:
            return

        text = node.text.decode(cs.ENCODING_UTF8)
        anim_name = ""

        for child in node.children:
            if child.type == "keyframes_name":
                if child.text:
                    anim_name = child.text.decode(cs.ENCODING_UTF8)
                    break

        if not anim_name:
            parts = text.split("{")[0].replace("@keyframes", "").strip()
            parts = parts.replace("@-webkit-keyframes", "").strip()
            anim_name = parts if parts else "unnamed_animation"

        anim_qn = f"{module_qn}.{anim_name}"

        keyframes: list[str] = []
        for child in node.children:
            if child.type == "keyframe_block_list":
                for block in child.children:
                    if block.type == "keyframe_block":
                        selector = block.child_by_field_name("selector")
                        if selector and selector.text:
                            keyframes.append(selector.text.decode(cs.ENCODING_UTF8))
                        else:
                            for subchild in block.children:
                                if subchild.type in ("from", "to", "integer"):
                                    if subchild.text:
                                        keyframes.append(
                                            subchild.text.decode(cs.ENCODING_UTF8)
                                        )
                                    break

        anim_props: PropertyDict = {
            cs.KEY_QUALIFIED_NAME: anim_qn,
            cs.KEY_NAME: anim_name,
            cs.KEY_START_LINE: node.start_point[0] + 1,
            cs.KEY_END_LINE: node.end_point[0] + 1,
        }
        if keyframes:
            anim_props["keyframes"] = ", ".join(keyframes)

        logger.debug(f"Keyframe animation found: {anim_name}")
        self.ingestor.ensure_node_batch(cs.NodeLabel.KEYFRAME_ANIMATION, anim_props)

        self.ingestor.ensure_relationship_batch(
            (cs.NodeLabel.MODULE, cs.KEY_QUALIFIED_NAME, module_qn),
            cs.RelationshipType.DEFINES_KEYFRAME,
            (cs.NodeLabel.KEYFRAME_ANIMATION, cs.KEY_QUALIFIED_NAME, anim_qn),
        )
