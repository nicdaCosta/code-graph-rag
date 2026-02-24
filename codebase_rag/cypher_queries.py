from .constants import CYPHER_DEFAULT_LIMIT

CYPHER_DELETE_ALL = "MATCH (n) DETACH DELETE n;"

CYPHER_LIST_PROJECTS = "MATCH (p:Project) RETURN p.name AS name ORDER BY p.name"

CYPHER_DELETE_PROJECT = """
MATCH (p:Project {name: $project_name})
OPTIONAL MATCH (p)-[:CONTAINS_PACKAGE|CONTAINS_FOLDER|CONTAINS_FILE|CONTAINS_MODULE*]->(container)
OPTIONAL MATCH (container)-[:DEFINES|DEFINES_METHOD*]->(defined)
DETACH DELETE p, container, defined
"""

CYPHER_EXAMPLE_DECORATED_FUNCTIONS = f"""MATCH (n:Function|Method)
WHERE ANY(d IN n.decorators WHERE toLower(d) IN ['flow', 'task'])
RETURN n.name AS name, n.qualified_name AS qualified_name, labels(n) AS type
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_CONTENT_BY_PATH = f"""MATCH (n)
WHERE n.path IS NOT NULL AND n.path STARTS WITH 'workflows'
RETURN n.name AS name, n.path AS path, labels(n) AS type
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_KEYWORD_SEARCH = f"""MATCH (n)
WHERE toLower(n.name) CONTAINS 'database' OR (n.qualified_name IS NOT NULL AND toLower(n.qualified_name) CONTAINS 'database')
RETURN n.name AS name, n.qualified_name AS qualified_name, labels(n) AS type
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_FIND_FILE = """MATCH (f:File) WHERE toLower(f.name) = 'readme.md' AND f.path = 'README.md'
RETURN f.path as path, f.name as name, labels(f) as type"""

CYPHER_EXAMPLE_README = f"""MATCH (f:File)
WHERE toLower(f.name) CONTAINS 'readme'
RETURN f.path AS path, f.name AS name, labels(f) AS type
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_PYTHON_FILES = f"""MATCH (f:File)
WHERE f.extension = '.py'
RETURN f.path AS path, f.name AS name, labels(f) AS type
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_TASKS = f"""MATCH (n:Function|Method)
WHERE 'task' IN n.decorators
RETURN n.qualified_name AS qualified_name, n.name AS name, labels(n) AS type
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_FILES_IN_FOLDER = f"""MATCH (f:File)
WHERE f.path STARTS WITH 'services'
RETURN f.path AS path, f.name AS name, labels(f) AS type
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_LIMIT_ONE = """MATCH (f:File) RETURN f.path as path, f.name as name, labels(f) as type LIMIT 1"""

CYPHER_EXAMPLE_FIND_CALLERS = f"""MATCH (caller)-[:CALLS]->(target:Function|Method)
WHERE toLower(target.name) = toLower('targetFunctionName')
  AND (target.is_external IS NULL OR NOT target.is_external)
OPTIONAL MATCH (m:Module)-[:DEFINES*1..4]->(caller)
WITH caller, target,
  coalesce(CASE WHEN caller:Module THEN caller.path ELSE null END, m.path) AS file_path
WHERE file_path IS NOT NULL
RETURN DISTINCT file_path, caller.name AS caller_name, target.name AS called_function
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_FUNCTION_WITH_PATH = f"""MATCH (m:Module)-[:DEFINES]->(f:Function)
WHERE toLower(f.name) CONTAINS 'search'
RETURN f.name AS function_name, f.qualified_name AS qualified_name, m.path AS file_path
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_CLASSES_IN_PATH = f"""MATCH (m:Module)-[:DEFINES]->(c:Class)
WHERE m.path STARTS WITH 'src/models'
RETURN c.name AS class_name, c.qualified_name AS qualified_name, m.path AS file_path
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_CLASS_METHODS = f"""MATCH (m:Module)-[:DEFINES]->(c:Class)-[:DEFINES_METHOD]->(method:Method)
WHERE toLower(c.name) = 'userservice'
RETURN method.name AS method_name, c.name AS class_name, m.path AS file_path
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_ANONYMOUS_FUNCTIONS = f"""MATCH (m:Module)-[:DEFINES]->(af:AnonymousFunction)
WHERE m.qualified_name = 'myapp.components.button'
RETURN af.qualified_name AS qualified_name, af.name AS name, af.start_line AS line
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_ANONYMOUS_CALLERS_WITH_TYPE = f"""MATCH (caller)-[:CALLS]->(fn:Function)
WHERE toLower(fn.name) = 'handlesubmit'
RETURN labels(caller)[0] AS caller_type, caller.qualified_name AS caller_qn, caller.name AS caller_name
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_PARENT_FUNCTIONS = f"""MATCH (parent:Function|Method)-[:DEFINES]->(af:AnonymousFunction)
WHERE af.name STARTS WITH 'map_'
RETURN parent.qualified_name AS parent_qn, af.qualified_name AS callback_qn, af.start_line AS line
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_ANONYMOUS_CALL_CHAINS = f"""MATCH (af:AnonymousFunction)-[:CALLS]->(target)
WHERE af.name STARTS WITH 'hook_useEffect_'
RETURN af.qualified_name AS hook_qn, target.name AS calls_function, labels(target)[0] AS target_type
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXAMPLE_ANONYMOUS_BY_LINE_RANGE = f"""MATCH (m:Module)-[:DEFINES*]->(af:AnonymousFunction)
WHERE m.qualified_name = 'myapp.components.button' AND af.start_line >= 50 AND af.end_line <= 100
RETURN af.qualified_name AS qualified_name, af.name AS name, af.start_line AS start_line, af.end_line AS end_line
LIMIT {CYPHER_DEFAULT_LIMIT}"""

CYPHER_EXPORT_NODES = """
MATCH (n)
RETURN id(n) as node_id, labels(n) as labels, properties(n) as properties
"""

CYPHER_EXPORT_RELATIONSHIPS = """
MATCH (a)-[r]->(b)
RETURN id(a) as from_id, id(b) as to_id, type(r) as type, properties(r) as properties
"""

CYPHER_RETURN_COUNT = "RETURN count(r) as created"
CYPHER_SET_PROPS_RETURN_COUNT = "SET r += row.props\nRETURN count(r) as created"

CYPHER_GET_FUNCTION_SOURCE_LOCATION = """
MATCH (m:Module)-[:DEFINES]->(n)
WHERE id(n) = $node_id
RETURN n.qualified_name AS qualified_name, n.start_line AS start_line,
       n.end_line AS end_line, m.path AS path
"""

CYPHER_FIND_BY_QUALIFIED_NAME = """
MATCH (n) WHERE n.qualified_name = $qn
OPTIONAL MATCH (m:Module)-[*]-(n)
RETURN n.name AS name, n.start_line AS start, n.end_line AS end, m.path AS path, n.docstring AS docstring
LIMIT 1
"""


def wrap_with_unwind(query: str) -> str:
    return f"UNWIND $batch AS row\n{query}"


def build_nodes_by_ids_query(node_ids: list[int]) -> str:
    placeholders = ", ".join(f"${i}" for i in range(len(node_ids)))
    return f"""
MATCH (n)
WHERE id(n) IN [{placeholders}]
RETURN id(n) AS node_id, n.qualified_name AS qualified_name,
       labels(n) AS type, n.name AS name
ORDER BY n.qualified_name
"""


def build_constraint_query(label: str, prop: str) -> str:
    return f"CREATE CONSTRAINT ON (n:{label}) ASSERT n.{prop} IS UNIQUE;"


def build_index_query(label: str, prop: str) -> str:
    return f"CREATE INDEX ON :{label}({prop});"


def build_merge_node_query(label: str, id_key: str) -> str:
    return f"MERGE (n:{label} {{{id_key}: row.id}})\nSET n += row.props"


def build_merge_relationship_query(
    from_label: str,
    from_key: str,
    rel_type: str,
    to_label: str,
    to_key: str,
    has_props: bool = False,
) -> str:
    query = (
        f"MATCH (a:{from_label} {{{from_key}: row.from_val}}), "
        f"(b:{to_label} {{{to_key}: row.to_val}})\n"
        f"MERGE (a)-[r:{rel_type}]->(b)\n"
    )
    query += CYPHER_SET_PROPS_RETURN_COUNT if has_props else CYPHER_RETURN_COUNT
    return query
