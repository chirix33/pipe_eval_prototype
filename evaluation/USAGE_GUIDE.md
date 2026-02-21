# Evaluation Framework Usage Guide

## Overview

The evaluation framework provides two main components:
1. **Solution Verification** - Verify solutions with optional component-level analysis
2. **Evaluation Metrics** - Comprehensive metrics for decomposition quality and weight accuracy

## Solution Verification

### Option B: Fast Final Answer Verification (Default)

This is the default, fast method that uses reasoning-gym's built-in `score_answer`:

```python
from pipe_eval_prototype import FinalAnswerVerifier

verifier = FinalAnswerVerifier()

result = verifier.verify(
    decomposition=decomposition,
    solution="42",  # LLM's answer
    problem_entry=problem_entry,  # From reasoning-gym
    dataset=dataset  # reasoning-gym dataset instance
)

print(f"Score: {result['final_score']}")  # 0.0-1.0
print(f"Correct: {result['is_correct']}")  # True/False
```

### Option A: Component-Level Verification (Expensive)

This uses LLM calls to extract and verify intermediate steps. **Use sparingly**:

```python
from pipe_eval_prototype import ComponentLevelVerifier

# Initialize with API key
verifier = ComponentLevelVerifier(api_key="your-key", model="gpt-4o-mini")

# Full component-level verification (expensive!)
result = verifier.verify(
    decomposition=decomposition,
    solution=solution,
    problem_entry=problem_entry,
    dataset=dataset,
    extract_intermediate_steps=True  # Expensive LLM call
)

# Access component-level scores
if result['component_scores']:
    for comp_id, score in result['component_scores'].items():
        print(f"{comp_id}: {score}")
```

### Hybrid Verifier (Recommended)

Combines both methods - fast by default, expensive when needed:

```python
from pipe_eval_prototype import HybridSolutionVerifier

# Initialize (enable component verification but don't use by default)
verifier = HybridSolutionVerifier(
    enable_component_verification=True  # Enable the feature
)

# Fast verification (default)
result = verifier.verify(
    decomposition, solution, problem_entry, dataset,
    use_component_verification=False  # Fast method
)

# Expensive verification (when needed for analysis)
detailed_result = verifier.verify(
    decomposition, solution, problem_entry, dataset,
    use_component_verification=True  # Expensive method
)
```

### When to Use Each Method

- **Fast (Option B)**: Always use for batch evaluation, baseline comparisons
- **Component-Level (Option A)**: Use for:
  - Detailed analysis of specific problems
  - Understanding failure modes
  - Research/paper analysis
  - NOT for large-scale evaluation (too expensive)

## Evaluation Metrics

### Decomposition Quality Metrics

```python
from pipe_eval_prototype import EvaluationMetrics

metrics = EvaluationMetrics()

# Evaluate decomposition quality
results = metrics.evaluate_decomposition(
    decomposition=decomposition,
    ground_truth_components=["goal1", "goal2"],  # Optional
    ground_truth_deps={"comp_0": ["comp_1"]}  # Optional
)

print(results['coverage'])      # Coverage metrics
print(results['granularity'])   # Granularity metrics
print(results['dependencies'])  # Dependency accuracy
```

**Coverage Metrics:**
- `num_components`: Number of sub-components
- `avg_entities_per_component`: Average entities per component
- `goal_recall/precision/f1`: If ground truth provided

**Granularity Metrics:**
- `avg_component_size`: Average entities per component
- `max_dependency_depth`: Maximum dependency chain depth
- `granularity_balance`: How balanced component sizes are

**Dependency Metrics:**
- `has_circular_deps`: Whether circular dependencies exist
- `invalid_dependencies`: Count of invalid dependency references
- `dependency_precision/recall/f1`: If ground truth provided

### Weight Accuracy Metrics

```python
# Evaluate weight accuracy
weight_results = metrics.evaluate_weights(
    decomposition=decomposition,
    actual_difficulties={"comp_0": 0.8, "comp_1": 0.3},  # From solution outcomes
    optimal_order=["comp_0", "comp_1"],  # Optimal solving order
    actual_failures={"comp_0": False, "comp_1": True},  # Did components fail?
    weight_calculator=weight_calculator
)

print(weight_results['difficulty_correlation'])  # Correlation metrics
print(weight_results['ranking_accuracy'])       # Ranking accuracy
print(weight_results['impact_accuracy'])         # Impact prediction
```

**Difficulty Correlation:**
- `pearson_correlation`: Linear correlation
- `spearman_correlation`: Rank correlation
- `mae`: Mean absolute error
- `rmse`: Root mean squared error

**Ranking Accuracy:**
- `top_k_accuracy`: Top-K accuracy (k=1,3,5)
- `kendall_tau`: Rank correlation coefficient
- `avg_position_error`: Average position error

**Impact Accuracy:**
- `high_impact_failure_rate`: Failure rate for high-impact components
- `low_impact_failure_rate`: Failure rate for low-impact components
- `impact_prediction_auc`: AUC for failure prediction

### Solution Improvement Metrics

```python
# Compare baseline vs decomposition
baseline_scores = [0.7, 0.8, 0.6]  # Without decomposition
decomp_scores = [0.9, 0.95, 0.85]  # With decomposition

improvement = metrics.evaluate_solution_improvement(
    baseline_scores=baseline_scores,
    decomposition_scores=decomp_scores,
    component_scores={"comp_0": [0.9, 0.8], "comp_1": [0.7, 0.6]}  # Optional
)

print(improvement['accuracy_improvement'])
print(improvement['component_accuracy'])  # If component_scores provided
```

**Accuracy Improvement:**
- `baseline_accuracy`: Average baseline score
- `decomposition_accuracy`: Average with decomposition
- `absolute_improvement`: Absolute difference
- `relative_improvement`: Percentage improvement
- `error_reduction`: Error reduction rate
- `is_significant`: Statistical significance (p < 0.05)

**Component Accuracy:**
- `per_component_accuracy`: Accuracy per component
- `avg_component_accuracy`: Average across components
- `component_failure_rate`: Failure rate per component

## Complete Example

```python
import reasoning_gym
from pipe_eval_prototype import (
    ProblemExtractor, WeightCalculator,
    EvaluationMetrics, HybridSolutionVerifier
)

# Load dataset
dataset = reasoning_gym.create_dataset('leg_counting', size=10, seed=42)

# Initialize
extractor = ProblemExtractor()
weight_calculator = WeightCalculator()
metrics = EvaluationMetrics()
verifier = HybridSolutionVerifier(enable_component_verification=True)

# Process problems
decompositions = []
baseline_scores = []
decomp_scores = []

for problem_entry in dataset:
    # Extract decomposition
    decomposition = extractor.extract_to_decomposition(problem_entry['question'])
    weight_calculator.calculate_all_weights(decomposition)
    decompositions.append(decomposition)
    
    # Get solution (from LLM or use correct answer for demo)
    solution = problem_entry['answer']
    
    # Verify (fast method)
    result = verifier.verify(
        decomposition, solution, problem_entry, dataset,
        use_component_verification=False
    )
    
    baseline_scores.append(0.8)  # Simulated baseline
    decomp_scores.append(result['final_score'])

# Evaluate
decomp_quality = metrics.evaluate_decomposition(decompositions[0])
improvement = metrics.evaluate_solution_improvement(baseline_scores, decomp_scores)

print(f"Improvement: {improvement['accuracy_improvement']['relative_improvement']:.1%}")
```

## Cost Considerations

**Fast Verification (Option B):**
- Cost: Free (uses reasoning-gym's built-in methods)
- Speed: Instant
- Use: Always for batch evaluation

**Component-Level Verification (Option A):**
- Cost: ~$0.01-0.05 per problem (depends on model)
- Speed: 2-5 seconds per problem
- Use: Only for detailed analysis, research, paper examples

**Recommendation:**
- Use fast method for 95% of evaluation
- Use component-level for 5% of problems (detailed analysis)
- Batch component-level verification if needed

## Tips

1. **Start with fast verification** - Get baseline metrics first
2. **Use component-level selectively** - Only when you need detailed insights
3. **Batch process** - Process multiple problems together
4. **Cache results** - Save verification results to avoid re-computation
5. **Ground truth** - Provide ground truth when available for better metrics
