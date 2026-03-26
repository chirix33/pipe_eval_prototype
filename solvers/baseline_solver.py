"""Baseline solver: Direct LLM problem-solving without decomposition"""

from typing import Any, Dict, Optional

from .base_solver import BaseSolver, SolverResult


class BaselineSolver(BaseSolver):
    """Solves problems directly without decomposition guidance.
    
    This is the baseline approach that treats problems as monolithic queries,
    representing the standard "black-box" LLM problem-solving approach.
    """
    
    BASELINE_PROMPT_TEMPLATE = """Solve the following problem. Provide your solution in JSON format.

Problem:
{problem_statement}

Respond with a JSON object containing:
- "reasoning": (string) Your step-by-step reasoning and work
- "final_answer": (string or number) Your final answer only, e.g. "100" for numeric answers

Output only valid JSON, no other text."""

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
            
            response = self._call_llm(
                prompt=prompt,
                system_message="You are a problem-solving assistant. Provide clear, accurate solutions in JSON format.",
                use_json_mode=True  # Request JSON mode for reliable parsing
            )
            
            # Parse JSON response to extract reasoning and final_answer
            reasoning, final_answer = self._parse_json_response(response)
            
            # Use reasoning as solution (for backward compatibility and logging)
            # If parsing failed, use full response as solution
            solution = reasoning if reasoning else response
            
            return SolverResult(
                solution=solution,
                success=True,
                final_answer=final_answer,
                metadata={
                    "method": "baseline",
                    "has_decomposition": False,
                    "components_used": [],
                    "json_parsed": final_answer is not None,
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
