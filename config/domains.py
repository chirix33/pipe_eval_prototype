"""Domain configurations for reasoning-gym tasks"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class DomainConfig:
    """Configuration for a reasoning domain"""
    
    name: str
    reasoning_gym_tasks: List[str]  # List of task names from reasoning-gym
    description: str
    expected_component_count_range: tuple[int, int] = (2, 8)  # Expected min/max components
    
    def __post_init__(self):
        """Validate configuration"""
        if not self.reasoning_gym_tasks:
            raise ValueError(f"Domain {self.name} must have at least one task")
        if self.expected_component_count_range[0] >= self.expected_component_count_range[1]:
            raise ValueError("Invalid component count range")


# Domain configurations
DOMAINS = {
    "arithmetic": DomainConfig(
        name="arithmetic",
        reasoning_gym_tasks=["leg_counting", "chain_sum", "basic_arithmetic"],
        description="Sequential arithmetic operations",
        expected_component_count_range=(2, 6),
    ),
    "games": DomainConfig(
        name="games",
        reasoning_gym_tasks=["countdown", "sudoku", "mini_sudoku"],
        description="Constraint satisfaction and puzzle-solving",
        expected_component_count_range=(3, 8),
    ),
    "logic": DomainConfig(
        name="logic",
        reasoning_gym_tasks=["knights_knaves", "propositional_logic", "zebra_puzzles"],
        description="Logical reasoning and inference chains",
        expected_component_count_range=(3, 10),
    ),
}


def get_domain_config(domain_name: str) -> DomainConfig:
    """Get configuration for a domain"""
    if domain_name not in DOMAINS:
        raise ValueError(
            f"Unknown domain: {domain_name}. Available domains: {list(DOMAINS.keys())}"
        )
    return DOMAINS[domain_name]


def get_all_domains() -> Dict[str, DomainConfig]:
    """Get all domain configurations"""
    return DOMAINS.copy()
