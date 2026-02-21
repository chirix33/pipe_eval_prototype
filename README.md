# PIPE-EVAL Prototype: Problem Statement Weight Calculator

A prototype implementation of a problem decomposition and weight calculation system for analyzing problem statements and identifying critical sub-components.

## Overview

This prototype implements the "Problem Statement Weight Calculator" artifact from the PIPE-EVAL framework. It:

1. **Extracts** sub-components from problem statements using LLM-based parsing
2. **Calculates** three weight dimensions: difficulty, dependency order, and failure impact
3. **Visualizes** the decomposition as a Mermaid DAG
4. **Prioritizes** components for monitoring and solving

## Architecture

### Core Components

- **`decomposition.py`**: Data structures (`SubComponent`, `ProblemDecomposition`)
- **`extractor.py`**: LLM-based problem statement parser
- **`weights.py`**: Heuristic weight calculators
- **`visualizer.py`**: Mermaid DAG generator
- **`evaluation/`**: Evaluation framework
  - **`verifier.py`**: Solution verification (fast Option B + optional expensive Option A)
  - **`metrics.py`**: Comprehensive evaluation metrics

### Sub-Component Structure

Each sub-component has:
- **Goal**: What needs to be achieved (e.g., "having rice", "count legs for dogs")
- **Entities**: Objects/resources involved (e.g., ["rice"], ["dogs", "3"])
- **Dependencies**: Other sub-components this depends on
- **Weights**:
  - `difficulty`: How hard is this to achieve? (0.0-1.0)
  - `dependency_order`: Execution order (0 = no deps, higher = later)
  - `failure_impact`: Impact if this fails (0.0-1.0)

## Installation

```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install openai numpy scipy scikit-learn
```

Set your OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

### Basic Example

```python
from pipe_eval_prototype import (
    ProblemExtractor,
    WeightCalculator,
    MermaidVisualizer
)

# Problem statement
problem = "I want to cook rice with a rice cooker"

# Extract sub-components
extractor = ProblemExtractor()
decomposition = extractor.extract_to_decomposition(problem)

# Calculate weights
weight_calculator = WeightCalculator()
weight_calculator.calculate_all_weights(decomposition)

# Visualize
visualizer = MermaidVisualizer(weight_calculator)
diagram = visualizer.generate_with_styles(decomposition)
print(diagram)
```

### With Reasoning-Gym

See `example_leg_counting.py` for a basic example using reasoning-gym tasks.

```bash
python example_leg_counting.py
```

### With Evaluation Framework

See `example_with_evaluation.py` for a complete example with evaluation metrics and solution verification.

```bash
python example_with_evaluation.py
```

**Key Features:**
- **Fast verification** (default): Uses reasoning-gym's built-in `score_answer` - no LLM calls
- **Component-level verification** (optional): Expensive but provides detailed component-level analysis
- **Comprehensive metrics**: Decomposition quality, weight accuracy, solution improvement

## Weight Calculation Heuristics

### Difficulty
- **Entity count**: More entities = higher difficulty
- **Goal verb complexity**: Complex verbs (calculate, verify) = higher difficulty
- **Dependency count**: More dependencies = higher difficulty

### Dependency Order
- Calculated via topological sort of dependency graph
- Leaf nodes (no dependencies) = order 0
- Increments for each dependency level

### Failure Impact
- **Dependent count**: More dependents = higher impact
- **Critical path**: Components on path to main goal = higher impact
- **Leaf components**: Lower impact (unless only component)

### Priority Score
Combined score: `(difficulty * 0.3) + (normalized_order * 0.2) + (failure_impact * 0.5)`

## Visualization

The visualizer generates Mermaid DAG diagrams with:
- Nodes colored by priority (red = high, yellow = medium, green = low)
- Edge directions showing dependencies
- Node labels showing goal, entities, and weights

View diagrams at: https://mermaid.live/

## Evaluation Framework

The evaluation framework provides:

### Solution Verification
- **Fast (Option B)**: Uses reasoning-gym's `score_answer` - instant, free
- **Component-Level (Option A)**: Extracts intermediate steps - expensive but detailed
- **Hybrid**: Combines both - fast by default, expensive when needed

### Evaluation Metrics
- **Decomposition Quality**: Coverage, granularity, dependency accuracy
- **Weight Accuracy**: Correlation with actual difficulty, ranking accuracy, impact prediction
- **Solution Improvement**: Accuracy improvement, component-level accuracy, statistical significance

See `evaluation/USAGE_GUIDE.md` for detailed usage instructions.

## Future Enhancements

- [x] Integration with reasoning-gym verification
- [ ] Learn weights from feedback (meta-learning)
- [ ] Support for multi-level decomposition
- [ ] Export to graph databases
- [ ] Interactive visualization

## License

This is a research prototype for the PIPE-EVAL project.
