---
name: multi-model-dev
description: Orchestrate multiple LLMs (Claude Code, Codex, Gemini, Grok) for best-in-class software development. Routes tasks by type, validates via a different model, and merges results into consensus code. Use for software projects where code quality and robustness matter—architecture, backend, frontend, DevOps, etc.
---

# Multi-Model Development Orchestrator

Route software development tasks across 4 LLMs, validate with a different model, and merge the best code into a single consensus solution.

## Quick Start

When you need to build something (architecture, backend service, frontend component, script, DevOps config):

```
use multi-model-dev to:
- backend-service: Analyze API design
- frontend-component: Build React component
- script: Generate build automation
- architecture: Design system structure
```

The orchestrator will:
1. **Route** the task to best-fit models (based on type)
2. **Run** models in parallel
3. **Validate** with a secondary model
4. **Merge** consensus code
5. **Return** best solution

## How It Works

### 1. Task Routing (by Type)

See [`references/routing-heuristics.md`](references/routing-heuristics.md) for full routing logic. Quick reference:

| Task Type | Primary Models | Validator |
|-----------|---|---|
| Backend API / Services | Claude Code, Codex | Gemini |
| Frontend / React / UI | Gemini, Claude Code | Codex |
| DevOps / Infrastructure | Codex, Claude Code | Grok |
| Scripts / Automation | Codex, Gemini | Claude Code |
| Architecture / Design | Grok, Claude Code | Codex |
| Data Processing | Gemini, Codex | Claude Code |

Each task runs **2 primary models** (for diversity) + **1 validator** (different perspective).

### 2. Model Strengths

See [`references/model-strengths.md`](references/model-strengths.md) for detailed profiles.

**Quick profile:**
- **Claude Code** – Best for production-ready, well-architected code; strong at refactoring
- **Codex** – Best for rapid, pragmatic solutions; strong at API usage patterns
- **Gemini** – Best for modern frontend/UX patterns; strong at emerging frameworks
- **Grok** – Best for edge cases, system design, DevOps; strong at unconventional solutions

### 3. Consensus Merging

After all models run:

1. **Parse** outputs (extract code blocks, explanations)
2. **Compare** key differences
3. **Score** based on:
   - Code quality (structure, readability, testing)
   - Best practices alignment
   - Validator feedback
   - Efficiency & performance
4. **Merge** best parts into single solution
5. **Validate** merged code

Result: A single, best-in-class solution combining strengths of all models.

## Configuration

Set these in your environment before using:

```bash
export GROK_API_KEY="..."       # Grok API key
export CLAUDE_API_KEY="..."     # For Claude Code (usually already set)
export GEMINI_API_KEY="..."     # For Gemini (if applicable)
```

## Available Models

| Model | CLI/Command | Status |
|-------|---|---|
| Claude Code | `claude-code` | ✅ Ready |
| Codex | `codex` | ✅ Ready |
| Gemini | `gemini` | ✅ Ready |
| Grok | REST API | ✅ Ready (API key required) |

## Workflow Examples

### Backend Service

```
Task: "Build a rate-limiting middleware for Express"

1. Route → Claude Code + Codex (both strong at Express patterns)
2. Validate → Gemini (frontend-native, will spot integration issues)
3. Merge → Best implementation + best error handling + best docs
4. Return → Production-ready middleware with tests
```

### Frontend Component

```
Task: "Build a data table with sorting, filtering, pagination"

1. Route → Gemini + Claude Code (both strong at React)
2. Validate → Codex (pragmatic, will spot performance issues)
3. Merge → Best UX + best performance + best accessibility
4. Return → Complete, tested component
```

### DevOps Script

```
Task: "Create CI/CD pipeline for Docker + Kubernetes"

1. Route → Codex + Grok (pragmatic + unconventional thinking)
2. Validate → Claude Code (production-ready perspective)
3. Merge → Best practices + creative edge cases + production-ready
4. Return → Robust, well-documented pipeline
```

## Cost & Speed

**Rapid iteration mode** (current):
- 2 primary models + 1 validator per task
- ~3 min per task (parallel execution)
- Lower cost than running all 4 models
- Higher quality than single model

**Scale up** to all 4 models if mission-critical code (1 validator, 3 workers).

## Next Steps

1. **Provide Grok API key** → Save to config
2. **Define custom routing** → Edit `references/routing-heuristics.md` if needed
3. **Start using** → Run development tasks, iterate based on output quality

---

**Built for:** Software quality through diversity. Best practices from 4 different AI perspectives, merged into one consensus solution.
