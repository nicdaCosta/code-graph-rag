from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from loguru import logger

from ... import constants as cs
from .registry import detect_framework

if TYPE_CHECKING:
    from ...services import IngestorProtocol
    from ...types_defs import ASTNode, LanguageQueries


class ReactIngestMixin:
    ingestor: IngestorProtocol
    repo_path: Path
    project_name: str

    def _ingest_react_components(
        self,
        root_node: ASTNode,
        module_qn: str,
        file_path: Path,
        language: cs.SupportedLanguage,
        queries: dict[cs.SupportedLanguage, LanguageQueries],
    ) -> None:
        if language not in cs.JS_TS_LANGUAGES:
            return

        imports = self._collect_imports_for_framework_detection(root_node)
        handlers = detect_framework(imports)

        for handler in handlers:
            if handler.framework_name != "react":
                continue

            components = handler.extract_components(root_node, module_qn, file_path)
            hooks = handler.extract_hooks(root_node, module_qn, components)
            relationships = handler.extract_relationships(
                root_node, module_qn, components
            )

            for component in components:
                props = handler.to_node_props(component)
                logger.debug(f"React component found: {component.name}")
                self.ingestor.ensure_node_batch(cs.NodeLabel.REACT_COMPONENT, props)

                self.ingestor.ensure_relationship_batch(
                    (cs.NodeLabel.MODULE, cs.KEY_QUALIFIED_NAME, module_qn),
                    cs.RelationshipType.DEFINES,
                    (
                        cs.NodeLabel.REACT_COMPONENT,
                        cs.KEY_QUALIFIED_NAME,
                        component.qualified_name,
                    ),
                )

                if component.props_interface:
                    self.ingestor.ensure_relationship_batch(
                        (
                            cs.NodeLabel.REACT_COMPONENT,
                            cs.KEY_QUALIFIED_NAME,
                            component.qualified_name,
                        ),
                        cs.RelationshipType.ACCEPTS_PROPS,
                        (
                            cs.NodeLabel.INTERFACE,
                            cs.KEY_NAME,
                            component.props_interface,
                        ),
                    )

            for hook in hooks:
                hook_props = {
                    cs.KEY_QUALIFIED_NAME: hook.qualified_name,
                    cs.KEY_NAME: hook.hook_name,
                    "is_builtin": hook.is_builtin,
                    cs.KEY_START_LINE: hook.start_line,
                }

                if hook.is_builtin:
                    self.ingestor.ensure_node_batch(cs.NodeLabel.REACT_HOOK, hook_props)

                logger.debug(f"Hook usage: {hook.hook_name} in {hook.component_qn}")
                self.ingestor.ensure_relationship_batch(
                    (
                        cs.NodeLabel.REACT_COMPONENT,
                        cs.KEY_QUALIFIED_NAME,
                        hook.component_qn,
                    ),
                    cs.RelationshipType.USES_HOOK,
                    (
                        cs.NodeLabel.REACT_HOOK,
                        cs.KEY_QUALIFIED_NAME,
                        hook.qualified_name,
                    ),
                )

            for rel in relationships:
                logger.debug(
                    f"Component relationship: {rel.source_qn} -[{rel.relationship_type}]-> {rel.target_qn}"
                )
                self.ingestor.ensure_relationship_batch(
                    (rel.source_label, cs.KEY_QUALIFIED_NAME, rel.source_qn),
                    rel.relationship_type,
                    (rel.target_label, cs.KEY_QUALIFIED_NAME, rel.target_qn),
                    properties=rel.properties if rel.properties else None,
                )

    def _collect_imports_for_framework_detection(self, root_node: ASTNode) -> set[str]:
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

            elif node.type == cs.TS_CALL_EXPRESSION:
                func_node = node.child_by_field_name(cs.FIELD_FUNCTION)
                if func_node and func_node.text:
                    func_name = func_node.text.decode(cs.ENCODING_UTF8)
                    if func_name == "require":
                        args = node.child_by_field_name(cs.FIELD_ARGUMENTS)
                        if args and args.children:
                            for arg in args.children:
                                if arg.type == cs.TS_STRING and arg.text:
                                    import_path = arg.text.decode(cs.ENCODING_UTF8)
                                    import_path = import_path.strip("'\"")
                                    imports.add(import_path)

            stack.extend(reversed(node.children))

        return imports
