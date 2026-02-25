"""LLM configuration settings"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMConfig:
    """Configuration for LLM interactions"""
    
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    temperature: float = 0.3  # Lower temperature for more deterministic extraction
    max_tokens: int = 2000
    timeout: int = 30  # Timeout in seconds
    
    def __post_init__(self):
        """Load API key from environment if not provided"""
        if self.api_key is None:
            self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
                "or pass api_key to LLMConfig."
            )
    
    @classmethod
    def from_env(cls) -> "LLMConfig":
        """Create config from environment variables"""
        return cls(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.3")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            timeout=int(os.getenv("LLM_TIMEOUT", "30")),
        )
