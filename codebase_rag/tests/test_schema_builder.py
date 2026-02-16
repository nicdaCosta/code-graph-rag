from __future__ import annotations

from codebase_rag.constants import NodeLabel, RelationshipType
from codebase_rag.schema_builder import GRAPH_SCHEMA_DEFINITION
from codebase_rag.types_defs import RELATIONSHIP_SCHEMAS


class TestCallsRelationshipSchema:
    def test_calls_sources_include_module(self) -> None:
        calls_schema = next(
            s for s in RELATIONSHIP_SCHEMAS if s.rel_type == RelationshipType.CALLS
        )

        assert NodeLabel.MODULE in calls_schema.sources

    def test_graph_schema_definition_reflects_module_caller(self) -> None:
        assert (
            "(Function|Method|Module) -[:CALLS]-> (Function|Method)"
            in GRAPH_SCHEMA_DEFINITION
        )
