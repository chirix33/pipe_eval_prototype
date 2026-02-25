# Experiments and Evaluation

This directory contains scripts for running cross-domain evaluations comparing baseline LLM problem-solving against decomposition-guided approaches.

## Structure

```
experiments/
├── cross_domain_eval.py    # Main cross-domain evaluation script
├── single_domain_eval.py    # Single domain detailed evaluation
└── results_analyzer.py     # Analyze and compare results

solvers/
├── base_solver.py          # Abstract solver interface
├── baseline_solver.py      # Direct LLM solving (no decomposition)
└── decomposition_solver.py # Decomposition-guided solving

config/
├── llm_config.py          # LLM configuration (gpt-4o-mini)
└── domains.py             # Domain configurations
```

## Quick Start

### 1. Run Cross-Domain Evaluation

Evaluate all domains (arithmetic, games, logic):

```bash
python experiments/cross_domain_eval.py --num-problems 10
```

Evaluate specific domains:

```bash
python experiments/cross_domain_eval.py --domains arithmetic games --num-problems 20
```

### 2. Run Single Domain Evaluation

Evaluate a specific domain in detail:

```bash
python experiments/single_domain_eval.py arithmetic --num-problems 30
```

### 3. Analyze Results

Generate analysis report:

```bash
python experiments/results_analyzer.py
```

## Results Format

Results are saved as JSON files in `data/results/`:

- `{domain}_{task}_results.json` - Individual domain results
- `cross_domain_results.json` - Combined results
- `analysis_report.txt` - Human-readable report

## Key Metrics Tracked

### Accuracy Metrics
- Baseline accuracy (direct LLM solving)
- Decomposition-guided accuracy
- Absolute and relative improvement

### Structural Clarity Metrics
- Number of components extracted
- Average entities per component
- Dependency graph structure
- Component coverage

### Goal-Imbued Knowledge Metrics
- Main goal identification
- Component goal clarity
- Dependency relationships
- Priority ordering accuracy

## Configuration

### LLM Settings

Default: `gpt-4o-mini` (configured in `config/llm_config.py`)

To change:
```python
from config import LLMConfig

config = LLMConfig(
    model="gpt-4o-mini",
    temperature=0.3,
    max_tokens=2000
)
```

### Domain Configuration

Domains are configured in `config/domains.py`:

- **Arithmetic**: leg_counting, chain_sum, basic_arithmetic
- **Games**: countdown, sudoku, mini_sudoku
- **Logic**: knights_knaves, propositional_logic, zebra_puzzles

## Error Handling

If an LLM call fails:
1. Error message is logged in results
2. Problem is marked as failed
3. Evaluation continues with next problem
4. User can retry failed problems manually

## Research Goals

This evaluation framework supports three research goals:

1. **Accuracy Improvement**: Prove decomposition-guided solving improves accuracy
2. **Structural Clarity**: Demonstrate systematic decomposition provides clarity
3. **Goal-Imbued Knowledge**: Show that decomposition captures goal-oriented knowledge
