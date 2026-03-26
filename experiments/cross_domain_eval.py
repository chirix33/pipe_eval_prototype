"""Cross-domain evaluation experiment"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import reasoning_gym

# Handle both script and module imports
try:
    from .. import (
        ProblemExtractor,
        WeightCalculator,
        EvaluationMetrics,
        HybridSolutionVerifier,
    )
    from ..config import LLMConfig, get_domain_config, get_all_domains
    from ..solvers import BaselineSolver, DecompositionSolver
except ImportError:
    # Running as script
    from pipe_eval_prototype import (
        ProblemExtractor,
        WeightCalculator,
        EvaluationMetrics,
        HybridSolutionVerifier,
    )
    from pipe_eval_prototype.config import LLMConfig, get_domain_config, get_all_domains
    from pipe_eval_prototype.solvers import BaselineSolver, DecompositionSolver


class CrossDomainEvaluator:
    """Evaluate baseline vs decomposition-guided solving across multiple domains"""
    
    def __init__(
        self,
        llm_config: Optional[LLMConfig] = None,
        output_dir: str = "data/results",
        num_problems_per_domain: int = 10
    ):
        """Initialize cross-domain evaluator.
        
        Args:
            llm_config: LLM configuration (uses default if not provided)
            output_dir: Directory to save results
            num_problems_per_domain: Number of problems to evaluate per domain
        """
        self.llm_config = llm_config or LLMConfig.from_env()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.num_problems_per_domain = num_problems_per_domain
        
        # Initialize components
        self.extractor = ProblemExtractor(api_key=self.llm_config.api_key, model=self.llm_config.model)
        self.weight_calculator = WeightCalculator()
        self.metrics = EvaluationMetrics()
        self.verifier = HybridSolutionVerifier(enable_component_verification=False)
        
        # Initialize solvers
        self.baseline_solver = BaselineSolver(self.llm_config)
        self.decomposition_solver = DecompositionSolver(self.llm_config, self.weight_calculator)
    
    def evaluate_domain(
        self,
        domain_name: str,
        task_name: str,
        num_problems: Optional[int] = None
    ) -> Dict:
        """Evaluate a single domain task.
        
        Args:
            domain_name: Name of the domain (e.g., "arithmetic")
            task_name: Name of reasoning-gym task (e.g., "leg_counting")
            num_problems: Number of problems to evaluate (uses default if None)
            
        Returns:
            Dictionary with evaluation results
        """
        num_problems = num_problems or self.num_problems_per_domain
        
        print(f"\n{'='*80}")
        print(f"Evaluating Domain: {domain_name} | Task: {task_name}")
        print(f"{'='*80}")
        
        # Load dataset
        try:
            dataset = reasoning_gym.create_dataset(task_name, size=num_problems, seed=42)
        except Exception as e:
            return {
                "domain": domain_name,
                "task": task_name,
                "error": f"Failed to load dataset: {str(e)}",
                "success": False
            }
        
        results = {
            "domain": domain_name,
            "task": task_name,
            "timestamp": datetime.now().isoformat(),
            "num_problems": num_problems,
            "baseline_results": [],
            "decomposition_results": [],
            "comparison": {},
            "success": True
        }
        
        baseline_scores = []
        decomposition_scores = []
        decomposition_qualities = []
        
        for i, problem_entry in enumerate(dataset):
            print(f"\nProblem {i+1}/{num_problems}:")
            print(f"  Q: {problem_entry['question'][:100]}...")
            
            # Extract decomposition
            try:
                decomposition = self.extractor.extract_to_decomposition(
                    problem_entry['question']
                )
                self.weight_calculator.calculate_all_weights(decomposition)
                
                # Evaluate decomposition quality (structural clarity)
                decomp_quality = self.metrics.evaluate_decomposition(decomposition)
                decomposition_qualities.append(decomp_quality)
                
            except Exception as e:
                print(f"  ✗ Decomposition extraction failed: {e}")
                continue
            
            # Solve with baseline
            print("  Solving with baseline...")
            baseline_result = self.baseline_solver.solve(
                problem_statement=problem_entry['question'],
                problem_entry=problem_entry
            )
            
            # Solve with decomposition
            print("  Solving with decomposition-guided...")
            decomp_result = self.decomposition_solver.solve(
                problem_statement=problem_entry['question'],
                problem_entry=problem_entry,
                decomposition=decomposition
            )
            
            # Verify solutions
            # Use final_answer if available (for high scores), otherwise fall back to full solution
            baseline_answer = baseline_result.final_answer if baseline_result.final_answer else baseline_result.solution
            decomp_answer = decomp_result.final_answer if decomp_result.final_answer else decomp_result.solution
            
            baseline_verification = self.verifier.verify(
                decomposition=decomposition,  # Use same decomposition for fair comparison
                solution=baseline_answer,
                problem_entry=problem_entry,
                dataset=dataset,
                use_component_verification=False
            )
            
            decomp_verification = self.verifier.verify(
                decomposition=decomposition,
                solution=decomp_answer,
                problem_entry=problem_entry,
                dataset=dataset,
                use_component_verification=False
            )
            
            baseline_score = baseline_verification['final_score']
            decomp_score = decomp_verification['final_score']
            
            baseline_scores.append(baseline_score)
            decomposition_scores.append(decomp_score)
            
            # Store results
            results["baseline_results"].append({
                "problem_index": i,
                "solution": baseline_result.solution,
                "final_answer": baseline_result.final_answer,
                "score": baseline_score,
                "success": baseline_result.success,
                "error": baseline_result.error_message,
            })
            
            results["decomposition_results"].append({
                "problem_index": i,
                "solution": decomp_result.solution,
                "final_answer": decomp_result.final_answer,
                "score": decomp_score,
                "success": decomp_result.success,
                "error": decomp_result.error_message,
                "decomposition_quality": decomp_quality,
                "decomposition_stats": decomp_result.metadata.get("decomposition_stats", {}),
            })
            
            print(f"  Baseline score: {baseline_score:.3f}")
            print(f"  Decomposition score: {decomp_score:.3f}")
            print(f"  Improvement: {decomp_score - baseline_score:+.3f}")
        
        # Calculate comparison metrics
        if baseline_scores and decomposition_scores:
            comparison = self.metrics.evaluate_solution_improvement(
                baseline_scores=baseline_scores,
                decomposition_scores=decomposition_scores
            )
            results["comparison"] = comparison
            
            # Calculate average decomposition quality (structural clarity)
            if decomposition_qualities:
                avg_coverage = sum(
                    q['coverage']['num_components'] for q in decomposition_qualities
                ) / len(decomposition_qualities)
                results["avg_decomposition_quality"] = {
                    "avg_components": avg_coverage,
                    "avg_coverage_metrics": {
                        k: sum(q['coverage'].get(k, 0) for q in decomposition_qualities) / len(decomposition_qualities)
                        for k in ['avg_entities_per_component', 'total_unique_entities']
                    }
                }
        
        return results
    
    def evaluate_all_domains(
        self,
        domains: Optional[List[str]] = None,
        problems_per_task: Optional[int] = None
    ) -> Dict:
        """Evaluate across all configured domains.
        
        Args:
            domains: List of domain names to evaluate (evaluates all if None)
            problems_per_task: Number of problems per task (uses default if None)
            
        Returns:
            Dictionary with all evaluation results
        """
        problems_per_task = problems_per_task or self.num_problems_per_domain
        
        all_domains = get_all_domains()
        domains_to_eval = domains or list(all_domains.keys())
        
        all_results = {
            "experiment_timestamp": datetime.now().isoformat(),
            "domains_evaluated": domains_to_eval,
            "problems_per_task": problems_per_task,
            "results": {}
        }
        
        for domain_name in domains_to_eval:
            domain_config = get_domain_config(domain_name)
            
            # Evaluate first task in domain (can be extended to all tasks)
            task_name = domain_config.reasoning_gym_tasks[0]
            
            domain_results = self.evaluate_domain(
                domain_name=domain_name,
                task_name=task_name,
                num_problems=problems_per_task
            )
            
            all_results["results"][domain_name] = domain_results
            
            # Save individual domain results
            domain_file = self.output_dir / f"{domain_name}_{task_name}_results.json"
            with open(domain_file, 'w') as f:
                json.dump(domain_results, f, indent=2, default=str)
            print(f"\n✓ Saved results to {domain_file}")
        
        # Save combined results
        combined_file = self.output_dir / "cross_domain_results.json"
        with open(combined_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"\n✓ Saved combined results to {combined_file}")
        
        return all_results


def main():
    """Run cross-domain evaluation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cross-domain evaluation")
    parser.add_argument("--domains", nargs="+", help="Domains to evaluate", default=None)
    parser.add_argument("--num-problems", type=int, default=10, help="Problems per domain")
    parser.add_argument("--output-dir", default="data/results", help="Output directory")
    
    args = parser.parse_args()
    
    evaluator = CrossDomainEvaluator(
        output_dir=args.output_dir,
        num_problems_per_domain=args.num_problems
    )
    
    results = evaluator.evaluate_all_domains(domains=args.domains)
    
    print("\n" + "="*80)
    print("Evaluation Complete!")
    print("="*80)
    print(f"Results saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
