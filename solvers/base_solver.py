"""Base solver interface"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple


@dataclass
class SolverResult:
    """Result from a problem solver"""
    
    solution: str
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None
    final_answer: Optional[str] = None  # Extracted final answer for scoring (if available)
    
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
            "final_answer": self.final_answer,
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
    
    def _call_llm(self, prompt: str, system_message: Optional[str] = None, use_json_mode: bool = False) -> str:
        """Make LLM API call with error handling
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            use_json_mode: If True, request JSON response format (only works with supported models)
            
        Returns:
            Response content as string
        """
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.llm_config.api_key)
            
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # Build request parameters
            request_params = {
                "model": self.llm_config.model,
                "messages": messages,
                "temperature": self.llm_config.temperature,
                "max_tokens": self.llm_config.max_tokens,
                "timeout": self.llm_config.timeout,
            }
            
            # Add JSON mode if requested (only for supported models)
            if use_json_mode:
                request_params["response_format"] = {"type": "json_object"}
            
            response = client.chat.completions.create(**request_params)
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            error_msg = f"LLM API error: {str(e)}"
            raise RuntimeError(error_msg) from e
    
    def _parse_json_response(self, response: str) -> Tuple[Optional[str], Optional[str]]:
        """Parse JSON response from LLM, extracting reasoning and final_answer.
        
        Handles cases where:
        - Response is pure JSON (from JSON mode)
        - Response is wrapped in markdown code fences (```json ... ```)
        - Response has extra text before/after JSON
        
        Args:
            response: Raw LLM response string
            
        Returns:
            Tuple of (reasoning, final_answer) where:
            - reasoning: The reasoning text (or None if not found)
            - final_answer: The final answer as a string (or None if not found)
        """
        if not response:
            return None, None
        
        json_str = None
        
        # First, try parsing the entire response as JSON (common with JSON mode)
        try:
            parsed = json.loads(response.strip())
            # Success! Use the parsed object directly
            json_str = response.strip()
        except json.JSONDecodeError:
            # Not pure JSON, try to extract JSON from markdown or mixed content
            # Try to extract JSON from markdown code fences
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find JSON object in the response (greedy match for nested objects)
                # Start from first { and try to find matching }
                brace_count = 0
                start_idx = response.find('{')
                if start_idx != -1:
                    for i in range(start_idx, len(response)):
                        if response[i] == '{':
                            brace_count += 1
                        elif response[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_str = response[start_idx:i+1]
                                break
        
        if json_str is None:
            # No JSON found, return original response as reasoning
            return response, None
        
        try:
            parsed = json.loads(json_str)
            
            # Extract reasoning (can be string or None)
            reasoning = parsed.get("reasoning")
            if reasoning is None:
                reasoning = parsed.get("reasoning_steps")  # Alternative key name
            if reasoning is None:
                # If no reasoning field, use the full response
                reasoning = response
            
            # Extract final_answer and convert to string
            final_answer = parsed.get("final_answer")
            if final_answer is None:
                final_answer = parsed.get("answer")  # Alternative key name
            
            if final_answer is not None:
                # Convert to string if it's a number or other type
                final_answer = str(final_answer).strip()
            
            return reasoning, final_answer
            
        except json.JSONDecodeError:
            # JSON parsing failed, return original response as reasoning
            return response, None
