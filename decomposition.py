"""Core data structures for problem decomposition"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SubComponent:
    """Represents a 1-level deep goal sub-component of a problem statement.
    
    Each sub-component has:
    - A goal (what needs to be achieved)
    - Entities (what objects/resources are involved)
    - Dependencies (other sub-components this depends on)
    - Three weight dimensions: difficulty, dependency_order, failure_impact
    """
    
    # Core fields
    component_id: str  # Unique identifier (e.g., "comp_0", "comp_1")
    goal: str  # e.g., "having rice", "count legs for dogs"
    entities: list[str]  # e.g., ["rice"], ["dogs", "3"]
    dependencies: list[str] = field(default_factory=list)  # IDs of dependent sub-components
    
    # Weight dimensions (0.0-1.0 scale)
    difficulty: float = 0.5  # How hard is this to achieve?
    dependency_order: int = 0  # Topological order (0 = no deps, higher = later)
    failure_impact: float = 0.5  # Impact if this fails (0.0 = low, 1.0 = critical)
    
    # Metadata
    description: Optional[str] = None  # Optional human-readable description
    
    def __post_init__(self):
        """Validate component after initialization"""
        if not self.component_id:
            raise ValueError("component_id cannot be empty")
        if not self.goal:
            raise ValueError("goal cannot be empty")
        if not isinstance(self.entities, list):
            raise ValueError("entities must be a list")
        if not isinstance(self.dependencies, list):
            raise ValueError("dependencies must be a list")
        
        # Validate weights are in valid range
        if not 0.0 <= self.difficulty <= 1.0:
            raise ValueError(f"difficulty must be between 0.0 and 1.0, got {self.difficulty}")
        if not 0.0 <= self.failure_impact <= 1.0:
            raise ValueError(f"failure_impact must be between 0.0 and 1.0, got {self.failure_impact}")
        if self.dependency_order < 0:
            raise ValueError(f"dependency_order must be non-negative, got {self.dependency_order}")


@dataclass
class ProblemDecomposition:
    """Complete decomposition of a problem statement into sub-components.
    
    Contains:
    - The original problem statement
    - All sub-components with their relationships
    - The main goal
    - Dependency graph structure
    """
    
    problem_statement: str
    main_goal: str
    sub_components: dict[str, SubComponent] = field(default_factory=dict)
    
    def add_component(self, component: SubComponent) -> None:
        """Add a sub-component to the decomposition"""
        if component.component_id in self.sub_components:
            raise ValueError(f"Component {component.component_id} already exists")
        self.sub_components[component.component_id] = component
    
    def get_component(self, component_id: str) -> Optional[SubComponent]:
        """Get a sub-component by ID"""
        return self.sub_components.get(component_id)
    
    def validate_dependencies(self) -> bool:
        """Validate that all dependencies reference existing components"""
        all_ids = set(self.sub_components.keys())
        for component in self.sub_components.values():
            for dep_id in component.dependencies:
                if dep_id not in all_ids:
                    return False
        return True
    
    def get_dependency_graph(self) -> dict[str, list[str]]:
        """Get dependency graph as adjacency list (component_id -> list of dependencies)"""
        graph = {}
        for comp_id, component in self.sub_components.items():
            graph[comp_id] = component.dependencies.copy()
        return graph
    
    def get_reverse_dependency_graph(self) -> dict[str, list[str]]:
        """Get reverse dependency graph (component_id -> list of dependents)"""
        reverse_graph = {comp_id: [] for comp_id in self.sub_components.keys()}
        for comp_id, component in self.sub_components.items():
            for dep_id in component.dependencies:
                if dep_id in reverse_graph:
                    reverse_graph[dep_id].append(comp_id)
        return reverse_graph
    
    def topological_sort(self) -> list[str]:
        """Perform topological sort to determine dependency order.
        
        Returns list of component IDs in execution order (dependencies first).
        """
        graph = self.get_dependency_graph()
        in_degree = {comp_id: len(deps) for comp_id, deps in graph.items()}
        queue = [comp_id for comp_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # Find all nodes that depend on this node
            for comp_id, deps in graph.items():
                if node in deps:
                    in_degree[comp_id] -= 1
                    if in_degree[comp_id] == 0:
                        queue.append(comp_id)
        
        # Check for cycles
        if len(result) != len(self.sub_components):
            raise ValueError("Circular dependency detected in problem decomposition")
        
        return result
    
    def update_dependency_orders(self) -> None:
        """Update dependency_order for all components based on topological sort"""
        sorted_order = self.topological_sort()
        order_map = {comp_id: idx for idx, comp_id in enumerate(sorted_order)}
        
        for component in self.sub_components.values():
            component.dependency_order = order_map[component.component_id]
