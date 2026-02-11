# Multi-Model Orchestrator v2

Async parallel execution of multiple LLMs with model abstraction, timeout handling, and error recovery.

## Features

- **Async Parallel Execution**: All models run concurrently using asyncio
- **Model Interface Abstraction**: Protocol-based design for easy model additions
- **Timeout Handling**: Configurable per-model timeouts with graceful recovery
- **Error Recovery**: Automatic retries on transient failures
- **Execution Modes**: Simple, Medium, Complex, Architectural
- **Output Parsing**: Standardized code extraction from each model format

## Quick Start

### CLI Usage

```bash
# Basic execution
python orchestrator.py "Build a REST API endpoint"

# With options
python orchestrator.py "Build a REST API" --mode medium --verbose

# Specific models
python orchestrator.py "Create a React form" --models gemini claude-code

# JSON output
python orchestrator.py "Write a CLI tool" --json
```

### Python API

```python
import asyncio
from orchestrator import Orchestrator, ExecutionMode

async def main():
    orch = Orchestrator()
    
    result = await orch.run(
        task="Build a REST API endpoint",
        mode=ExecutionMode.MEDIUM,
        verbose=True
    )
    
    print(result.consensus_code)
    print(f"Time: {result.execution_time:.1f}s")

asyncio.run(main())
```

### Synchronous Usage

```python
from orchestrator import Orchestrator

orch = Orchestrator()
result = orch.run_sync("Build a REST API endpoint", verbose=True)
print(result.consensus_code)
```

## Execution Modes

| Mode | Models | Validators | Use Case |
|------|--------|------------|----------|
| **SIMPLE** | 1 primary | None | <50 LOC, quick tasks |
| **MEDIUM** | 2 primary | 1 | 50-500 LOC, standard tasks |
| **COMPLEX** | 2 primary | 2 | >500 LOC, critical code |
| **ARCHITECTURAL** | All 4 | None | System design, all perspectives |

## Model Runners

### Built-in Runners

| Runner | Model | CLI/API |
|--------|-------|---------|
| `ClaudeCodeRunner` | claude-code | `claude -p` |
| `CodexRunner` | codex | `codex -q` |
| `GeminiRunner` | gemini | `gemini -p` |
| `GrokRunner` | grok | REST API |

### Adding Custom Runners

```python
from orchestrator import BaseModelRunner

class MyModelRunner(BaseModelRunner):
    @property
    def name(self) -> str:
        return "my-model"
    
    async def _execute(self, prompt: str) -> Tuple[str, str]:
        # Your implementation
        code = await call_my_model(prompt)
        return code, code

# Register with orchestrator
orch = Orchestrator()
orch.runners["my-model"] = MyModelRunner()
```

## Task Routing

Tasks are automatically routed based on keywords:

| Category | Keywords | Primary Models | Validator |
|----------|----------|----------------|-----------|
| Frontend | react, component, ui, form | gemini, claude-code | codex |
| Backend | api, endpoint, service, database | claude-code, codex | gemini |
| DevOps | docker, kubernetes, ci/cd | codex, grok | claude-code |
| Scripts | script, automation, bash, cli | codex, gemini | claude-code |
| Data | data, pipeline, etl, sql | codex, claude-code | gemini |
| Architecture | architecture, design, scale | grok, claude-code | codex |

## Configuration

```python
orch = Orchestrator(
    grok_api_key="xai-...",      # Grok API key (or use GROK_API_KEY env)
    default_timeout=60.0,         # Per-model timeout in seconds
    max_retries=1                 # Retry attempts on failure
)
```

## Result Structure

```python
@dataclass
class OrchestratorResult:
    task: str                     # Original task
    mode: ExecutionMode           # Execution mode used
    category: str                 # Detected category
    consensus_code: str           # Merged best code
    explanation: str              # Merge explanation
    outputs: List[ModelOutput]    # Individual model outputs
    validation: Optional[Dict]    # Validation results
    execution_time: float         # Total execution time
    metadata: Dict[str, Any]      # Additional metadata
```

## Error Handling

### Timeout Handling

```python
# Model times out after 60s by default
result = await orch.run(task, timeout=120.0)  # Extend timeout

# Check for timeout failures
for output in result.outputs:
    if not output.success and "Timeout" in output.error:
        print(f"{output.model} timed out")
```

### Retry Logic

```python
# Configure retries
orch = Orchestrator(max_retries=2)

# Models are retried on transient failures
# Permanent failures (e.g., auth errors) are not retried
```

### Graceful Degradation

If some models fail, the orchestrator continues with successful outputs:

```python
result = await orch.run(task)

successful = [o for o in result.outputs if o.success]
failed = [o for o in result.outputs if not o.success]

print(f"Succeeded: {len(successful)}, Failed: {len(failed)}")
```

## Performance

### Parallel Execution

All models run concurrently:

```
Sequential: Model A (30s) → Model B (30s) → Model C (30s) = 90s
Parallel:   Model A ─┬─ Model B ─┬─ Model C = 30s (max)
                     └───────────┘
```

### Typical Execution Times

| Mode | Models | Typical Time |
|------|--------|--------------|
| SIMPLE | 1 | 15-30s |
| MEDIUM | 3 | 30-45s |
| COMPLEX | 4 | 45-60s |
| ARCHITECTURAL | 4 | 45-60s |

## Integration with Validator

The orchestrator automatically integrates with the validator module:

```python
result = await orch.run(task, verbose=True)

if result.validation:
    if result.validation["needs_human_review"]:
        print("Human review needed!")
        for reason in result.validation["review_reasons"]:
            print(f"  - {reason}")
```

## Migration from v1

### Key Changes

| v1 (orchestrate.py) | v2 (orchestrator.py) |
|---------------------|----------------------|
| `ThreadPoolExecutor` | `asyncio` |
| `MultiModelOrchestrator` | `Orchestrator` |
| `orchestrate()` | `run()` / `run_sync()` |
| Dict return | `OrchestratorResult` dataclass |
| Inline model code | `BaseModelRunner` abstraction |

### Migration Example

```python
# v1
from orchestrate import MultiModelOrchestrator
orch = MultiModelOrchestrator()
result = orch.orchestrate(task, verbose=True)
code = result["consensus_code"]

# v2
from orchestrator import Orchestrator
orch = Orchestrator()
result = orch.run_sync(task, verbose=True)
code = result.consensus_code
```

## Files

| File | Purpose |
|------|---------|
| `orchestrator.py` | Main orchestrator (v2) |
| `orchestrate.py` | Legacy orchestrator (v1) |
| `orchestrator-v2.md` | This documentation |
