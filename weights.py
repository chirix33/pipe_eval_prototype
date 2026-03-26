"""Heuristic weight calculators for sub-components"""

from typing import Optional

from .decomposition import ProblemDecomposition, SubComponent


class WeightCalculator:
    """Calculates weights for sub-components using heuristics."""
    
    def __init__(self):
        """Initialize the weight calculator"""
        pass
    
    def calculate_difficulty(self, component: SubComponent, decomposition: ProblemDecomposition) -> float:
        """Calculate difficulty weight (0.0-1.0) based on heuristics.
        
        Heuristics:
        - More entities = higher difficulty
        - Complex goal verbs (e.g., "calculate", "verify") = higher difficulty
        - More dependencies = higher difficulty
        
        Args:
            component: The sub-component to evaluate
            decomposition: The full problem decomposition
            
        Returns:
            Difficulty score between 0.0 and 1.0
        """
        difficulty = 0.0
        
        # Entity count factor (normalized to 0-0.4)
        num_entities = len(component.entities)
        entity_factor = min(0.4, num_entities / 10.0)  # Cap at 0.4 for 10+ entities
        difficulty += entity_factor
        
        # Goal verb complexity factor (0-0.3)
        complex_verbs = {
            "calculate", "compute", "verify", "validate", "construct", "generate",
            "solve", "determine", "analyze", "evaluate", "optimize"
        }
        simple_verbs = {
            "have", "get", "obtain", "use", "select", "choose", "find"
        }
        
        goal_lower = component.goal.lower()
        if any(verb in goal_lower for verb in complex_verbs):
            difficulty += 0.3
        elif any(verb in goal_lower for verb in simple_verbs):
            difficulty += 0.1
        
        # Dependency count factor (0-0.3)
        num_deps = len(component.dependencies)
        dep_factor = min(0.3, num_deps / 5.0)  # Cap at 0.3 for 5+ dependencies
        difficulty += dep_factor
        
        return min(1.0, difficulty)
    
    def calculate_failure_impact(
        self, 
        component: SubComponent, 
        decomposition: ProblemDecomposition
    ) -> float:
        """Calculate failure impact weight (0.0-1.0) based on heuristics.
        
        Heuristics:
        - Components with many dependents = higher impact
        - Components on critical path to main goal = higher impact
        - Leaf components (no dependents) = lower impact
        
        Args:
            component: The sub-component to evaluate
            decomposition: The full problem decomposition
            
        Returns:
            Failure impact score between 0.0 and 1.0
        """
        reverse_graph = decomposition.get_reverse_dependency_graph()
        dependents = reverse_graph.get(component.component_id, [])
        
        # Base impact from number of dependents (0-0.6)
        num_dependents = len(dependents)
        total_components = len(decomposition.sub_components)
        if total_components > 0:
            dependent_factor = min(0.6, (num_dependents / total_components) * 2.0)
        else:
            dependent_factor = 0.0
        
        # Critical path factor: components with no dependencies or many dependents
        # are likely on critical path (0-0.4)
        if len(component.dependencies) == 0 and num_dependents > 0:
            # Root component with dependents = critical
            critical_factor = 0.4
        elif num_dependents == 0:
            # Leaf component = less critical (unless it's the only component)
            critical_factor = 0.1 if total_components > 1 else 0.4
        else:
            # Intermediate component
            critical_factor = 0.2
        
        impact = dependent_factor + critical_factor
        
        return min(1.0, impact)
    
    def calculate_all_weights(self, decomposition: ProblemDecomposition) -> None:
        """Calculate and update all weights for all components in a decomposition.
        
        This updates:
        - difficulty
        - dependency_order (via topological sort)
        - failure_impact
        
        Args:
            decomposition: The problem decomposition to update
        """
        # First, update dependency orders via topological sort
        decomposition.update_dependency_orders()
        
        # Then calculate difficulty and failure impact for each component
        for component in decomposition.sub_components.values():
            component.difficulty = self.calculate_difficulty(component, decomposition)
            component.failure_impact = self.calculate_failure_impact(component, decomposition)
    
    def get_priority_score(self, component: SubComponent) -> float:
        """Calculate a combined priority score for a component.
        
        Higher score = higher priority for solving/monitoring.
        
        Formula: beta_0 + (difficulty * w_1) + (dependency_order_norm * w_2) + (failure_impact * w_3)
        where beta_0 is the intercept (constant term).
        
        Args:
            component: The sub-component to score
            
        Returns:
            Priority score (0.0-1.0)
        """
        # Intercept and weights
        beta_0 = 0.1  # Constant term (intercept)
        w_1 = 0.25    # Difficulty weight
        w_2 = 0.15    # Dependency order weight
        w_3 = 0.50    # Failure impact weight

        # Normalize dependency_order (assuming max order is reasonable)
        # For now, normalize by dividing by max(1, order) - this is a simple heuristic
        max_order = max(1, component.dependency_order)
        normalized_order = component.dependency_order / max_order if max_order > 0 else 0.0
        
        priority = (
            beta_0 +
            component.difficulty * w_1 +
            normalized_order * w_2 +
            component.failure_impact * w_3
        )
        
        return min(1.0, priority)
