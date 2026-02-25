"""Simple script to run cross-domain evaluation"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipe_eval_prototype.config import LLMConfig
from pipe_eval_prototype.experiments import CrossDomainEvaluator


def main():
    """Run cross-domain evaluation"""
    
    print("=" * 80)
    print("PIPE-EVAL Cross-Domain Evaluation")
    print("=" * 80)
    print("\nThis will evaluate baseline vs decomposition-guided solving")
    print("across arithmetic, games, and logic domains.")
    print("\nNote: This requires OpenAI API key (set OPENAI_API_KEY)")
    print("=" * 80)
    
    # Get number of problems from user
    try:
        num_problems = int(input("\nNumber of problems per domain (default: 5): ") or "5")
    except ValueError:
        num_problems = 5
    
    # Initialize evaluator
    try:
        llm_config = LLMConfig.from_env()
        evaluator = CrossDomainEvaluator(
            llm_config=llm_config,
            output_dir="data/results",
            num_problems_per_domain=num_problems
        )
    except ValueError as e:
        print(f"\n✗ Configuration error: {e}")
        print("\nPlease set OPENAI_API_KEY environment variable.")
        return
    
    # Run evaluation
    print(f"\nStarting evaluation with {num_problems} problems per domain...")
    print("This may take several minutes depending on API response times.\n")
    
    try:
        results = evaluator.evaluate_all_domains()
        
        print("\n" + "=" * 80)
        print("Evaluation Complete!")
        print("=" * 80)
        print("\nResults saved to: data/results/")
        print("\nTo analyze results, run:")
        print("  python experiments/results_analyzer.py")
        
    except KeyboardInterrupt:
        print("\n\nEvaluation interrupted by user.")
    except Exception as e:
        print(f"\n✗ Evaluation failed: {e}")
        print("\nPlease check your API key and try again.")


if __name__ == "__main__":
    main()
