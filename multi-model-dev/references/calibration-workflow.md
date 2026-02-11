# Model Calibration Workflow

Guide for calibrating and updating model strength profiles based on observed performance.

## Overview

The calibration system helps you:
1. **Benchmark** models against standardized tasks
2. **Score** outputs using consistent criteria
3. **Track** performance over time
4. **Adjust** routing weights based on results
5. **Update** profiles when patterns emerge

## Quick Start

```bash
cd multi-model-dev/scripts

# List available benchmark tasks
python benchmark.py --list-tasks

# View current performance report
python benchmark.py --report

# Update routing weights from benchmark data
python benchmark.py --update-weights
```

## Calibration Process

### Step 1: Run Benchmark Tasks

Run the same task through all models:

```python
from benchmark import BENCHMARK_TASKS, BenchmarkTracker, BenchmarkResult, score_output
from orchestrate import MultiModelOrchestrator
import time

tracker = BenchmarkTracker()
orch = MultiModelOrchestrator()

# Pick a task
task = BENCHMARK_TASKS[0]  # backend-001: REST API Endpoint

# Run each model individually
for model_name in ["claude-code", "codex", "gemini", "grok"]:
    start = time.time()
    
    # Get model output (implement per-model run)
    output = run_single_model(model_name, task.prompt)
    
    execution_time = time.time() - start
    
    # Score the output
    scores, total = score_output(output, task)
    
    # Record result
    result = BenchmarkResult(
        task_id=task.id,
        model=model_name,
        output=output,
        execution_time=execution_time,
        timestamp=datetime.now().isoformat(),
        scores=scores,
        total_score=total
    )
    tracker.add_result(result)
```

### Step 2: Score Outputs

#### Auto-Scoring (Quick)
```python
scores, total = score_output(output, task)
```

Auto-scoring checks for:
- Code structure (functions, classes, imports)
- Expected elements from task definition
- Documentation (docstrings, comments, type hints)
- Error handling patterns

#### Manual Scoring (Accurate)
```python
scores, total = score_output_manual(output, task)
```

Manual scoring prompts for each criterion:
- **Correctness** (0-20): Does the code work?
- **Structure** (0-20): Is it well-organized?
- **Performance** (0-15): Is it efficient?
- **Best Practices** (0-20): Follows conventions?
- **Documentation** (0-15): Has comments/docs?
- **Testing** (0-10): Includes tests/error handling?

### Step 3: Analyze Results

```bash
# Generate report
python benchmark.py --report
```

Sample output:
```
# Model Benchmark Report

## Overall Rankings

| Rank | Model | Avg Score |
|------|-------|-----------|
| 1 | claude-code | 82.3 |
| 2 | codex | 78.5 |
| 3 | gemini | 75.2 |
| 4 | grok | 73.8 |

## Rankings by Category

### Backend
| Model | Avg Score |
|-------|-----------|
| claude-code | 88.0 |
| codex | 82.0 |
...
```

### Step 4: Update Routing Weights

```bash
python benchmark.py --update-weights
```

This:
1. Reads all benchmark results
2. Calculates average scores per model per category
3. Applies exponential moving average to existing weights
4. Saves updated weights to `routing_weights.json`

### Step 5: Review & Commit Changes

If significant patterns emerge:

1. Update `model-strengths.md` with new observations
2. Update `routing-heuristics.md` with adjusted recommendations
3. Commit changes to the repo

## Scoring Criteria Details

| Criterion | Weight | What to Look For |
|-----------|--------|------------------|
| **Correctness** | 20 | Valid syntax, runs without errors, correct logic |
| **Structure** | 20 | Modular design, clear organization, extensible |
| **Performance** | 15 | Efficient algorithms, no obvious bottlenecks |
| **Best Practices** | 20 | Idiomatic code, follows conventions, clean patterns |
| **Documentation** | 15 | Clear comments, docstrings, type hints, examples |
| **Testing** | 10 | Error handling, edge cases, test coverage hints |

### Score Interpretation

| Range | Meaning |
|-------|---------|
| 90-100 | Production-ready, use as-is |
| 80-89 | Very good, minor polish needed |
| 70-79 | Good, needs review before use |
| 60-69 | Acceptable, significant revision needed |
| <60 | Reference only, needs rework |

## Learning Loop

### Weekly Calibration
1. Run 2-3 benchmark tasks through all models
2. Score outputs (manual for accuracy)
3. Update weights if >10% change observed
4. Document surprising results

### After Major Updates
When a model is updated (new version), re-run all benchmarks:
1. Full benchmark suite through updated model
2. Compare to previous results
3. Update profiles if significant changes

### Tracking Surprises
Document when models perform unexpectedly:

```markdown
## Surprising Results Log

### 2026-02-11: Grok excels at backend validation
- Task: backend-002 (Repository Pattern)
- Expected: Claude Code primary
- Actual: Grok scored 92 (vs Claude Code 85)
- Reason: Grok caught more edge cases in error handling
- Action: Increase Grok weight for backend validation tasks
```

## File Locations

| File | Purpose |
|------|---------|
| `benchmark.py` | Benchmark runner and scoring |
| `benchmark_results.json` | Historical results (auto-created) |
| `routing_weights.json` | Current routing weights (auto-created) |
| `model-strengths.md` | Human-readable model profiles |
| `routing-heuristics.md` | Task routing decision logic |

## Advanced Usage

### Custom Benchmark Tasks

Add tasks to `BENCHMARK_TASKS` in `benchmark.py`:

```python
BenchmarkTask(
    id="custom-001",
    name="My Custom Task",
    category=TaskCategory.BACKEND,
    prompt="Your task prompt here...",
    expected_elements=["element1", "element2"],
    complexity="medium",
    language="python"
)
```

### Adjusting Learning Rate

The weight update uses exponential moving average:

```python
weights.update_from_benchmarks(tracker, learning_rate=0.1)
```

- **0.1** (default): Gradual adjustment, stable
- **0.2-0.3**: Faster adaptation, more volatile
- **0.05**: Very conservative, slow to change

### Exporting Results

```bash
# JSON export
python benchmark.py --export results.json

# Programmatic access
from benchmark import BenchmarkTracker
tracker = BenchmarkTracker()
for result in tracker.results:
    print(f"{result.model}: {result.total_score}")
```
