"""PIPE-EVAL Prototype: Problem Statement Weight Calculator Artifact

This prototype implements a problem decomposition and weight calculation system
for analyzing problem statements and identifying critical sub-components.
"""

from .decomposition import ProblemDecomposition, SubComponent
from .extractor import ProblemExtractor
from .weights import WeightCalculator
from .visualizer import MermaidVisualizer
from .evaluation import (
    EvaluationMetrics,
    DecompositionCoverageMetrics,
    WeightAccuracyMetrics,
    SolutionImprovementMetrics,
    SolutionVerifier,
    FinalAnswerVerifier,
    ComponentLevelVerifier,
    HybridSolutionVerifier,
)
from .config import LLMConfig, DomainConfig, get_domain_config
from .solvers import BaseSolver, SolverResult, BaselineSolver, DecompositionSolver

__all__ = [
    "ProblemDecomposition",
    "SubComponent",
    "ProblemExtractor",
    "WeightCalculator",
    "MermaidVisualizer",
    "EvaluationMetrics",
    "DecompositionCoverageMetrics",
    "WeightAccuracyMetrics",
    "SolutionImprovementMetrics",
    "SolutionVerifier",
    "FinalAnswerVerifier",
    "ComponentLevelVerifier",
    "HybridSolutionVerifier",
    "LLMConfig",
    "DomainConfig",
    "get_domain_config",
    "BaseSolver",
    "SolverResult",
    "BaselineSolver",
    "DecompositionSolver",
]
