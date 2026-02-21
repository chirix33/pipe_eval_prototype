"""Example: Using PIPE-EVAL with evaluation metrics and solution verification"""

import sys
import os

# Add parent directory to path to import reasoning_gym
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import reasoning_gym
from pipe_eval_prototype import (
    ProblemExtractor,
    WeightCalculator,
    MermaidVisualizer,
    EvaluationMetrics,
    HybridSolutionVerifier,
)


def main():
    """Demonstrate evaluation framework with reasoning-gym leg_counting task"""
    
    print("=" * 80)
    print("PIPE-EVAL Prototype: Evaluation Framework Demo")
    print("=" * 80)
    
    # Create reasoning-gym dataset
    print("\n1. Loading reasoning-gym dataset...")
    dataset = reasoning_gym.create_dataset('leg_counting', size=5, seed=42)
    print(f"✓ Loaded {len(dataset)} problems")
    
    # Initialize components
    print("\n2. Initializing components...")
    extractor = ProblemExtractor()
    weight_calculator = WeightCalculator()
    visualizer = MermaidVisualizer(weight_calculator)
    metrics = EvaluationMetrics()
    
    # Hybrid verifier: fast by default, expensive component verification optional
    verifier = HybridSolutionVerifier(
        enable_component_verification=True  # Enable but don't use by default
    )
    print("✓ Components initialized")
    
    # Process a few problems
    decompositions = []
    problem_entries = []
    
    print("\n3. Processing problems...")
    for i, problem_entry in enumerate(dataset):
        if i >= 3:  # Process first 3 problems
            break
        
        print(f"\n   Problem {i+1}:")
        print(f"   Q: {problem_entry['question'][:80]}...")
        
        try:
            # Extract decomposition
            decomposition = extractor.extract_to_decomposition(problem_entry['question'])
            weight_calculator.calculate_all_weights(decomposition)
            
            decompositions.append(decomposition)
            problem_entries.append(problem_entry)
            
            print(f"   ✓ Extracted {len(decomposition.sub_components)} components")
            
        except Exception as e:
            print(f"   ✗ Extraction failed: {e}")
            continue
    
    if not decompositions:
        print("\n✗ No successful decompositions. Exiting.")
        return
    
    # Evaluate decompositions
    print("\n4. Evaluating decompositions...")
    for i, decomposition in enumerate(decompositions):
        print(f"\n   Decomposition {i+1}:")
        eval_results = metrics.evaluate_decomposition(decomposition)
        
        print(f"   Coverage:")
        print(f"     - Components: {eval_results['coverage']['num_components']}")
        print(f"     - Avg entities/component: {eval_results['coverage']['avg_entities_per_component']:.2f}")
        print(f"     - Total unique entities: {eval_results['coverage']['total_unique_entities']}")
        
        print(f"   Granularity:")
        print(f"     - Avg component size: {eval_results['granularity']['avg_component_size']:.2f}")
        print(f"     - Max dependency depth: {eval_results['granularity']['max_dependency_depth']}")
        
        print(f"   Dependencies:")
        print(f"     - Has circular deps: {eval_results['dependencies']['has_circular_deps']}")
        print(f"     - Invalid deps: {eval_results['dependencies']['invalid_dependencies']}")
    
    # Verify solutions (fast method - Option B)
    print("\n5. Verifying solutions (fast method)...")
    baseline_scores = []
    decomposition_scores = []
    
    # Simulate solutions (in real use, these would come from LLM)
    for i, (decomposition, problem_entry) in enumerate(zip(decompositions, problem_entries)):
        # Use correct answer as "solution" for demo
        solution = problem_entry['answer']
        
        # Verify with fast method (Option B)
        result = verifier.verify(
            decomposition,
            solution,
            problem_entry,
            dataset,
            use_component_verification=False  # Fast method
        )
        
        baseline_scores.append(1.0)  # Assume baseline gets correct answer
        decomposition_scores.append(result['final_score'])
        
        print(f"\n   Problem {i+1}:")
        print(f"     Final score: {result['final_score']:.3f}")
        print(f"     Is correct: {result['is_correct']}")
        print(f"     Method: {result['verification_method']}")
    
    # Calculate improvement metrics
    print("\n6. Calculating improvement metrics...")
    improvement = metrics.evaluate_solution_improvement(
        baseline_scores,
        decomposition_scores
    )
    
    print(f"\n   Accuracy Improvement:")
    print(f"     Baseline: {improvement['accuracy_improvement']['baseline_accuracy']:.3f}")
    print(f"     With decomposition: {improvement['accuracy_improvement']['decomposition_accuracy']:.3f}")
    print(f"     Absolute improvement: {improvement['accuracy_improvement']['absolute_improvement']:.3f}")
    print(f"     Relative improvement: {improvement['accuracy_improvement']['relative_improvement']:.1%}")
    
    # Demonstrate expensive component-level verification (Option A)
    print("\n7. Component-level verification (expensive - optional)...")
    print("   Note: This uses LLM calls and is expensive. Use sparingly.")
    
    use_expensive = input("   Use expensive component-level verification? (y/n): ").lower() == 'y'
    
    if use_expensive and decompositions:
        print("\n   Running component-level verification on first problem...")
        decomposition = decompositions[0]
        problem_entry = problem_entries[0]
        solution = problem_entry['answer']
        
        result = verifier.verify(
            decomposition,
            solution,
            problem_entry,
            dataset,
            use_component_verification=True  # Expensive method
        )
        
        print(f"\n   Results:")
        print(f"     Final score: {result['final_score']:.3f}")
        print(f"     Method: {result['verification_method']}")
        
        if result.get('component_scores'):
            print(f"\n   Component-level scores:")
            for comp_id, score in result['component_scores'].items():
                component = decomposition.get_component(comp_id)
                print(f"     {comp_id}: {component.goal} -> {score:.3f}")
        
        if result.get('intermediate_steps'):
            print(f"\n   Extracted {len(result['intermediate_steps'])} intermediate steps")
    else:
        print("   Skipped (use sparingly due to cost)")
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary:")
    print("=" * 80)
    print(f"✓ Processed {len(decompositions)} problems")
    print(f"✓ Evaluated decomposition quality")
    print(f"✓ Verified solutions (fast method)")
    print(f"✓ Calculated improvement metrics")
    print(f"\nNote: Component-level verification is available but expensive.")
    print("      Use HybridSolutionVerifier with use_component_verification=True when needed.")


if __name__ == "__main__":
    main()
