from collections.abc import Callable

from loguru import logger

from ... import constants as cs
from ... import logs as ls
from ...types_defs import ASTNode, FunctionRegistryTrieProtocol, NodeType
from ..import_processor import ImportProcessor
from ..utils import safe_decode_text
from . import utils as ut


class JsTypeInferenceEngine:
    def __init__(
        self,
        import_processor: ImportProcessor,
        function_registry: FunctionRegistryTrieProtocol,
        project_name: str,
        find_method_ast_node_func: Callable[[str], ASTNode | None],
    ):
        self.import_processor = import_processor
        self.function_registry = function_registry
        self.project_name = project_name
        self._find_method_ast_node = find_method_ast_node_func

    def build_local_variable_type_map(
        self, caller_node: ASTNode, module_qn: str
    ) -> dict[str, str]:
        local_var_types: dict[str, str] = {}

        stack: list[ASTNode] = [caller_node]

        declarator_count = 0

        while stack:
            current = stack.pop()

            if current.type == cs.TS_VARIABLE_DECLARATOR:
                declarator_count += 1
                name_node = current.child_by_field_name("name")
                value_node = current.child_by_field_name("value")

                if name_node and value_node:
                    var_name_text = name_node.text
                    if var_name_text:
                        var_name = safe_decode_text(name_node)
                        if var_name is not None:
                            logger.debug(
                                ls.JS_VAR_DECLARATOR_FOUND.format(
                                    var_name=var_name, module_qn=module_qn
                                )
                            )

                            if var_type := self._infer_js_variable_type_from_value(
                                value_node, module_qn
                            ):
                                local_var_types[var_name] = var_type
                                logger.debug(
                                    ls.JS_VAR_INFERRED.format(
                                        var_name=var_name, var_type=var_type
                                    )
                                )
                            else:
                                logger.debug(
                                    ls.JS_VAR_INFER_FAILED.format(var_name=var_name)
                                )

            stack.extend(reversed(current.children))

        logger.debug(
            ls.JS_VAR_TYPE_MAP_BUILT.format(
                count=len(local_var_types), declarator_count=declarator_count
            )
        )
        return local_var_types

    def _infer_js_variable_type_from_value(
        self, value_node: ASTNode, module_qn: str
    ) -> str | None:
        logger.debug(ls.JS_INFER_VALUE_NODE.format(node_type=value_node.type))

        if value_node.type == cs.TS_NEW_EXPRESSION:
            if class_name := ut.extract_constructor_name(value_node):
                class_qn = self._resolve_js_class_name(class_name, module_qn)
                return class_qn or class_name

        elif value_node.type == cs.TS_CALL_EXPRESSION:
            func_node = value_node.child_by_field_name("function")
            func_type = func_node.type if func_node else cs.STR_NONE
            logger.debug(ls.JS_CALL_EXPR_FUNC_NODE.format(func_type=func_type))

            if func_node and func_node.type == cs.TS_MEMBER_EXPRESSION:
                method_call_text = ut.extract_method_call(func_node)
                logger.debug(
                    ls.JS_EXTRACTED_METHOD_CALL.format(method_call=method_call_text)
                )
                if method_call_text:
                    if inferred_type := self._infer_js_method_return_type(
                        method_call_text, module_qn
                    ):
                        logger.debug(
                            ls.JS_TYPE_INFERRED.format(
                                method_call=method_call_text,
                                inferred_type=inferred_type,
                            )
                        )
                        return inferred_type
                    logger.debug(
                        ls.JS_RETURN_TYPE_INFER_FAILED.format(
                            method_call=method_call_text
                        )
                    )

            elif func_node and func_node.type == cs.TS_IDENTIFIER:
                func_name = func_node.text
                if func_name:
                    return safe_decode_text(func_node)

        logger.debug(ls.JS_NO_PATTERN_MATCHED.format(node_type=value_node.type))
        return None

    def _infer_js_method_return_type(
        self, method_call: str, module_qn: str
    ) -> str | None:
        parts = method_call.split(cs.SEPARATOR_DOT)
        if len(parts) != 2:
            logger.debug(ls.JS_METHOD_CALL_INVALID.format(method_call=method_call))
            return None

        class_name, method_name = parts

        class_qn = self._resolve_js_class_name(class_name, module_qn)
        if not class_qn:
            logger.debug(
                ls.JS_CLASS_RESOLVE_FAILED.format(
                    class_name=class_name, module_qn=module_qn
                )
            )
            return None

        logger.debug(
            ls.JS_CLASS_RESOLVED.format(class_name=class_name, class_qn=class_qn)
        )

        method_qn = f"{class_qn}{cs.SEPARATOR_DOT}{method_name}"
        logger.debug(ls.JS_LOOKING_FOR_METHOD.format(method_qn=method_qn))

        method_node = self._find_method_ast_node(method_qn)
        if not method_node:
            logger.debug(ls.JS_METHOD_AST_NOT_FOUND.format(method_qn=method_qn))
            return None

        return_type = self._analyze_return_statements(method_node, method_qn)
        logger.debug(
            ls.JS_RETURN_ANALYZED.format(method_qn=method_qn, return_type=return_type)
        )
        return return_type

    def _resolve_js_class_name(self, class_name: str, module_qn: str) -> str | None:
        if module_qn in self.import_processor.import_mapping:
            import_map = self.import_processor.import_mapping[module_qn]
            if class_name in import_map:
                imported_qn = import_map[class_name]

                full_class_qn = f"{imported_qn}{cs.SEPARATOR_DOT}{class_name}"
                if (
                    full_class_qn in self.function_registry
                    and self.function_registry[full_class_qn] == NodeType.CLASS
                ):
                    return full_class_qn

                return imported_qn

        local_class_qn = f"{module_qn}{cs.SEPARATOR_DOT}{class_name}"
        if (
            local_class_qn in self.function_registry
            and self.function_registry[local_class_qn] == NodeType.CLASS
        ):
            return local_class_qn

        return None

    def _analyze_return_statements(
        self, method_node: ASTNode, method_qn: str
    ) -> str | None:
        return_nodes: list[ASTNode] = []
        ut.find_return_statements(method_node, return_nodes)

        for return_node in return_nodes:
            for child in return_node.children:
                if child.type == cs.TS_RETURN:
                    continue

                if inferred_type := ut.analyze_return_expression(child, method_qn):
                    return inferred_type

        return None

    def _infer_for_of_loop_variable(
        self,
        for_node: ASTNode,
        local_var_types: dict[str, str],
        module_qn: str,
    ) -> tuple[str, str] | None:
        """Extract variable name and infer element type from for-of loop.

        Handles patterns like:
            for (const user of users) { ... }  // user: User if users: User[]
            for (const [key, value] of map) { ... }  // destructuring

        Returns tuple of (variable_name, inferred_type) or None.
        """
        left_node = for_node.child_by_field_name(cs.FIELD_LEFT)
        right_node = for_node.child_by_field_name(cs.FIELD_RIGHT)

        if not left_node or not right_node:
            return None

        var_name = self._extract_for_of_variable_name(left_node)
        if not var_name:
            return None

        iterable_type = self._get_iterable_type(right_node, local_var_types, module_qn)
        if not iterable_type:
            logger.debug(ls.JS_FOR_OF_NO_ITERABLE)
            return None

        logger.debug(ls.JS_FOR_OF_ITERABLE_TYPE.format(iterable_type=iterable_type))

        element_type = self._extract_element_type(iterable_type)
        if element_type:
            logger.debug(
                ls.JS_FOR_OF_VAR_INFERRED.format(
                    var_name=var_name, var_type=element_type
                )
            )
            return (var_name, element_type)

        return None

    def _extract_for_of_variable_name(self, left_node: ASTNode) -> str | None:
        """Extract variable name from for-of loop left side."""
        if left_node.type == cs.TS_IDENTIFIER:
            return safe_decode_text(left_node)

        for child in left_node.children:
            if child.type == cs.TS_VARIABLE_DECLARATOR:
                name_node = child.child_by_field_name(cs.FIELD_NAME)
                if name_node and name_node.type == cs.TS_IDENTIFIER:
                    return safe_decode_text(name_node)
            elif child.type == cs.TS_IDENTIFIER:
                return safe_decode_text(child)

        return None

    def _get_iterable_type(
        self,
        right_node: ASTNode,
        local_var_types: dict[str, str],
        module_qn: str,
    ) -> str | None:
        """Get the type of the iterable in a for-of loop."""
        if right_node.type == cs.TS_IDENTIFIER:
            var_name = safe_decode_text(right_node)
            if var_name and var_name in local_var_types:
                return local_var_types[var_name]

        if right_node.type == cs.TS_CALL_EXPRESSION:
            return self._infer_js_variable_type_from_value(right_node, module_qn)

        return None

    def _extract_element_type(self, array_type: str) -> str | None:
        """Extract element type from array or generic type.

        Handles:
            - User[] -> User
            - Array<User> -> User
            - Map<string, User> -> User (value type)
            - Set<User> -> User
        """
        array_type = array_type.strip()

        if array_type.endswith("[]"):
            element = array_type[:-2].strip()
            logger.debug(
                ls.JS_ARRAY_TYPE_EXTRACTED.format(
                    array_type=array_type, element=element
                )
            )
            return element

        if "<" in array_type and array_type.endswith(">"):
            return self._extract_generic_element_type(array_type)

        return None

    def _extract_generic_element_type(self, generic_type: str) -> str | None:
        """Extract element type from generic type notation.

        Handles:
            - Array<User> -> User
            - Map<string, User> -> User (value type)
            - Set<User> -> User
            - Promise<User> -> User
        """
        start = generic_type.find("<")
        end = generic_type.rfind(">")

        if start == -1 or end == -1 or start >= end:
            return None

        base_type = generic_type[:start].strip()
        type_args = generic_type[start + 1 : end].strip()

        if base_type in ("Array", "Set", "Promise", "Iterable", "Iterator"):
            element = type_args.strip()
            logger.debug(
                ls.JS_GENERIC_TYPE_EXTRACTED.format(
                    generic=generic_type, element=element
                )
            )
            return element

        if base_type == "Map":
            parts = self._split_type_args(type_args)
            if len(parts) >= 2:
                value_type = parts[1].strip()
                logger.debug(
                    ls.JS_GENERIC_TYPE_EXTRACTED.format(
                        generic=generic_type, element=value_type
                    )
                )
                return value_type

        return None

    def _split_type_args(self, type_args: str) -> list[str]:
        """Split generic type arguments, handling nested generics."""
        parts: list[str] = []
        current = ""
        depth = 0

        for char in type_args:
            if char == "<":
                depth += 1
                current += char
            elif char == ">":
                depth -= 1
                current += char
            elif char == "," and depth == 0:
                parts.append(current.strip())
                current = ""
            else:
                current += char

        if current.strip():
            parts.append(current.strip())

        return parts

    def extract_return_type_annotation(self, func_node: ASTNode) -> str | None:
        """Extract return type annotation from function declaration.

        Handles TypeScript return type annotations like:
            function getUser(): User { ... }
            const getUser = (): User => { ... }
        """
        return_type_node = func_node.child_by_field_name(cs.FIELD_RETURN_TYPE)
        if return_type_node:
            type_str = self._parse_type_node(return_type_node)
            if type_str:
                logger.debug(ls.JS_RETURN_TYPE_ANNOTATION.format(return_type=type_str))
            return type_str

        for child in func_node.children:
            if child.type == cs.TS_TYPE_ANNOTATION:
                type_str = self._parse_type_node(child)
                if type_str:
                    logger.debug(
                        ls.JS_RETURN_TYPE_ANNOTATION.format(return_type=type_str)
                    )
                return type_str

        return None

    def extract_variable_type_annotation(self, var_node: ASTNode) -> str | None:
        """Extract type annotation from variable declaration.

        Handles TypeScript type annotations like:
            const users: User[] = getUsers();
            let count: number = 0;
        """
        type_node = var_node.child_by_field_name(cs.FIELD_TYPE_ANNOTATION)
        if type_node:
            return self._parse_type_node(type_node)

        name_node = var_node.child_by_field_name(cs.FIELD_NAME)
        if name_node:
            for child in name_node.children:
                if child.type == cs.TS_TYPE_ANNOTATION:
                    return self._parse_type_node(child)

        for child in var_node.children:
            if child.type == cs.TS_TYPE_ANNOTATION:
                return self._parse_type_node(child)

        return None

    def _parse_type_node(self, type_node: ASTNode) -> str | None:
        """Parse a type annotation node into a string representation."""
        if not type_node:
            return None

        if type_node.text:
            type_str = safe_decode_text(type_node)
            if type_str and type_str.startswith(":"):
                type_str = type_str[1:].strip()
            logger.debug(ls.JS_TYPE_ANNOTATION_FOUND.format(annotation=type_str))
            return type_str

        return None

    def build_local_variable_type_map_with_for_of(
        self, caller_node: ASTNode, module_qn: str
    ) -> dict[str, str]:
        """Build variable type map including for-of loop variable inference.

        Extended version that handles:
        - Regular variable declarations
        - TypeScript type annotations
        - For-of loop variable inference
        """
        local_var_types: dict[str, str] = {}
        stack: list[ASTNode] = [caller_node]
        declarator_count = 0

        while stack:
            current = stack.pop()

            if current.type == cs.TS_VARIABLE_DECLARATOR:
                declarator_count += 1
                self._process_variable_declarator(current, local_var_types, module_qn)

            elif current.type == "for_in_statement":
                if self._is_for_of_loop(current):
                    result = self._infer_for_of_loop_variable(
                        current, local_var_types, module_qn
                    )
                    if result:
                        var_name, var_type = result
                        local_var_types[var_name] = var_type

            stack.extend(reversed(current.children))

        logger.debug(
            ls.JS_VAR_TYPE_MAP_BUILT.format(
                count=len(local_var_types), declarator_count=declarator_count
            )
        )
        return local_var_types

    def _process_variable_declarator(
        self,
        var_node: ASTNode,
        local_var_types: dict[str, str],
        module_qn: str,
    ) -> None:
        """Process a variable declarator node to extract type information."""
        name_node = var_node.child_by_field_name(cs.FIELD_NAME)
        value_node = var_node.child_by_field_name(cs.FIELD_VALUE)

        if not name_node:
            return

        var_name_text = name_node.text
        if not var_name_text:
            return

        var_name = safe_decode_text(name_node)
        if var_name is None:
            return

        logger.debug(
            ls.JS_VAR_DECLARATOR_FOUND.format(var_name=var_name, module_qn=module_qn)
        )

        type_annotation = self.extract_variable_type_annotation(var_node)
        if type_annotation:
            local_var_types[var_name] = type_annotation
            logger.debug(
                ls.JS_VAR_INFERRED.format(var_name=var_name, var_type=type_annotation)
            )
            return

        if value_node:
            var_type = self._infer_js_variable_type_from_value(value_node, module_qn)
            if var_type:
                local_var_types[var_name] = var_type
                logger.debug(
                    ls.JS_VAR_INFERRED.format(var_name=var_name, var_type=var_type)
                )
            else:
                logger.debug(ls.JS_VAR_INFER_FAILED.format(var_name=var_name))

    def _is_for_of_loop(self, for_node: ASTNode) -> bool:
        """Check if a for_in_statement is actually a for-of loop.

        In tree-sitter TypeScript, for-of loops have node type 'for_in_statement'
        but contain 'of' keyword instead of 'in'.
        """
        if for_node.text:
            text = safe_decode_text(for_node)
            if text and " of " in text:
                return True
        return False
