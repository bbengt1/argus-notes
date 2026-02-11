# Validator Model Pattern

Cross-perspective review where a different model validates primary outputs.

## Why Validation Matters

When multiple models produce output for the same task, each has blind spots:
- **Claude Code**: May be overly conservative
- **Codex**: May trade polish for speed
- **Gemini**: May miss backend considerations
- **Grok**: May over-engineer

A **validator model** provides a fresh perspective:
- Sees all outputs for comparison
- Catches inconsistencies
- Identifies which parts to merge
- Flags issues for human review

## Validator Selection

| Primary Models | Validator | Why |
|---------------|-----------|-----|
| Claude Code + Codex | Gemini | Frontend/UX perspective |
| Gemini + Claude Code | Codex | Pragmatic real-world check |
| Codex + Grok | Claude Code | Production-ready validation |
| Grok + Claude Code | Codex | Real-world pragmatism |

### Selection Logic

1. Validator should **not** be one of the primary models
2. Validator should offer a **different perspective**
3. When in doubt, use **Claude Code** (most thorough)

## Validation Process

```
┌─────────────────────────────────────────────────────────────┐
│                       TASK                                  │
└─────────────────────────────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │   Model A   │ │   Model B   │ │   Model C   │
    │  (Primary)  │ │  (Primary)  │ │ (Validator) │
    └─────────────┘ └─────────────┘ └─────────────┘
           │               │               │
           ▼               ▼               │
    ┌─────────────────────────────┐        │
    │      Collect Outputs        │        │
    └─────────────────────────────┘        │
                    │                      │
                    ▼                      ▼
    ┌─────────────────────────────────────────┐
    │         VALIDATOR REVIEWS ALL           │
    │  - Scores each output                   │
    │  - Identifies strengths/weaknesses      │
    │  - Flags critical issues                │
    │  - Recommends merge strategy            │
    └─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
 ┌──────────────┐       ┌──────────────┐
 │ Confidence   │       │ Confidence   │
 │   >= 90%     │       │    < 90%     │
 └──────────────┘       └──────────────┘
        │                       │
        ▼                       ▼
 ┌──────────────┐       ┌──────────────┐
 │  Auto-merge  │       │ Human Review │
 └──────────────┘       └──────────────┘
```

## Usage

### Basic Validation

```python
from validator import Validator

validator = Validator()
result = validator.validate(
    task="Build a REST API endpoint",
    outputs={
        "claude-code": code_from_claude,
        "codex": code_from_codex
    },
    validator_model="gemini"  # Optional, auto-selected if omitted
)

print(f"Status: {result.status}")
print(f"Confidence: {result.confidence:.0%}")
print(f"Merge recommendation: {result.merge_recommendation}")
```

### With Orchestrator

```python
from orchestrate import MultiModelOrchestrator

orch = MultiModelOrchestrator()
result = orch.orchestrate("Build a REST API endpoint", verbose=True)

# Validation is included automatically
if result["validation"]:
    if result["validation"]["needs_human_review"]:
        print("Human review needed!")
        print(result["validation"]["review_reasons"])
```

### Custom Model Runner

```python
def my_model_runner(model: str, prompt: str) -> str:
    if model == "grok":
        return call_grok_api(prompt)
    elif model == "claude":
        return call_claude_api(prompt)
    # etc.

validator = Validator(model_runner=my_model_runner)
```

## Validation Response

The validator produces a structured analysis:

```json
{
  "analyses": {
    "claude-code": {
      "score": 85,
      "strengths": ["Well-structured", "Good error handling"],
      "weaknesses": ["Verbose"],
      "issues": [],
      "merge_worthy": true
    },
    "codex": {
      "score": 78,
      "strengths": ["Concise", "Pragmatic"],
      "weaknesses": ["Missing edge cases"],
      "issues": ["No input validation"],
      "merge_worthy": true
    }
  },
  "merge_recommendation": ["claude-code", "codex"],
  "merge_strategy": "combine",
  "concerns": ["Input validation missing in codex output"],
  "confidence": 0.92,
  "summary": "Both outputs acceptable. Recommend combining claude-code structure with codex pragmatism."
}
```

## Confidence Threshold

| Confidence | Action |
|------------|--------|
| >= 90% | Auto-merge allowed |
| 80-89% | Merge with caution |
| 70-79% | Human review recommended |
| < 70% | Human review required |

## Escalation Triggers

Human review is automatically triggered when:

1. **Low confidence** (< 90%)
2. **Critical issues** in any output
3. **Security-sensitive** keywords detected
4. **No merge-worthy** outputs
5. **Explicit concerns** flagged by validator

### Security Keywords

The following keywords trigger escalation:
- security, vulnerability, unsafe
- injection, authentication, authorization
- password, secret, key, token
- production, database, delete, drop

## Merge Strategies

| Strategy | When to Use |
|----------|-------------|
| `use_best` | One output clearly superior |
| `combine` | Multiple outputs have complementary strengths |
| `sequential` | Outputs build on each other |

## Human Review Format

When escalation is triggered:

```markdown
# Human Review Required

**Task:** Build a REST API endpoint
**Validator:** gemini
**Confidence:** 85%

## Why Review Needed
- Validator confidence 85% below threshold 90%
- codex has 1 critical issues

## Concerns
- Input validation missing in codex output

## Model Analyses

### claude-code (Score: 85)
**Strengths:** Well-structured, Good error handling
**Weaknesses:** Verbose

### codex (Score: 78)
**Strengths:** Concise, Pragmatic
**Weaknesses:** Missing edge cases
**⚠️ Issues:** No input validation

## Recommendation
**Strategy:** combine
**Merge order:** claude-code → codex

---
*Please review and approve/reject the merge.*
```

## Best Practices

1. **Always validate** when using 2+ models
2. **Trust the validator** for routine tasks
3. **Review escalations** promptly
4. **Update profiles** when validators consistently disagree
5. **Log validation results** for calibration

## Files

| File | Purpose |
|------|---------|
| `validator.py` | Core validation logic |
| `orchestrate.py` | Integration with orchestrator |
| `validator-pattern.md` | This documentation |
