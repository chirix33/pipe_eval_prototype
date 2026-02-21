"""Manual test script that doesn't require OpenAI API - for testing structure"""

from decomposition import ProblemDecomposition, SubComponent
from weights import WeightCalculator
from visualizer import MermaidVisualizer


def test_manual_decomposition():
    """Test the system with manually created decomposition"""
    
    print("=" * 80)
    print("PIPE-EVAL Prototype: Manual Test (No LLM Required)")
    print("=" * 80)
    
    # Create a manual decomposition for "cook rice with rice cooker"
    decomposition = ProblemDecomposition(
        problem_statement="I want to cook rice with a rice cooker",
        main_goal="cook rice successfully"
    )
    
    # Add sub-components manually
    comp0 = SubComponent(
        component_id="comp_0",
        goal="having rice",
        entities=["rice"],
        dependencies=[]
    )
    
    comp1 = SubComponent(
        component_id="comp_1",
        goal="having water",
        entities=["water"],
        dependencies=[]
    )
    
    comp2 = SubComponent(
        component_id="comp_2",
        goal="having rice cooker",
        entities=["rice cooker"],
        dependencies=[]
    )
    
    comp3 = SubComponent(
        component_id="comp_3",
        goal="cooking rice",
        entities=["rice", "water", "rice cooker"],
        dependencies=["comp_0", "comp_1", "comp_2"]
    )
    
    decomposition.add_component(comp0)
    decomposition.add_component(comp1)
    decomposition.add_component(comp2)
    decomposition.add_component(comp3)
    
    print(f"\nProblem Statement: {decomposition.problem_statement}")
    print(f"Main Goal: {decomposition.main_goal}")
    print(f"Sub-components: {len(decomposition.sub_components)}\n")
    
    # Calculate weights
    weight_calculator = WeightCalculator()
    weight_calculator.calculate_all_weights(decomposition)
    
    # Display components
    print("Sub-Components:")
    print("-" * 80)
    for comp_id, component in decomposition.sub_components.items():
        priority = weight_calculator.get_priority_score(component)
        print(f"\n{comp_id}:")
        print(f"  Goal: {component.goal}")
        print(f"  Entities: {component.entities}")
        print(f"  Dependencies: {component.dependencies}")
        print(f"  Difficulty: {component.difficulty:.3f}")
        print(f"  Dependency Order: {component.dependency_order}")
        print(f"  Failure Impact: {component.failure_impact:.3f}")
        print(f"  Priority Score: {priority:.3f}")
    
    # Generate visualization
    print("\n" + "=" * 80)
    print("Mermaid DAG Visualization:")
    print("=" * 80)
    visualizer = MermaidVisualizer(weight_calculator)
    mermaid_diagram = visualizer.generate_with_styles(
        decomposition,
        show_weights=True,
        show_priority=True
    )
    print(mermaid_diagram)
    
    # Save to file
    output_file = "manual_test_decomposition.mmd"
    visualizer.save_to_file(decomposition, output_file, show_weights=True, show_priority=True)
    print(f"\n✓ Diagram saved to {output_file}")
    print("\nYou can view this diagram at: https://mermaid.live/")
    
    # Test topological sort
    print("\n" + "=" * 80)
    print("Dependency Order (Topological Sort):")
    print("=" * 80)
    sorted_order = decomposition.topological_sort()
    for i, comp_id in enumerate(sorted_order):
        component = decomposition.get_component(comp_id)
        print(f"{i}. {comp_id}: {component.goal} (order: {component.dependency_order})")


if __name__ == "__main__":
    test_manual_decomposition()
