"""Mermaid DAG visualization generator"""

from typing import Optional

from .decomposition import ProblemDecomposition, SubComponent
from .weights import WeightCalculator


class MermaidVisualizer:
    """Generates Mermaid DAG visualizations for problem decompositions."""
    
    def __init__(self, weight_calculator: Optional[WeightCalculator] = None):
        """Initialize the visualizer.
        
        Args:
            weight_calculator: Optional weight calculator for priority scores
        """
        self.weight_calculator = weight_calculator or WeightCalculator()
    
    def generate_dag(
        self, 
        decomposition: ProblemDecomposition,
        show_weights: bool = True,
        show_priority: bool = True,
        node_style: str = "rounded"
    ) -> str:
        """Generate a Mermaid DAG diagram for the problem decomposition.
        
        Args:
            decomposition: The problem decomposition to visualize
            show_weights: Whether to show weight values in node labels
            show_priority: Whether to color nodes by priority score
            node_style: Mermaid node style ("rounded", "rect", "circle", etc.)
            
        Returns:
            Mermaid diagram code as string
        """
        lines = ["graph TD"]
        
        # Calculate priority scores if needed
        priority_scores = {}
        if show_priority:
            for comp_id, component in decomposition.sub_components.items():
                priority_scores[comp_id] = self.weight_calculator.get_priority_score(component)
        
        # Create nodes
        for comp_id, component in decomposition.sub_components.items():
            node_label = self._format_node_label(component, show_weights, show_priority, priority_scores.get(comp_id))
            node_style_str = self._get_node_style(component, show_priority, priority_scores.get(comp_id))
            
            lines.append(f'    {comp_id}["{node_label}"]{node_style_str}')
        
        # Create edges (dependencies)
        for comp_id, component in decomposition.sub_components.items():
            for dep_id in component.dependencies:
                lines.append(f"    {dep_id} --> {comp_id}")
        
        return "\n".join(lines)
    
    def _format_node_label(
        self, 
        component: SubComponent, 
        show_weights: bool,
        show_priority: bool,
        priority_score: Optional[float]
    ) -> str:
        """Format node label with component information."""
        label_parts = [f"Goal: {component.goal}"]
        
        if component.entities:
            entities_str = ", ".join(component.entities[:3])  # Limit to first 3
            if len(component.entities) > 3:
                entities_str += "..."
            label_parts.append(f"Entities: {entities_str}")
        
        if show_weights:
            label_parts.append(f"Diff: {component.difficulty:.2f}")
            label_parts.append(f"Order: {component.dependency_order}")
            label_parts.append(f"Impact: {component.failure_impact:.2f}")
        
        if show_priority and priority_score is not None:
            label_parts.append(f"Priority: {priority_score:.2f}")
        
        return "\\n".join(label_parts)
    
    def _get_node_style(
        self, 
        component: SubComponent,
        show_priority: bool,
        priority_score: Optional[float]
    ) -> str:
        """Get Mermaid node style based on priority."""
        if not show_priority or priority_score is None:
            return ""
        
        # Color nodes by priority: red (high) -> yellow (medium) -> green (low)
        if priority_score >= 0.7:
            color = "#ff6b6b"  # Red for high priority
        elif priority_score >= 0.4:
            color = "#ffd93d"  # Yellow for medium priority
        else:
            color = "#6bcf7f"  # Green for low priority
        
        return f":::priority_{int(priority_score * 100)}"
    
    def generate_with_styles(
        self,
        decomposition: ProblemDecomposition,
        show_weights: bool = True,
        show_priority: bool = True
    ) -> str:
        """Generate Mermaid diagram with CSS styling for priority colors.
        
        Args:
            decomposition: The problem decomposition to visualize
            show_weights: Whether to show weight values
            show_priority: Whether to color by priority
            
        Returns:
            Complete Mermaid diagram with styles
        """
        diagram = self.generate_dag(decomposition, show_weights, show_priority)
        
        if show_priority:
            # Add CSS classes for priority coloring
            styles = ["    classDef priority_high fill:#ff6b6b,stroke:#c92a2a,stroke-width:2px"]
            styles.append("    classDef priority_med fill:#ffd93d,stroke:#f59f00,stroke-width:2px")
            styles.append("    classDef priority_low fill:#6bcf7f,stroke:#2b8a3e,stroke-width:2px")
            
            # Assign classes to nodes
            priority_scores = {}
            for comp_id, component in decomposition.sub_components.items():
                priority_score = self.weight_calculator.get_priority_score(component)
                priority_scores[comp_id] = priority_score
            
            for comp_id, score in priority_scores.items():
                if score >= 0.7:
                    styles.append(f"    class {comp_id} priority_high")
                elif score >= 0.4:
                    styles.append(f"    class {comp_id} priority_med")
                else:
                    styles.append(f"    class {comp_id} priority_low")
            
            return diagram + "\n" + "\n".join(styles)
        
        return diagram
    
    def save_to_file(self, decomposition: ProblemDecomposition, filepath: str, **kwargs) -> None:
        """Save Mermaid diagram to a file.
        
        Args:
            decomposition: The problem decomposition to visualize
            filepath: Path to save the file
            **kwargs: Additional arguments passed to generate_with_styles
        """
        diagram = self.generate_with_styles(decomposition, **kwargs)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(diagram)
