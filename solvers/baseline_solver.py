"""Baseline solver: Direct LLM problem-solving without decomposition"""

from typing import Any, Dict, Optional

from .base_solver import BaseSolver, SolverResult


class BaselineSolver(BaseSolver):
    """Solves problems directly without decomposition guidance.
    
    This is the baseline approach that treats problems as monolithic queries,
    representing the standard "black-box" LLM problem-solving approach.
    """
    
    BASELINE_PROMPT_TEMPLATE = """Solve the following problem. Provide your answer clearly and concisely.

Problem:
{problem_statement}

Answer:"""

    def solve(
        self,
        problem_statement: str,
        problem_entry: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SolverResult:
        """Solve problem directly without decomposition.
        
        Args:
            problem_statement: The problem to solve
            problem_entry: Optional problem entry (not used in baseline)
            **kwargs: Additional arguments (not used)
            
        Returns:
            SolverResult with solution
        """
        try:
            prompt = self.BASELINE_PROMPT_TEMPLATE.format(
                problem_statement=problem_statement
            )
            
            solution = self._call_llm(
                prompt=prompt,
                system_message="You are a problem-solving assistant. Provide clear, accurate solutions."
            )
            
            return SolverResult(
                solution=solution,
                success=True,
                metadata={
                    "method": "baseline",
                    "has_decomposition": False,
                    "components_used": [],
                }
            )
            
        except Exception as e:
            return SolverResult(
                solution="",
                success=False,
                error_message=str(e),
                metadata={
                    "method": "baseline",
                    "has_decomposition": False,
                }
            )
