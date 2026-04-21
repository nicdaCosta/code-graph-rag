from google.protobuf import struct_pb2 as _struct_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GraphCodeIndex(_message.Message):
    __slots__ = ()
    NODES_FIELD_NUMBER: _ClassVar[int]
    RELATIONSHIPS_FIELD_NUMBER: _ClassVar[int]
    nodes: _containers.RepeatedCompositeFieldContainer[Node]
    relationships: _containers.RepeatedCompositeFieldContainer[Relationship]
    def __init__(self, nodes: _Optional[_Iterable[_Union[Node, _Mapping]]] = ..., relationships: _Optional[_Iterable[_Union[Relationship, _Mapping]]] = ...) -> None: ...

class Node(_message.Message):
    __slots__ = ()
    PROJECT_FIELD_NUMBER: _ClassVar[int]
    PACKAGE_FIELD_NUMBER: _ClassVar[int]
    FOLDER_FIELD_NUMBER: _ClassVar[int]
    MODULE_FIELD_NUMBER: _ClassVar[int]
    CLASS_NODE_FIELD_NUMBER: _ClassVar[int]
    FUNCTION_FIELD_NUMBER: _ClassVar[int]
    METHOD_FIELD_NUMBER: _ClassVar[int]
    FILE_FIELD_NUMBER: _ClassVar[int]
    EXTERNAL_PACKAGE_FIELD_NUMBER: _ClassVar[int]
    MODULE_IMPLEMENTATION_FIELD_NUMBER: _ClassVar[int]
    MODULE_INTERFACE_FIELD_NUMBER: _ClassVar[int]
    INTERFACE_NODE_FIELD_NUMBER: _ClassVar[int]
    ENUM_NODE_FIELD_NUMBER: _ClassVar[int]
    TYPE_NODE_FIELD_NUMBER: _ClassVar[int]
    UNION_NODE_FIELD_NUMBER: _ClassVar[int]
    ANONYMOUS_FUNCTION_FIELD_NUMBER: _ClassVar[int]
    CSS_RULE_FIELD_NUMBER: _ClassVar[int]
    CSS_SELECTOR_FIELD_NUMBER: _ClassVar[int]
    CSS_VARIABLE_FIELD_NUMBER: _ClassVar[int]
    SCSS_VARIABLE_FIELD_NUMBER: _ClassVar[int]
    SCSS_MIXIN_FIELD_NUMBER: _ClassVar[int]
    SCSS_FUNCTION_FIELD_NUMBER: _ClassVar[int]
    MEDIA_QUERY_FIELD_NUMBER: _ClassVar[int]
    KEYFRAME_ANIMATION_FIELD_NUMBER: _ClassVar[int]
    HTML_ELEMENT_FIELD_NUMBER: _ClassVar[int]
    REACT_COMPONENT_FIELD_NUMBER: _ClassVar[int]
    REACT_HOOK_FIELD_NUMBER: _ClassVar[int]
    REACT_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    STYLED_COMPONENT_FIELD_NUMBER: _ClassVar[int]
    CSS_IN_JS_RULE_FIELD_NUMBER: _ClassVar[int]
    project: Project
    package: Package
    folder: Folder
    module: Module
    class_node: Class
    function: Function
    method: Method
    file: File
    external_package: ExternalPackage
    module_implementation: ModuleImplementation
    module_interface: ModuleInterface
    interface_node: Interface
    enum_node: Enum
    type_node: Type
    union_node: Union
    anonymous_function: AnonymousFunction
    css_rule: CssRule
    css_selector: CssSelector
    css_variable: CssVariable
    scss_variable: ScssVariable
    scss_mixin: ScssMixin
    scss_function: ScssFunction
    media_query: MediaQuery
    keyframe_animation: KeyframeAnimation
    html_element: HtmlElement
    react_component: ReactComponent
    react_hook: ReactHook
    react_context: ReactContext
    styled_component: StyledComponent
    css_in_js_rule: CssInJsRule
    def __init__(self, project: _Optional[_Union[Project, _Mapping]] = ..., package: _Optional[_Union[Package, _Mapping]] = ..., folder: _Optional[_Union[Folder, _Mapping]] = ..., module: _Optional[_Union[Module, _Mapping]] = ..., class_node: _Optional[_Union[Class, _Mapping]] = ..., function: _Optional[_Union[Function, _Mapping]] = ..., method: _Optional[_Union[Method, _Mapping]] = ..., file: _Optional[_Union[File, _Mapping]] = ..., external_package: _Optional[_Union[ExternalPackage, _Mapping]] = ..., module_implementation: _Optional[_Union[ModuleImplementation, _Mapping]] = ..., module_interface: _Optional[_Union[ModuleInterface, _Mapping]] = ..., interface_node: _Optional[_Union[Interface, _Mapping]] = ..., enum_node: _Optional[_Union[Enum, _Mapping]] = ..., type_node: _Optional[_Union[Type, _Mapping]] = ..., union_node: _Optional[_Union[Union, _Mapping]] = ..., anonymous_function: _Optional[_Union[AnonymousFunction, _Mapping]] = ..., css_rule: _Optional[_Union[CssRule, _Mapping]] = ..., css_selector: _Optional[_Union[CssSelector, _Mapping]] = ..., css_variable: _Optional[_Union[CssVariable, _Mapping]] = ..., scss_variable: _Optional[_Union[ScssVariable, _Mapping]] = ..., scss_mixin: _Optional[_Union[ScssMixin, _Mapping]] = ..., scss_function: _Optional[_Union[ScssFunction, _Mapping]] = ..., media_query: _Optional[_Union[MediaQuery, _Mapping]] = ..., keyframe_animation: _Optional[_Union[KeyframeAnimation, _Mapping]] = ..., html_element: _Optional[_Union[HtmlElement, _Mapping]] = ..., react_component: _Optional[_Union[ReactComponent, _Mapping]] = ..., react_hook: _Optional[_Union[ReactHook, _Mapping]] = ..., react_context: _Optional[_Union[ReactContext, _Mapping]] = ..., styled_component: _Optional[_Union[StyledComponent, _Mapping]] = ..., css_in_js_rule: _Optional[_Union[CssInJsRule, _Mapping]] = ...) -> None: ...

class Relationship(_message.Message):
    __slots__ = ()
    class RelationshipType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
        __slots__ = ()
        RELATIONSHIP_TYPE_UNSPECIFIED: _ClassVar[Relationship.RelationshipType]
        CONTAINS_PACKAGE: _ClassVar[Relationship.RelationshipType]
        CONTAINS_FOLDER: _ClassVar[Relationship.RelationshipType]
        CONTAINS_FILE: _ClassVar[Relationship.RelationshipType]
        CONTAINS_MODULE: _ClassVar[Relationship.RelationshipType]
        DEFINES: _ClassVar[Relationship.RelationshipType]
        DEFINES_METHOD: _ClassVar[Relationship.RelationshipType]
        IMPORTS: _ClassVar[Relationship.RelationshipType]
        INHERITS: _ClassVar[Relationship.RelationshipType]
        OVERRIDES: _ClassVar[Relationship.RelationshipType]
        CALLS: _ClassVar[Relationship.RelationshipType]
        DEPENDS_ON_EXTERNAL: _ClassVar[Relationship.RelationshipType]
        IMPLEMENTS_MODULE: _ClassVar[Relationship.RelationshipType]
        IMPLEMENTS: _ClassVar[Relationship.RelationshipType]
        EXPORTS: _ClassVar[Relationship.RelationshipType]
        EXPORTS_MODULE: _ClassVar[Relationship.RelationshipType]
        STYLES: _ClassVar[Relationship.RelationshipType]
        REFERENCES_STYLESHEET: _ClassVar[Relationship.RelationshipType]
        DEFINES_STYLE: _ClassVar[Relationship.RelationshipType]
        HAS_SELECTOR: _ClassVar[Relationship.RelationshipType]
        USES_MIXIN: _ClassVar[Relationship.RelationshipType]
        USES_VARIABLE: _ClassVar[Relationship.RelationshipType]
        SCSS_IMPORTS: _ClassVar[Relationship.RelationshipType]
        DEFINES_VARIABLE: _ClassVar[Relationship.RelationshipType]
        DEFINES_MEDIA_QUERY: _ClassVar[Relationship.RelationshipType]
        DEFINES_KEYFRAME: _ClassVar[Relationship.RelationshipType]
        USES_CSS_VARIABLE: _ClassVar[Relationship.RelationshipType]
        RENDERS: _ClassVar[Relationship.RelationshipType]
        USES_HOOK: _ClassVar[Relationship.RelationshipType]
        PROVIDES_CONTEXT: _ClassVar[Relationship.RelationshipType]
        CONSUMES_CONTEXT: _ClassVar[Relationship.RelationshipType]
        ACCEPTS_PROPS: _ClassVar[Relationship.RelationshipType]
        HAS_STYLED_COMPONENT: _ClassVar[Relationship.RelationshipType]
        STYLED_WITH: _ClassVar[Relationship.RelationshipType]
    RELATIONSHIP_TYPE_UNSPECIFIED: Relationship.RelationshipType
    CONTAINS_PACKAGE: Relationship.RelationshipType
    CONTAINS_FOLDER: Relationship.RelationshipType
    CONTAINS_FILE: Relationship.RelationshipType
    CONTAINS_MODULE: Relationship.RelationshipType
    DEFINES: Relationship.RelationshipType
    DEFINES_METHOD: Relationship.RelationshipType
    IMPORTS: Relationship.RelationshipType
    INHERITS: Relationship.RelationshipType
    OVERRIDES: Relationship.RelationshipType
    CALLS: Relationship.RelationshipType
    DEPENDS_ON_EXTERNAL: Relationship.RelationshipType
    IMPLEMENTS_MODULE: Relationship.RelationshipType
    IMPLEMENTS: Relationship.RelationshipType
    EXPORTS: Relationship.RelationshipType
    EXPORTS_MODULE: Relationship.RelationshipType
    STYLES: Relationship.RelationshipType
    REFERENCES_STYLESHEET: Relationship.RelationshipType
    DEFINES_STYLE: Relationship.RelationshipType
    HAS_SELECTOR: Relationship.RelationshipType
    USES_MIXIN: Relationship.RelationshipType
    USES_VARIABLE: Relationship.RelationshipType
    SCSS_IMPORTS: Relationship.RelationshipType
    DEFINES_VARIABLE: Relationship.RelationshipType
    DEFINES_MEDIA_QUERY: Relationship.RelationshipType
    DEFINES_KEYFRAME: Relationship.RelationshipType
    USES_CSS_VARIABLE: Relationship.RelationshipType
    RENDERS: Relationship.RelationshipType
    USES_HOOK: Relationship.RelationshipType
    PROVIDES_CONTEXT: Relationship.RelationshipType
    CONSUMES_CONTEXT: Relationship.RelationshipType
    ACCEPTS_PROPS: Relationship.RelationshipType
    HAS_STYLED_COMPONENT: Relationship.RelationshipType
    STYLED_WITH: Relationship.RelationshipType
    TYPE_FIELD_NUMBER: _ClassVar[int]
    SOURCE_ID_FIELD_NUMBER: _ClassVar[int]
    TARGET_ID_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    SOURCE_LABEL_FIELD_NUMBER: _ClassVar[int]
    TARGET_LABEL_FIELD_NUMBER: _ClassVar[int]
    type: Relationship.RelationshipType
    source_id: str
    target_id: str
    properties: _struct_pb2.Struct
    source_label: str
    target_label: str
    def __init__(self, type: _Optional[_Union[Relationship.RelationshipType, str]] = ..., source_id: _Optional[str] = ..., target_id: _Optional[str] = ..., properties: _Optional[_Union[_struct_pb2.Struct, _Mapping]] = ..., source_label: _Optional[str] = ..., target_label: _Optional[str] = ...) -> None: ...

class Project(_message.Message):
    __slots__ = ()
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class Package(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    path: str
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class Folder(_message.Message):
    __slots__ = ()
    PATH_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    path: str
    name: str
    def __init__(self, path: _Optional[str] = ..., name: _Optional[str] = ...) -> None: ...

class File(_message.Message):
    __slots__ = ()
    PATH_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    EXTENSION_FIELD_NUMBER: _ClassVar[int]
    path: str
    name: str
    extension: str
    def __init__(self, path: _Optional[str] = ..., name: _Optional[str] = ..., extension: _Optional[str] = ...) -> None: ...

class Module(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    path: str
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class ModuleImplementation(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    IMPLEMENTS_MODULE_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    path: str
    implements_module: str
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., path: _Optional[str] = ..., implements_module: _Optional[str] = ...) -> None: ...

class ModuleInterface(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PATH_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    path: str
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., path: _Optional[str] = ...) -> None: ...

class ExternalPackage(_message.Message):
    __slots__ = ()
    NAME_FIELD_NUMBER: _ClassVar[int]
    name: str
    def __init__(self, name: _Optional[str] = ...) -> None: ...

class Function(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DOCSTRING_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    DECORATORS_FIELD_NUMBER: _ClassVar[int]
    IS_EXPORTED_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    docstring: str
    start_line: int
    end_line: int
    decorators: _containers.RepeatedScalarFieldContainer[str]
    is_exported: bool
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., docstring: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ..., decorators: _Optional[_Iterable[str]] = ..., is_exported: _Optional[bool] = ...) -> None: ...

class Method(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DOCSTRING_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    DECORATORS_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    docstring: str
    start_line: int
    end_line: int
    decorators: _containers.RepeatedScalarFieldContainer[str]
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., docstring: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ..., decorators: _Optional[_Iterable[str]] = ...) -> None: ...

class Class(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DOCSTRING_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    DECORATORS_FIELD_NUMBER: _ClassVar[int]
    IS_EXPORTED_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    docstring: str
    start_line: int
    end_line: int
    decorators: _containers.RepeatedScalarFieldContainer[str]
    is_exported: bool
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., docstring: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ..., decorators: _Optional[_Iterable[str]] = ..., is_exported: _Optional[bool] = ...) -> None: ...

class Interface(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DOCSTRING_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    DECORATORS_FIELD_NUMBER: _ClassVar[int]
    IS_EXPORTED_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    docstring: str
    start_line: int
    end_line: int
    decorators: _containers.RepeatedScalarFieldContainer[str]
    is_exported: bool
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., docstring: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ..., decorators: _Optional[_Iterable[str]] = ..., is_exported: _Optional[bool] = ...) -> None: ...

class Enum(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DOCSTRING_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    DECORATORS_FIELD_NUMBER: _ClassVar[int]
    IS_EXPORTED_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    docstring: str
    start_line: int
    end_line: int
    decorators: _containers.RepeatedScalarFieldContainer[str]
    is_exported: bool
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., docstring: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ..., decorators: _Optional[_Iterable[str]] = ..., is_exported: _Optional[bool] = ...) -> None: ...

class Type(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DOCSTRING_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    DECORATORS_FIELD_NUMBER: _ClassVar[int]
    IS_EXPORTED_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    docstring: str
    start_line: int
    end_line: int
    decorators: _containers.RepeatedScalarFieldContainer[str]
    is_exported: bool
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., docstring: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ..., decorators: _Optional[_Iterable[str]] = ..., is_exported: _Optional[bool] = ...) -> None: ...

class Union(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DOCSTRING_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    DECORATORS_FIELD_NUMBER: _ClassVar[int]
    IS_EXPORTED_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    docstring: str
    start_line: int
    end_line: int
    decorators: _containers.RepeatedScalarFieldContainer[str]
    is_exported: bool
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., docstring: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ..., decorators: _Optional[_Iterable[str]] = ..., is_exported: _Optional[bool] = ...) -> None: ...

class AnonymousFunction(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DOCSTRING_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    docstring: str
    start_line: int
    end_line: int
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., docstring: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ...) -> None: ...

class CssRule(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    start_line: int
    end_line: int
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ...) -> None: ...

class CssSelector(_message.Message):
    __slots__ = ()
    NAME_FIELD_NUMBER: _ClassVar[int]
    SELECTOR_TYPE_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    name: str
    selector_type: str
    start_line: int
    end_line: int
    def __init__(self, name: _Optional[str] = ..., selector_type: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ...) -> None: ...

class CssVariable(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    value: str
    start_line: int
    end_line: int
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., value: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ...) -> None: ...

class ScssVariable(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    value: str
    start_line: int
    end_line: int
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., value: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ...) -> None: ...

class ScssMixin(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    parameters: _containers.RepeatedScalarFieldContainer[str]
    start_line: int
    end_line: int
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., parameters: _Optional[_Iterable[str]] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ...) -> None: ...

class ScssFunction(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    PARAMETERS_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    parameters: _containers.RepeatedScalarFieldContainer[str]
    start_line: int
    end_line: int
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., parameters: _Optional[_Iterable[str]] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ...) -> None: ...

class MediaQuery(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    CONDITION_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    condition: str
    start_line: int
    end_line: int
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., condition: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ...) -> None: ...

class KeyframeAnimation(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    KEYFRAMES_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    keyframes: str
    start_line: int
    end_line: int
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., keyframes: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ...) -> None: ...

class HtmlElement(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    TAG_NAME_FIELD_NUMBER: _ClassVar[int]
    ELEMENT_ID_FIELD_NUMBER: _ClassVar[int]
    ELEMENT_CLASSES_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    tag_name: str
    element_id: str
    element_classes: str
    start_line: int
    end_line: int
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., tag_name: _Optional[str] = ..., element_id: _Optional[str] = ..., element_classes: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ...) -> None: ...

class ReactComponent(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    COMPONENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    PROPS_INTERFACE_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    IS_EXPORTED_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    component_type: str
    props_interface: str
    start_line: int
    end_line: int
    is_exported: bool
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., component_type: _Optional[str] = ..., props_interface: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ..., is_exported: _Optional[bool] = ...) -> None: ...

class ReactHook(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    IS_BUILTIN_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    is_builtin: bool
    start_line: int
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., is_builtin: _Optional[bool] = ..., start_line: _Optional[int] = ...) -> None: ...

class ReactContext(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    start_line: int
    end_line: int
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ...) -> None: ...

class StyledComponent(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    COMPONENT_TYPE_FIELD_NUMBER: _ClassVar[int]
    PROPS_INTERFACE_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    IS_EXPORTED_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    component_type: str
    props_interface: str
    start_line: int
    end_line: int
    is_exported: bool
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., component_type: _Optional[str] = ..., props_interface: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ..., is_exported: _Optional[bool] = ...) -> None: ...

class CssInJsRule(_message.Message):
    __slots__ = ()
    QUALIFIED_NAME_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    START_LINE_FIELD_NUMBER: _ClassVar[int]
    END_LINE_FIELD_NUMBER: _ClassVar[int]
    qualified_name: str
    name: str
    start_line: int
    end_line: int
    def __init__(self, qualified_name: _Optional[str] = ..., name: _Optional[str] = ..., start_line: _Optional[int] = ..., end_line: _Optional[int] = ...) -> None: ...
