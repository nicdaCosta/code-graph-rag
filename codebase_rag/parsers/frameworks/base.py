from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from ... import constants as cs

if TYPE_CHECKING:
    from pathlib import Path

    from ...types_defs import ASTNode, PropertyDict


@dataclass
class ComponentInfo:
    name: str
    qualified_name: str
    component_type: str
    start_line: int
    end_line: int
    props_interface: str | None = None
    is_exported: bool = False
    properties: dict[str, str] = field(default_factory=dict)


@dataclass
class HookUsage:
    hook_name: str
    qualified_name: str
    component_qn: str
    start_line: int
    is_builtin: bool = True


@dataclass
class ComponentRelationship:
    source_qn: str
    source_label: cs.NodeLabel
    relationship_type: cs.RelationshipType
    target_qn: str
    target_label: cs.NodeLabel
    properties: dict[str, str] = field(default_factory=dict)


class FrameworkHandler(ABC):
    @property
    @abstractmethod
    def framework_name(self) -> str:
        pass

    @abstractmethod
    def detect_framework(self, imports: set[str]) -> bool:
        pass

    @abstractmethod
    def extract_components(
        self,
        root_node: ASTNode,
        module_qn: str,
        file_path: Path,
    ) -> list[ComponentInfo]:
        pass

    @abstractmethod
    def extract_hooks(
        self,
        root_node: ASTNode,
        module_qn: str,
        components: list[ComponentInfo],
    ) -> list[HookUsage]:
        pass

    @abstractmethod
    def extract_relationships(
        self,
        root_node: ASTNode,
        module_qn: str,
        components: list[ComponentInfo],
    ) -> list[ComponentRelationship]:
        pass

    def to_node_props(self, component: ComponentInfo) -> PropertyDict:
        props: PropertyDict = {
            cs.KEY_QUALIFIED_NAME: component.qualified_name,
            cs.KEY_NAME: component.name,
            "component_type": component.component_type,
            cs.KEY_START_LINE: component.start_line,
            cs.KEY_END_LINE: component.end_line,
        }
        if component.props_interface:
            props["props_interface"] = component.props_interface
        if component.is_exported:
            props[cs.KEY_IS_EXPORTED] = True
        props.update(component.properties)
        return props
