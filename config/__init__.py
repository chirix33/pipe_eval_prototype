"""Configuration module for PIPE-EVAL prototype"""

from .llm_config import LLMConfig
from .domains import DomainConfig, get_domain_config, get_all_domains

__all__ = [
    "LLMConfig",
    "DomainConfig",
    "get_domain_config",
    "get_all_domains",
]
