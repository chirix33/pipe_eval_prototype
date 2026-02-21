"""Example: Using PIPE-EVAL prototype with reasoning-gym leg_counting task"""

import sys
import os

# Add parent directory to path to import reasoning_gym
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from pipe_eval_prototype import (
    ProblemExtractor,
    WeightCalculator,
    MermaidVisualizer
)


def main():
    """Demonstrate problem decomposition on reasoning-gym leg_counting task"""
    
    # Example problem statement from leg_counting task
    problem_statement = """Your task is to count how many legs there are in total when given a list of animals.

Now, how many legs are there in total if you have 3 dogs, 2 cats, 5 chickens?"""
    
    print("=" * 80)
    print("PIPE-EVAL Prototype: Problem Statement Weight Calculator")
    print("=" * 80)
    print(f"\nProblem Statement:\n{problem_statement}\n")
    
    # Initialize components
    print("Initializing components...")
    extractor = ProblemExtractor()
    weight_calculator = WeightCalculator()
    visualizer = MermaidVisualizer(weight_calculator)
    
    # Extract sub-components
    print("\nExtracting sub-components using LLM...")
    try:
        decomposition = extractor.extract_to_decomposition(problem_statement)
        print(f"✓ Extracted {len(decomposition.sub_components)} sub-components")
        print(f"✓ Main goal: {decomposition.main_goal}\n")
    except Exception as e:
        print(f"✗ Extraction failed: {e}")
        print("\nNote: Make sure you have:")
        print("  1. OpenAI API key set in environment (OPENAI_API_KEY)")
        print("  2. openai package installed (pip install openai)")
        return
    
    # Calculate weights
    print("Calculating weights...")
    weight_calculator.calculate_all_weights(decomposition)
    print("✓ Weights calculated\n")
    
    # Display sub-components
    print("Sub-Components:")
    print("-" * 80)
    for comp_id, component in decomposition.sub_components.items():
        print(f"\n{comp_id}:")
        print(f"  Goal: {component.goal}")
        print(f"  Entities: {component.entities}")
        print(f"  Dependencies: {component.dependencies}")
        print(f"  Difficulty: {component.difficulty:.3f}")
        print(f"  Dependency Order: {component.dependency_order}")
        print(f"  Failure Impact: {component.failure_impact:.3f}")
        priority = weight_calculator.get_priority_score(component)
        print(f"  Priority Score: {priority:.3f}")
    
    # Generate visualization
    print("\n" + "=" * 80)
    print("Mermaid DAG Visualization:")
    print("=" * 80)
    mermaid_diagram = visualizer.generate_with_styles(
        decomposition,
        show_weights=True,
        show_priority=True
    )
    print(mermaid_diagram)
    
    # Save to file
    output_file = "leg_counting_decomposition.mmd"
    visualizer.save_to_file(decomposition, output_file, show_weights=True, show_priority=True)
    print(f"\n✓ Diagram saved to {output_file}")
    print("\nYou can view this diagram at: https://mermaid.live/")
    
    # Summary statistics
    print("\n" + "=" * 80)
    print("Summary Statistics:")
    print("=" * 80)
    print(f"Total sub-components: {len(decomposition.sub_components)}")
    avg_difficulty = sum(c.difficulty for c in decomposition.sub_components.values()) / len(decomposition.sub_components)
    avg_impact = sum(c.failure_impact for c in decomposition.sub_components.values()) / len(decomposition.sub_components)
    print(f"Average difficulty: {avg_difficulty:.3f}")
    print(f"Average failure impact: {avg_impact:.3f}")
    
    # Identify critical components (high priority)
    critical_components = [
        (comp_id, component, weight_calculator.get_priority_score(component))
        for comp_id, component in decomposition.sub_components.items()
    ]
    critical_components.sort(key=lambda x: x[2], reverse=True)
    
    print(f"\nTop 3 Critical Components (by priority):")
    for i, (comp_id, component, priority) in enumerate(critical_components[:3], 1):
        print(f"  {i}. {comp_id}: {component.goal} (priority: {priority:.3f})")


if __name__ == "__main__":
    main()
