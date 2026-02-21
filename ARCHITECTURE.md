# Architecture Overview

## Design Decisions

### 1. LLM-Based Extraction
- **Why**: Flexible parsing of natural language problem statements
- **Model**: Uses OpenAI GPT-4o-mini (configurable)
- **Output**: Structured JSON with main_goal and sub_components
- **Fallback**: JSON extraction with regex if response is wrapped

### 2. Heuristic Weight Calculation
- **Why**: Fast, deterministic, no training data needed initially
- **Difficulty**: Based on entity count, verb complexity, dependency count
- **Dependency Order**: Topological sort of dependency graph
- **Failure Impact**: Based on dependent count and critical path analysis

### 3. In-Memory Storage
- **Why**: Prototype simplicity, fast access
- **Structure**: Python dicts and dataclasses
- **Future**: Can easily migrate to graph DB or vector store

### 4. Mermaid Visualization
- **Why**: Standard format, easy to embed/view
- **Features**: Color-coded by priority, shows weights, dependency edges
- **Viewing**: Can paste into mermaid.live or GitHub markdown

## Data Flow

```
Problem Statement
    ↓
[LLM Extractor]
    ↓
ProblemDecomposition (with SubComponents)
    ↓
[Weight Calculator]
    ↓
Updated SubComponents (with weights)
    ↓
[Mermaid Visualizer]
    ↓
Mermaid DAG Diagram
```

## Component Responsibilities

### `SubComponent`
- Represents a single 1-level deep goal
- Stores: goal, entities, dependencies, weights
- Validates: weights in range, non-empty fields

### `ProblemDecomposition`
- Container for all sub-components
- Manages: dependency graph, topological sorting
- Validates: dependency references exist

### `ProblemExtractor`
- LLM interface for parsing
- Converts: natural language → structured components
- Handles: API errors, JSON parsing

### `WeightCalculator`
- Heuristic-based weight computation
- Updates: difficulty, dependency_order, failure_impact
- Computes: combined priority score

### `MermaidVisualizer`
- Generates: Mermaid diagram code
- Styles: nodes by priority (red/yellow/green)
- Formats: node labels with weights

## Weight Calculation Details

### Difficulty Formula
```
difficulty = min(1.0, 
    entity_factor (0-0.4) +
    verb_complexity (0-0.3) +
    dependency_factor (0-0.3)
)
```

### Failure Impact Formula
```
impact = min(1.0,
    dependent_factor (0-0.6) +
    critical_path_factor (0-0.4)
)
```

### Priority Score Formula
```
priority = (difficulty * 0.3) + 
           (normalized_order * 0.2) + 
           (failure_impact * 0.5)
```

## Extension Points

### Adding New Weight Dimensions
1. Add field to `SubComponent` dataclass
2. Implement calculation method in `WeightCalculator`
3. Update `MermaidVisualizer` to display new weight

### Learning from Feedback
1. Store solution attempts and outcomes
2. Train model to predict weights from features
3. Replace heuristic methods with learned models

### Multi-Level Decomposition
1. Extend `SubComponent` to have nested components
2. Modify extractor to parse deeper hierarchies
3. Update visualizer to show nested structure

## Testing Strategy

1. **Manual Tests**: `test_manual.py` - No API required
2. **Integration Tests**: `example_leg_counting.py` - With reasoning-gym
3. **Unit Tests**: Test each component in isolation

## Future Enhancements

- [ ] Graph database backend (Neo4j, ArangoDB)
- [ ] Vector embeddings for semantic similarity
- [ ] Feedback loop for weight learning
- [ ] Multi-level decomposition support
- [ ] Export to other formats (GraphML, DOT)
- [ ] Interactive web visualization
