"""Single domain evaluation script"""

import json
import sys
import os
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Handle both script and module imports
try:
    from .cross_domain_eval import CrossDomainEvaluator
    from ..config import get_domain_config
except ImportError:
    # Running as script
    from experiments.cross_domain_eval import CrossDomainEvaluator
    from pipe_eval_prototype.config import get_domain_config


class SingleDomainEvaluator:
    """Evaluate a single domain in detail"""
    
    def __init__(
        self,
        domain_name: str,
        llm_config=None,
        output_dir: str = "data/results",
        num_problems: int = 20
    ):
        """Initialize single domain evaluator.
        
        Args:
            domain_name: Name of domain to evaluate
            llm_config: LLM configuration
            output_dir: Output directory
            num_problems: Number of problems to evaluate
        """
        self.domain_name = domain_name
        self.domain_config = get_domain_config(domain_name)
        self.evaluator = CrossDomainEvaluator(
            llm_config=llm_config,
            output_dir=output_dir,
            num_problems_per_domain=num_problems
        )
    
    def evaluate(self, task_name: Optional[str] = None) -> dict:
        """Evaluate the domain.
        
        Args:
            task_name: Specific task to evaluate (uses first task if None)
            
        Returns:
            Evaluation results
        """
        task_name = task_name or self.domain_config.reasoning_gym_tasks[0]
        
        return self.evaluator.evaluate_domain(
            domain_name=self.domain_name,
            task_name=task_name,
            num_problems=self.evaluator.num_problems_per_domain
        )


def main():
    """Run single domain evaluation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Single domain evaluation")
    parser.add_argument("domain", help="Domain to evaluate (arithmetic, games, logic)")
    parser.add_argument("--task", help="Specific task name", default=None)
    parser.add_argument("--num-problems", type=int, default=20, help="Number of problems")
    parser.add_argument("--output-dir", default="data/results", help="Output directory")
    
    args = parser.parse_args()
    
    evaluator = SingleDomainEvaluator(
        domain_name=args.domain,
        output_dir=args.output_dir,
        num_problems=args.num_problems
    )
    
    results = evaluator.evaluate(task_name=args.task)
    
    print("\n" + "="*80)
    print(f"Domain Evaluation Complete: {args.domain}")
    print("="*80)
    print(json.dumps(results.get("comparison", {}), indent=2))


if __name__ == "__main__":
    main()
