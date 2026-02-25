"""Decomposition-guided solver: Uses weighted sub-components to guide problem-solving"""

from typing import Any, Dict, List, Optional

from ..decomposition import ProblemDecomposition, SubComponent
from ..weights import WeightCalculator
from .base_solver import BaseSolver, SolverResult


class DecompositionSolver(BaseSolver):
    """Solves problems using decomposition-guided approach.
    
    This solver uses the problem decomposition with weighted sub-components
    to guide the LLM through solving the problem systematically.
    """
    
    DECOMPOSITION_PROMPT_TEMPLATE = """Solve the following problem by addressing each sub-component systematically.

Problem Statement:
{problem_statement}

Main Goal: {main_goal}

Sub-Components (in priority order):
{components_list}

Instructions:
1. Address each sub-component in the order listed above
2. Pay special attention to high-priority components (those with higher priority scores)
3. Ensure you address all dependencies before solving dependent components
4. Show your work for each component
5. Provide your final answer clearly

Begin solving:"""

    def __init__(self, llm_config, weight_calculator: Optional[WeightCalculator] = None):
        """Initialize decomposition-guided solver.
        
        Args:
            llm_config: LLM configuration
            weight_calculator: Optional weight calculator (creates new one if not provided)
        """
        super().__init__(llm_config)
        self.weight_calculator = weight_calculator or WeightCalculator()
    
    def solve(
        self,
        problem_statement: str,
        problem_entry: Optional[Dict[str, Any]] = None,
        decomposition: Optional[ProblemDecomposition] = None,
        **kwargs
    ) -> SolverResult:
        """Solve problem using decomposition guidance.
        
        Args:
            problem_statement: The problem to solve
            problem_entry: Optional problem entry (not directly used)
            decomposition: ProblemDecomposition with weighted components
            **kwargs: Additional arguments
            
        Returns:
            SolverResult with solution and decomposition metadata
        """
        if decomposition is None:
            return SolverResult(
                solution="",
                success=False,
                error_message="Decomposition is required for decomposition-guided solving",
                metadata={"method": "decomposition_guided"}
            )
        
        try:
            # Ensure weights are calculated
            self.weight_calculator.calculate_all_weights(decomposition)
            
            # Build prioritized component list
            components_list = self._build_prioritized_component_list(decomposition)
            
            # Build prompt
            prompt = self.DECOMPOSITION_PROMPT_TEMPLATE.format(
                problem_statement=problem_statement,
                main_goal=decomposition.main_goal,
                components_list=components_list
            )
            
            solution = self._call_llm(
                prompt=prompt,
                system_message=(
                    "You are a systematic problem-solving assistant. "
                    "Use the provided decomposition to solve problems step-by-step, "
                    "addressing each component in priority order."
                )
            )
            
            # Extract metadata about decomposition usage
            metadata = {
                "method": "decomposition_guided",
                "has_decomposition": True,
                "num_components": len(decomposition.sub_components),
                "components_used": list(decomposition.sub_components.keys()),
                "main_goal": decomposition.main_goal,
                "decomposition_stats": self._extract_decomposition_stats(decomposition),
            }
            
            return SolverResult(
                solution=solution,
                success=True,
                metadata=metadata
            )
            
        except Exception as e:
            return SolverResult(
                solution="",
                success=False,
                error_message=str(e),
                metadata={
                    "method": "decomposition_guided",
                    "has_decomposition": True,
                }
            )
    
    def _build_prioritized_component_list(
        self,
        decomposition: ProblemDecomposition
    ) -> str:
        """Build formatted list of components in priority order.
        
        Args:
            decomposition: The problem decomposition
            
        Returns:
            Formatted string listing components with priorities
        """
        # Get components sorted by priority
        components_with_priority = [
            (comp_id, component, self.weight_calculator.get_priority_score(component))
            for comp_id, component in decomposition.sub_components.items()
        ]
        components_with_priority.sort(key=lambda x: x[2], reverse=True)
        
        # Format component list
        lines = []
        for idx, (comp_id, component, priority) in enumerate(components_with_priority, 1):
            deps_str = ", ".join(component.dependencies) if component.dependencies else "None"
            entities_str = ", ".join(component.entities) if component.entities else "None"
            
            line = (
                f"{idx}. Component: {component.goal}\n"
                f"   - Entities: {entities_str}\n"
                f"   - Dependencies: {deps_str}\n"
                f"   - Difficulty: {component.difficulty:.2f}\n"
                f"   - Failure Impact: {component.failure_impact:.2f}\n"
                f"   - Priority Score: {priority:.2f}"
            )
            lines.append(line)
        
        return "\n\n".join(lines)
    
    def _extract_decomposition_stats(
        self,
        decomposition: ProblemDecomposition
    ) -> Dict[str, Any]:
        """Extract statistics about the decomposition.
        
        Args:
            decomposition: The problem decomposition
            
        Returns:
            Dictionary with decomposition statistics
        """
        if not decomposition.sub_components:
            return {}
        
        difficulties = [c.difficulty for c in decomposition.sub_components.values()]
        impacts = [c.failure_impact for c in decomposition.sub_components.values()]
        orders = [c.dependency_order for c in decomposition.sub_components.values()]
        
        return {
            "avg_difficulty": sum(difficulties) / len(difficulties),
            "avg_impact": sum(impacts) / len(impacts),
            "max_dependency_order": max(orders) if orders else 0,
            "num_components": len(decomposition.sub_components),
            "num_root_components": sum(1 for c in decomposition.sub_components.values() if not c.dependencies),
            "num_leaf_components": sum(1 for c in decomposition.sub_components.values() if len(c.dependencies) > 0),
        }
