"""Base solver interface"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class SolverResult:
    """Result from a problem solver"""
    
    solution: str
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided"""
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "solution": self.solution,
            "success": self.success,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class BaseSolver(ABC):
    """Abstract base class for problem solvers"""
    
    def __init__(self, llm_config):
        """Initialize solver with LLM configuration"""
        self.llm_config = llm_config
    
    @abstractmethod
    def solve(
        self,
        problem_statement: str,
        problem_entry: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SolverResult:
        """
        Solve a problem statement.
        
        Args:
            problem_statement: The problem to solve
            problem_entry: Optional problem entry from reasoning-gym
            **kwargs: Additional solver-specific arguments
            
        Returns:
            SolverResult with solution and metadata
        """
        pass
    
    def _call_llm(self, prompt: str, system_message: Optional[str] = None) -> str:
        """Make LLM API call with error handling"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.llm_config.api_key)
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.llm_config.model,
                messages=messages,
                temperature=self.llm_config.temperature,
                max_tokens=self.llm_config.max_tokens,
                timeout=self.llm_config.timeout,
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            error_msg = f"LLM API error: {str(e)}"
            raise RuntimeError(error_msg) from e
