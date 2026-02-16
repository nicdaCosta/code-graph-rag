import textwrap
from collections import defaultdict
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from tree_sitter import Query, QueryCursor

from codebase_rag import constants as cs
from codebase_rag.parser_loader import load_parsers
from codebase_rag.parsers.js_ts.module_system import JsTsModuleSystemMixin
from codebase_rag.tests.conftest import create_mock_node


class ConcreteModuleSystemMixin(JsTsModuleSystemMixin):
    def __init__(
        self,
        ingestor: MagicMock,
        import_processor: MagicMock,
        function_registry: MagicMock,
        simple_name_lookup: defaultdict[str, set[str]],
    ) -> None:
        super().__init__()
        self.ingestor = ingestor
        self.import_processor = import_processor
        self.function_registry = function_registry
        self.simple_name_lookup = simple_name_lookup
        self.repo_path = Path("/test/repo")
        self.project_name = "test_project"
        self._get_docstring = MagicMock(return_value=None)
        self._is_export_inside_function = MagicMock(return_value=False)


@pytest.fixture
def mock_ingestor() -> MagicMock:
    ingestor = MagicMock()
    ingestor.ensure_node_batch = MagicMock()
    ingestor.ensure_relationship_batch = MagicMock()
    return ingestor


@pytest.fixture
def mock_import_processor() -> MagicMock:
    processor = MagicMock()
    processor._resolve_js_module_path = MagicMock(return_value="resolved.module")
    return processor


@pytest.fixture
def mock_function_registry() -> MagicMock:
    registry = MagicMock()
    registry.__contains__ = MagicMock(return_value=False)
    registry.__setitem__ = MagicMock()
    return registry


@pytest.fixture
def mixin(
    mock_ingestor: MagicMock,
    mock_import_processor: MagicMock,
    mock_function_registry: MagicMock,
) -> ConcreteModuleSystemMixin:
    return ConcreteModuleSystemMixin(
        ingestor=mock_ingestor,
        import_processor=mock_import_processor,
        function_registry=mock_function_registry,
        simple_name_lookup=defaultdict(set),
    )


@pytest.fixture
def mock_language_queries() -> dict[cs.SupportedLanguage, MagicMock]:
    mock_lang = MagicMock()
    return {
        cs.SupportedLanguage.JS: {cs.QUERY_LANGUAGE: mock_lang},
        cs.SupportedLanguage.TS: {cs.QUERY_LANGUAGE: mock_lang},
    }


class TestProcessCommonjsImport:
    def test_creates_module_node_and_relationship(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_ingestor: MagicMock,
        mock_import_processor: MagicMock,
    ) -> None:
        mock_import_processor._resolve_js_module_path.return_value = "fs"

        mixin._process_commonjs_import("readFile", "fs", "my_module")

        mock_ingestor.ensure_node_batch.assert_called_once()
        call_args = mock_ingestor.ensure_node_batch.call_args
        assert call_args[0][0] == cs.NodeLabel.MODULE
        assert call_args[0][1][cs.KEY_QUALIFIED_NAME] == "fs"

        mock_ingestor.ensure_relationship_batch.assert_called_once()
        rel_args = mock_ingestor.ensure_relationship_batch.call_args
        assert rel_args[0][1] == cs.RelationshipType.IMPORTS

    def test_skips_duplicate_imports(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_ingestor: MagicMock,
        mock_import_processor: MagicMock,
    ) -> None:
        mock_import_processor._resolve_js_module_path.return_value = "fs"

        mixin._process_commonjs_import("readFile", "fs", "my_module")
        mixin._process_commonjs_import("writeFile", "fs", "my_module")

        assert mock_ingestor.ensure_node_batch.call_count == 1

    def test_handles_resolution_error_gracefully(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_ingestor: MagicMock,
        mock_import_processor: MagicMock,
    ) -> None:
        mock_import_processor._resolve_js_module_path.side_effect = Exception(
            "Resolution failed"
        )

        mixin._process_commonjs_import("readFile", "fs", "my_module")

        mock_ingestor.ensure_node_batch.assert_not_called()


class TestProcessVariableDeclaratorForCommonjs:
    def test_processes_simple_destructuring(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_import_processor: MagicMock,
    ) -> None:
        mock_import_processor._resolve_js_module_path.return_value = "fs"

        shorthand_id = create_mock_node(
            cs.TS_SHORTHAND_PROPERTY_IDENTIFIER_PATTERN, "readFile"
        )
        object_pattern = create_mock_node(cs.TS_OBJECT_PATTERN, children=[shorthand_id])

        module_string = create_mock_node(cs.TS_STRING, "'fs'")
        arguments = create_mock_node(cs.TS_ARGUMENTS, children=[module_string])
        require_id = create_mock_node(cs.TS_IDENTIFIER, cs.JS_REQUIRE_KEYWORD)
        call_expr = create_mock_node(
            cs.TS_CALL_EXPRESSION,
            fields={
                cs.FIELD_FUNCTION: require_id,
                cs.TS_FIELD_ARGUMENTS: arguments,
            },
        )

        declarator = create_mock_node(
            cs.TS_VARIABLE_DECLARATOR,
            fields={
                cs.FIELD_NAME: object_pattern,
                cs.FIELD_VALUE: call_expr,
            },
        )

        mixin._process_variable_declarator_for_commonjs(declarator, "test_module")

        mock_import_processor._resolve_js_module_path.assert_called_once()

    def test_processes_aliased_destructuring(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_import_processor: MagicMock,
    ) -> None:
        mock_import_processor._resolve_js_module_path.return_value = "fs"

        key_node = create_mock_node(cs.TS_PROPERTY_IDENTIFIER, "readFile")
        value_node = create_mock_node(cs.TS_IDENTIFIER, "rf")
        pair_pattern = create_mock_node(
            cs.TS_PAIR_PATTERN,
            fields={
                cs.FIELD_KEY: key_node,
                cs.FIELD_VALUE: value_node,
            },
        )
        object_pattern = create_mock_node(cs.TS_OBJECT_PATTERN, children=[pair_pattern])

        module_string = create_mock_node(cs.TS_STRING, "'fs'")
        arguments = create_mock_node(cs.TS_ARGUMENTS, children=[module_string])
        require_id = create_mock_node(cs.TS_IDENTIFIER, cs.JS_REQUIRE_KEYWORD)
        call_expr = create_mock_node(
            cs.TS_CALL_EXPRESSION,
            fields={
                cs.FIELD_FUNCTION: require_id,
                cs.TS_FIELD_ARGUMENTS: arguments,
            },
        )

        declarator = create_mock_node(
            cs.TS_VARIABLE_DECLARATOR,
            fields={
                cs.FIELD_NAME: object_pattern,
                cs.FIELD_VALUE: call_expr,
            },
        )

        mixin._process_variable_declarator_for_commonjs(declarator, "test_module")

        mock_import_processor._resolve_js_module_path.assert_called_once()

    def test_skips_non_object_pattern_name(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_import_processor: MagicMock,
    ) -> None:
        name_node = create_mock_node(cs.TS_IDENTIFIER, "fs")
        call_expr = create_mock_node(cs.TS_CALL_EXPRESSION)
        declarator = create_mock_node(
            cs.TS_VARIABLE_DECLARATOR,
            fields={
                cs.FIELD_NAME: name_node,
                cs.FIELD_VALUE: call_expr,
            },
        )

        mixin._process_variable_declarator_for_commonjs(declarator, "test_module")

        mock_import_processor._resolve_js_module_path.assert_not_called()

    def test_skips_non_require_call(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_import_processor: MagicMock,
    ) -> None:
        object_pattern = create_mock_node(cs.TS_OBJECT_PATTERN, children=[])
        import_id = create_mock_node(cs.TS_IDENTIFIER, "import")
        call_expr = create_mock_node(
            cs.TS_CALL_EXPRESSION,
            fields={cs.FIELD_FUNCTION: import_id},
        )
        declarator = create_mock_node(
            cs.TS_VARIABLE_DECLARATOR,
            fields={
                cs.FIELD_NAME: object_pattern,
                cs.FIELD_VALUE: call_expr,
            },
        )

        mixin._process_variable_declarator_for_commonjs(declarator, "test_module")

        mock_import_processor._resolve_js_module_path.assert_not_called()

    def test_skips_empty_object_pattern(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_import_processor: MagicMock,
    ) -> None:
        object_pattern = create_mock_node(cs.TS_OBJECT_PATTERN, children=[])

        module_string = create_mock_node(cs.TS_STRING, "'fs'")
        arguments = create_mock_node(cs.TS_ARGUMENTS, children=[module_string])
        require_id = create_mock_node(cs.TS_IDENTIFIER, cs.JS_REQUIRE_KEYWORD)
        call_expr = create_mock_node(
            cs.TS_CALL_EXPRESSION,
            fields={
                cs.FIELD_FUNCTION: require_id,
                cs.TS_FIELD_ARGUMENTS: arguments,
            },
        )

        declarator = create_mock_node(
            cs.TS_VARIABLE_DECLARATOR,
            fields={
                cs.FIELD_NAME: object_pattern,
                cs.FIELD_VALUE: call_expr,
            },
        )

        mixin._process_variable_declarator_for_commonjs(declarator, "test_module")

        mock_import_processor._resolve_js_module_path.assert_not_called()


class TestIngestMissingImportPatterns:
    def test_skips_non_js_ts_languages(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_language_queries: dict[cs.SupportedLanguage, MagicMock],
    ) -> None:
        mixin._ingest_missing_import_patterns(
            MagicMock(),
            "test_module",
            cs.SupportedLanguage.PYTHON,
            mock_language_queries,
        )

    def test_skips_when_no_language_obj(
        self,
        mixin: ConcreteModuleSystemMixin,
    ) -> None:
        queries: dict[cs.SupportedLanguage, dict[str, MagicMock | None]] = {
            cs.SupportedLanguage.JS: {cs.QUERY_LANGUAGE: None}
        }
        mixin._ingest_missing_import_patterns(
            MagicMock(),
            "test_module",
            cs.SupportedLanguage.JS,
            queries,
        )


class TestIngestCommonjsExports:
    def test_skips_non_js_ts_languages(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_language_queries: dict[cs.SupportedLanguage, MagicMock],
    ) -> None:
        mixin._ingest_commonjs_exports(
            MagicMock(),
            "test_module",
            cs.SupportedLanguage.PYTHON,
            mock_language_queries,
        )

    def test_skips_when_no_language_obj(
        self,
        mixin: ConcreteModuleSystemMixin,
    ) -> None:
        queries: dict[cs.SupportedLanguage, dict[str, MagicMock | None]] = {
            cs.SupportedLanguage.JS: {cs.QUERY_LANGUAGE: None}
        }
        mixin._ingest_commonjs_exports(
            MagicMock(),
            "test_module",
            cs.SupportedLanguage.JS,
            queries,
        )


class TestIngestEs6Exports:
    def test_handles_query_errors_gracefully(
        self,
        mixin: ConcreteModuleSystemMixin,
    ) -> None:
        mock_lang = MagicMock()
        queries: dict[cs.SupportedLanguage, dict[str, MagicMock]] = {
            cs.SupportedLanguage.JS: {cs.QUERY_LANGUAGE: mock_lang}
        }

        mixin._ingest_es6_exports(
            MagicMock(),
            "test_module",
            cs.SupportedLanguage.JS,
            queries,
        )


class TestEdgeCases:
    def test_missing_name_field_in_declarator(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_import_processor: MagicMock,
    ) -> None:
        call_expr = create_mock_node(cs.TS_CALL_EXPRESSION)
        declarator = create_mock_node(
            cs.TS_VARIABLE_DECLARATOR,
            fields={cs.FIELD_VALUE: call_expr},
        )

        mixin._process_variable_declarator_for_commonjs(declarator, "test_module")

        mock_import_processor._resolve_js_module_path.assert_not_called()

    def test_missing_value_field_in_declarator(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_import_processor: MagicMock,
    ) -> None:
        object_pattern = create_mock_node(cs.TS_OBJECT_PATTERN)
        declarator = create_mock_node(
            cs.TS_VARIABLE_DECLARATOR,
            fields={cs.FIELD_NAME: object_pattern},
        )

        mixin._process_variable_declarator_for_commonjs(declarator, "test_module")

        mock_import_processor._resolve_js_module_path.assert_not_called()

    def test_missing_function_field_in_call_expression(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_import_processor: MagicMock,
    ) -> None:
        object_pattern = create_mock_node(cs.TS_OBJECT_PATTERN)
        call_expr = create_mock_node(cs.TS_CALL_EXPRESSION, fields={})
        declarator = create_mock_node(
            cs.TS_VARIABLE_DECLARATOR,
            fields={
                cs.FIELD_NAME: object_pattern,
                cs.FIELD_VALUE: call_expr,
            },
        )

        mixin._process_variable_declarator_for_commonjs(declarator, "test_module")

        mock_import_processor._resolve_js_module_path.assert_not_called()

    def test_missing_arguments_in_require_call(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_import_processor: MagicMock,
    ) -> None:
        object_pattern = create_mock_node(cs.TS_OBJECT_PATTERN, children=[])
        require_id = create_mock_node(cs.TS_IDENTIFIER, cs.JS_REQUIRE_KEYWORD)
        call_expr = create_mock_node(
            cs.TS_CALL_EXPRESSION,
            fields={cs.FIELD_FUNCTION: require_id},
        )
        declarator = create_mock_node(
            cs.TS_VARIABLE_DECLARATOR,
            fields={
                cs.FIELD_NAME: object_pattern,
                cs.FIELD_VALUE: call_expr,
            },
        )

        mixin._process_variable_declarator_for_commonjs(declarator, "test_module")

        mock_import_processor._resolve_js_module_path.assert_not_called()

    def test_non_string_module_argument(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_import_processor: MagicMock,
    ) -> None:
        shorthand_id = create_mock_node(
            cs.TS_SHORTHAND_PROPERTY_IDENTIFIER_PATTERN, "readFile"
        )
        object_pattern = create_mock_node(cs.TS_OBJECT_PATTERN, children=[shorthand_id])

        identifier_arg = create_mock_node(cs.TS_IDENTIFIER, "moduleName")
        arguments = create_mock_node(cs.TS_ARGUMENTS, children=[identifier_arg])
        require_id = create_mock_node(cs.TS_IDENTIFIER, cs.JS_REQUIRE_KEYWORD)
        call_expr = create_mock_node(
            cs.TS_CALL_EXPRESSION,
            fields={
                cs.FIELD_FUNCTION: require_id,
                cs.TS_FIELD_ARGUMENTS: arguments,
            },
        )

        declarator = create_mock_node(
            cs.TS_VARIABLE_DECLARATOR,
            fields={
                cs.FIELD_NAME: object_pattern,
                cs.FIELD_VALUE: call_expr,
            },
        )

        mixin._process_variable_declarator_for_commonjs(declarator, "test_module")

        mock_import_processor._resolve_js_module_path.assert_not_called()

    def test_pair_pattern_with_wrong_key_type(
        self,
        mixin: ConcreteModuleSystemMixin,
        mock_import_processor: MagicMock,
    ) -> None:
        mock_import_processor._resolve_js_module_path.return_value = "fs"

        key_node = create_mock_node(cs.TS_STRING, "'readFile'")
        value_node = create_mock_node(cs.TS_IDENTIFIER, "rf")
        pair_pattern = create_mock_node(
            cs.TS_PAIR_PATTERN,
            fields={
                cs.FIELD_KEY: key_node,
                cs.FIELD_VALUE: value_node,
            },
        )
        object_pattern = create_mock_node(cs.TS_OBJECT_PATTERN, children=[pair_pattern])

        module_string = create_mock_node(cs.TS_STRING, "'fs'")
        arguments = create_mock_node(cs.TS_ARGUMENTS, children=[module_string])
        require_id = create_mock_node(cs.TS_IDENTIFIER, cs.JS_REQUIRE_KEYWORD)
        call_expr = create_mock_node(
            cs.TS_CALL_EXPRESSION,
            fields={
                cs.FIELD_FUNCTION: require_id,
                cs.TS_FIELD_ARGUMENTS: arguments,
            },
        )

        declarator = create_mock_node(
            cs.TS_VARIABLE_DECLARATOR,
            fields={
                cs.FIELD_NAME: object_pattern,
                cs.FIELD_VALUE: call_expr,
            },
        )

        mixin._process_variable_declarator_for_commonjs(declarator, "test_module")

        mock_import_processor._resolve_js_module_path.assert_not_called()


class TestEs6ExportConstQueryCapture:
    @pytest.fixture(scope="class")
    def ts_parser_and_language(self) -> tuple:
        parsers, queries = load_parsers()
        parser = parsers[cs.SupportedLanguage.TS]
        lang = queries[cs.SupportedLanguage.TS][cs.QUERY_LANGUAGE]
        return parser, lang

    def _run_export_const_query(self, parser, lang, code: str) -> dict:
        tree = parser.parse(bytes(code, cs.ENCODING_UTF8))
        cleaned = textwrap.dedent(cs.JS_ES6_EXPORT_CONST_QUERY).strip()
        query = Query(lang, cleaned)
        cursor = QueryCursor(query)
        return cursor.captures(tree.root_node)

    def test_captures_arrow_function_export(self, ts_parser_and_language) -> None:
        parser, lang = ts_parser_and_language
        code = "export const handleClick = (e) => { e.preventDefault(); };"
        captures = self._run_export_const_query(parser, lang, code)

        names = captures.get(cs.CAPTURE_EXPORT_NAME, [])
        funcs = captures.get(cs.CAPTURE_EXPORT_FUNCTION, [])
        assert len(names) == 1
        assert names[0].text.decode(cs.ENCODING_UTF8) == "handleClick"
        assert funcs[0].type == cs.TS_ARROW_FUNCTION

    def test_captures_function_expression_export(self, ts_parser_and_language) -> None:
        parser, lang = ts_parser_and_language
        code = "export const greet = function(name) { return name; };"
        captures = self._run_export_const_query(parser, lang, code)

        names = captures.get(cs.CAPTURE_EXPORT_NAME, [])
        funcs = captures.get(cs.CAPTURE_EXPORT_FUNCTION, [])
        assert len(names) == 1
        assert names[0].text.decode(cs.ENCODING_UTF8) == "greet"
        assert funcs[0].type == cs.TS_FUNCTION_EXPRESSION

    def test_captures_call_expression_factory_export(
        self, ts_parser_and_language
    ) -> None:
        parser, lang = ts_parser_and_language
        code = (
            "export const getFlights = createSelector(selectState, (s) => s.flights);"
        )
        captures = self._run_export_const_query(parser, lang, code)

        names = captures.get(cs.CAPTURE_EXPORT_NAME, [])
        funcs = captures.get(cs.CAPTURE_EXPORT_FUNCTION, [])
        assert len(names) == 1
        assert names[0].text.decode(cs.ENCODING_UTF8) == "getFlights"
        assert funcs[0].type == cs.TS_CALL_EXPRESSION

    def test_captures_connect_factory_export(self, ts_parser_and_language) -> None:
        parser, lang = ts_parser_and_language
        code = "export const mapStateToProps = connect(mapState, mapDispatch);"
        captures = self._run_export_const_query(parser, lang, code)

        names = captures.get(cs.CAPTURE_EXPORT_NAME, [])
        funcs = captures.get(cs.CAPTURE_EXPORT_FUNCTION, [])
        assert len(names) == 1
        assert names[0].text.decode(cs.ENCODING_UTF8) == "mapStateToProps"
        assert funcs[0].type == cs.TS_CALL_EXPRESSION

    def test_skips_string_literal_export(self, ts_parser_and_language) -> None:
        parser, lang = ts_parser_and_language
        code = 'export const API_URL = "https://api.example.com";'
        captures = self._run_export_const_query(parser, lang, code)

        names = captures.get(cs.CAPTURE_EXPORT_NAME, [])
        assert len(names) == 0


class TestEs6ExportBlockQueryCapture:
    @pytest.fixture(scope="class")
    def ts_parser_and_language(self) -> tuple:
        parsers, queries = load_parsers()
        parser = parsers[cs.SupportedLanguage.TS]
        lang = queries[cs.SupportedLanguage.TS][cs.QUERY_LANGUAGE]
        return parser, lang

    def _run_export_block_query(self, parser, lang, code: str) -> dict:
        tree = parser.parse(bytes(code, cs.ENCODING_UTF8))
        cleaned = textwrap.dedent(cs.JS_ES6_EXPORT_BLOCK_QUERY).strip()
        query = Query(lang, cleaned)
        cursor = QueryCursor(query)
        return cursor.captures(tree.root_node)

    def test_captures_named_exports(self, ts_parser_and_language) -> None:
        parser, lang = ts_parser_and_language
        code = """
const getFeatureDecision = () => true;
const getConfigServiceValue = () => 'value';
export { getFeatureDecision, getConfigServiceValue };
"""
        captures = self._run_export_block_query(parser, lang, code)
        names = captures.get(cs.CAPTURE_EXPORT_NAME, [])
        decoded = [n.text.decode(cs.ENCODING_UTF8) for n in names]
        assert "getFeatureDecision" in decoded
        assert "getConfigServiceValue" in decoded

    def test_creates_exports_relationship_for_known_function(self) -> None:
        ingestor = MagicMock()
        function_registry = defaultdict(set)
        function_registry["myproject.module.myFunc"] = set()

        mixin = ConcreteModuleSystemMixin(
            ingestor=ingestor,
            import_processor=MagicMock(),
            function_registry=function_registry,
            simple_name_lookup=defaultdict(set),
        )

        parsers, queries = load_parsers()
        parser = parsers[cs.SupportedLanguage.TS]

        code = """
const myFunc = () => true;
export { myFunc };
"""
        tree = parser.parse(bytes(code, cs.ENCODING_UTF8))

        mixin._ingest_es6_exports(
            tree.root_node,
            "myproject.module",
            cs.SupportedLanguage.TS,
            queries,
        )

        ingestor.ensure_relationship_batch.assert_any_call(
            (cs.NodeLabel.MODULE, cs.KEY_QUALIFIED_NAME, "myproject.module"),
            cs.RelationshipType.EXPORTS,
            (
                cs.NodeLabel.FUNCTION,
                cs.KEY_QUALIFIED_NAME,
                "myproject.module.myFunc",
            ),
        )

    def test_skips_export_for_unknown_function(self) -> None:
        ingestor = MagicMock()
        function_registry = defaultdict(set)

        mixin = ConcreteModuleSystemMixin(
            ingestor=ingestor,
            import_processor=MagicMock(),
            function_registry=function_registry,
            simple_name_lookup=defaultdict(set),
        )

        parsers, queries = load_parsers()
        parser = parsers[cs.SupportedLanguage.TS]

        code = """
export { unknownFunc };
"""
        tree = parser.parse(bytes(code, cs.ENCODING_UTF8))

        mixin._ingest_es6_exports(
            tree.root_node,
            "myproject.module",
            cs.SupportedLanguage.TS,
            queries,
        )

        for call_args in ingestor.ensure_relationship_batch.call_args_list:
            args = call_args[0]
            if len(args) >= 3:
                assert args[2] != (
                    cs.NodeLabel.FUNCTION,
                    cs.KEY_QUALIFIED_NAME,
                    "myproject.module.unknownFunc",
                )
