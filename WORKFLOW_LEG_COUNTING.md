# Workflow: Leg-Counting Problem Through example_with_evaluation

This document walks through the **workflow implementation** for the problem statement:

> **"Your task is to count how many legs there are in total when given a list of animals. Now, how many legs are there in total if you have 3 dogs, 2 cats, 5 chickens?"**

Answer: 3×4 + 2×4 + 5×2 = **30** legs.

---

## Overview

`example_with_evaluation.py` does **not** solve the problem. It:

1. Loads **reasoning-gym** `leg_counting` problems (which may include this or similar questions).
2. **Decomposes** each problem via an LLM (extractor).
3. **Calculates weights** (difficulty, dependency order, failure impact) on the decomposition.
4. **Evaluates** decomposition quality (coverage, granularity, dependencies).
5. **Verifies** a given solution (here, the dataset’s correct answer is used as a stand-in).
6. **Optionally** runs expensive component-level verification (LLM to break solution into steps and score components).

The “solver” is external; the pipeline consumes a `solution` string (e.g. from an LLM or the ground truth).

---

## Step-by-step workflow

### 1. Load reasoning-gym dataset

```python
dataset = reasoning_gym.create_dataset('leg_counting', size=5, seed=42)
```

- **reasoning-gym** (`reasoning_gym.factory.create_dataset`): Instantiates `LegCountingDataset` with `LegCountingConfig(size=5, seed=42)`.
- Each **entry** from the dataset is a dict:
  - `question`: e.g. the task text + “how many legs… if you have 3 dogs, 2 cats, 5 chickens?”
  - `answer`: e.g. `"30"` (string).
  - `metadata`: e.g. `source_dataset`, `animals`, `total_legs`, etc.

With `seed=42`, the first few problems are fixed; one of them may match or resemble the 3 dogs / 2 cats / 5 chickens formulation (exact text depends on how the template is filled).

### 2. Initialize components

- **ProblemExtractor**: OpenAI client (e.g. `gpt-4o-mini`) for decomposition.
- **WeightCalculator**: Heuristics for difficulty, dependency order, failure impact.
- **MermaidVisualizer**: Renders decomposition as a Mermaid DAG (not used in this example script).
- **EvaluationMetrics**: Coverage, granularity, dependencies, solution improvement.
- **HybridSolutionVerifier**: Fast final-answer verification + optional component-level (expensive) verification.

### 3. Process problems (first 3)

For each of the first 3 dataset entries:

1. **Extract decomposition**  
   `extractor.extract_to_decomposition(problem_entry['question'])`  
   - Sends the problem text to the LLM with the extraction prompt (main goal + sub-components with goal, entities, dependencies).  
   - Parses JSON and builds a `ProblemDecomposition`: `main_goal`, `sub_components` (e.g. `comp_0`, `comp_1`, …), each with `goal`, `entities`, `dependencies`.  
   - Resolves dependency references to component IDs.

2. **Calculate weights**  
   `weight_calculator.calculate_all_weights(decomposition)`  
   - Sets `difficulty`, `dependency_order`, `failure_impact` per component (and thus priority).

Decompositions and problem entries are stored for the rest of the pipeline.

### 4. Evaluate decompositions

For each decomposition:

- **Coverage**: number of components, avg entities per component, total unique entities.
- **Granularity**: avg component size (e.g. goal length), max dependency depth.
- **Dependencies**: has_circular_deps, invalid_dependencies.

No ground truth is passed here, so dependency checks are structural only.

### 5. Verify solutions (fast method – Option B)

For each (decomposition, problem_entry):

- **Solution**: In this demo, `solution = problem_entry['answer']` (e.g. `"30"`).
- **Verifier**: `verifier.verify(..., use_component_verification=False)`:
  - Calls `dataset.score_answer(answer=solution, entry=problem_entry)`.
  - For **leg_counting**, the base `ProceduralDataset.score_answer` in reasoning-gym compares the given string to `entry["answer"]`; exact match → 1.0, substring → partial.
- **Output**: `final_score`, `is_correct` (e.g. `final_score >= 0.99`), `verification_method: 'final_answer'`.

So “verification” here is: run the dataset’s scorer on the provided solution and report the score.

### 6. Solution improvement metrics

- **baseline_scores**: In the example, all 1.0 (assumed correct baseline).
- **decomposition_scores**: The `final_score` from step 5 for each problem.
- `metrics.evaluate_solution_improvement(baseline_scores, decomposition_scores)` returns accuracy improvement (baseline vs decomposition accuracy, absolute/relative).

### 7. Component-level verification (expensive – Option A)

If the user answers **y** to “Use expensive component-level verification?”:

- Runs only on the **first** problem.
- **Verifier**: `verifier.verify(..., use_component_verification=True)`:
  1. **Final score**: Same as Option B: `dataset.score_answer(solution, problem_entry)`.
  2. **Intermediate steps**: One LLM call asking the model to break the solution into steps (component_goal, calculation, result) as JSON.
  3. **Component mapping**: For each sub-component in the decomposition, find which steps “match” (goal/entity overlap).
  4. **Component scores**: Per-component score (e.g. heuristic: numeric result → 1.0, or optional extra LLM check).
- **Output**: Same as fast path plus `component_scores` (e.g. `comp_0: 1.0`, `comp_1: 0.5`), `intermediate_steps` (list of step dicts), `verification_method: 'hybrid'`.

---

## Example run output

To run the script (with the expensive option):

```bash
# From repo root (research), with .venv and OPENAI_API_KEY set
.venv/Scripts/python pipe_eval_prototype/example_with_evaluation.py
# When prompted: "Use expensive component-level verification? (y/n):" type y
```

**Requirements:** `OPENAI_API_KEY` in the environment; `reasoning_gym` and `pipe_eval_prototype` importable (e.g. run from `research` with parent on `PYTHONPATH` or install both in `.venv`).

**Typical output shape:**

```
================================================================================
PIPE-EVAL Prototype: Evaluation Framework Demo
================================================================================

1. Loading reasoning-gym dataset...
✓ Loaded 5 problems

2. Initializing components...
✓ Components initialized

3. Processing problems...

   Problem 1:
   Q: Your task is to count how many legs there are in total when given a list of...
   ✓ Extracted 3 components

   Problem 2:
   ...
   ✓ Extracted 4 components

   Problem 3:
   ...
   ✓ Extracted 3 components

4. Evaluating decompositions...

   Decomposition 1:
   Coverage:
     - Components: 3
     - Avg entities/component: 2.33
     - Total unique entities: 5
   Granularity:
     - Avg component size: 28.50
     - Max dependency depth: 1
   Dependencies:
     - Has circular deps: False
     - Invalid deps: []

   (similar for Decomposition 2, 3)

5. Verifying solutions (fast method)...

   Problem 1:
     Final score: 1.000
     Is correct: True
     Method: final_answer

   Problem 2:
     Final score: 1.000
     Is correct: True
     Method: final_answer

   Problem 3:
     Final score: 1.000
     Is correct: True
     Method: final_answer

6. Calculating improvement metrics...

   Accuracy Improvement:
     Baseline: 1.000
     With decomposition: 1.000
     Absolute improvement: 0.000
     Relative improvement: 0.0%

7. Component-level verification (expensive - optional)...
   Note: This uses LLM calls and is expensive. Use sparingly.
   Use expensive component-level verification? (y/n): y

   Running component-level verification on first problem...

   Results:
     Final score: 1.000
     Method: hybrid

   Component-level scores:
     comp_0: Count legs for each animal type -> 1.000
     comp_1: Sum the leg counts -> 1.000
     comp_2: Report the total -> 1.000

   Extracted 3 intermediate steps

================================================================================
Summary:
================================================================================
✓ Processed 3 problems
✓ Evaluated decomposition quality
✓ Verified solutions (fast method)
✓ Calculated improvement metrics
...
```

- **Sections 1–4**: Dataset load; first 3 problems decomposed (LLM) and weighted; decomposition metrics (coverage, granularity, dependencies). Component count and numbers vary by LLM.
- **Section 5**: Fast verification: `dataset.score_answer(solution, entry)` → `final_score` (1.0 when solution is the ground-truth string).
- **Section 6**: With baseline and decomposition both using correct answers, improvement is 0%; in real use you’d compare a no-decomposition solver vs decomposition-guided solver.
- **Section 7 (with y)**: One extra LLM call to break the solution into steps; steps matched to decomposition components; per-component scores and step count printed. Exact goals and scores depend on the extractor and verifier LLM outputs.

---

## Where the “solving” happens

- **Inside this repo**: The pipeline **never** computes the answer (e.g. 30). It only:
  - Decomposes the problem (extractor),
  - Scores a **given** solution (verifier + reasoning-gym `score_answer`).
- **reasoning-gym**: Provides problems and **scoring**: `dataset.score_answer(answer, entry)` (for leg_counting, string match / substring vs `entry["answer"]`).
- **Real use**: You would replace `solution = problem_entry['answer']` with a call to your own solver/LLM that produces the answer string, then pass that into the same verification flow.

---

## Files involved

| Step              | Location |
|-------------------|----------|
| Dataset creation  | `reasoning_gym.factory.create_dataset`, `reasoning_gym.arithmetic.leg_counting` |
| Decomposition     | `pipe_eval_prototype.extractor` (LLM), `pipe_eval_prototype.decomposition` (structures) |
| Weights           | `pipe_eval_prototype.weights` |
| Decomposition eval| `pipe_eval_prototype.evaluation.metrics` |
| Verification      | `pipe_eval_prototype.evaluation.verifier` (FinalAnswerVerifier + optional ComponentLevelVerifier) |
| Score of answer   | `reasoning_gym.dataset.ProceduralDataset.score_answer` (leg_counting uses default) |
