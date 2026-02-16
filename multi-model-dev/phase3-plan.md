# Phase 3 — Dynamic Model Routing (Issue #14)

**Status:** In Progress  
**Depends on:** Phase 1 (model swap), Phase 2 (personality overlays)

---

## Goal

Automatically route Argus queries to the best model based on task type:
- **Claude** for technical precision, code, emotional nuance
- **Grok 3** for speed, creativity, humor, quick facts
- **Grok 4** for reasoning, analysis, multi-step problems

---

## Architecture

```
User Query
    ↓
[Router] ← routing.yaml (categories, keywords, patterns)
    ↓
Category Classification (creative? technical? emotional? factual?)
    ↓
Model Selection (with cost-awareness + sticky sessions)
    ↓
[OpenClaw] session_status(model=selected_model)
    ↓
[Personality Overlay] ← personality-overlays/{model}.yaml
    ↓
Argus Response (consistent identity, model-optimized)
```

---

## Components

### 1. `routing.yaml` — Configuration
Task categories with keyword/pattern signals and model preferences.
Includes override support (`/route grok`), confidence thresholds, 
cost-aware tie-breaking, and sticky sessions for multi-turn contexts.

### 2. `router.py` — Classification Engine
- Scores queries against all categories
- Picks highest-confidence match above threshold
- Falls back to Claude (default) when uncertain
- Supports sticky sessions (e.g., stays on Claude during emotional conversations)
- Logs all routing decisions for analytics
- Maintains state between turns

### 3. Integration with OpenClaw
The router outputs a model ID that can be passed to `session_status(model=...)` 
for live switching. In practice:
1. Router classifies incoming query
2. If model differs from current, switch via session_status
3. Personality overlay auto-applies based on active model
4. Response generated with model-specific tuning

---

## Key Features

### Cost-Aware Routing
When two categories score within 10% of each other, prefer the cheaper model.
Prevents unnecessary use of expensive models for borderline tasks.

### Sticky Sessions
Certain categories (emotional, reasoning) trigger "sticky" mode — the router
stays on the same model for N turns to maintain conversational continuity.
Avoids jarring mid-conversation model switches.

### User Override
`/route grok tell me about X` forces Grok regardless of classification.
Gives the user explicit control when they want a specific model's style.

### Routing Analytics
All decisions logged to `routing-log.jsonl`. Run `router.py --stats` to see
category/model distribution and average confidence over time.

---

## Testing

Built-in test suite with 18 test cases covering all categories:
```bash
python3 router.py --test
```

Individual query testing:
```bash
python3 router.py "tell me a joke" --verbose
python3 router.py "debug this Python script" --json
python3 router.py "pros and cons of PETG vs PLA"
```

---

## Deployment

### Current: Manual Integration
Router runs as a standalone classifier. Results inform model selection
but require manual `session_status()` calls.

### Future: OpenClaw Hook
Integrate router into OpenClaw's message pipeline so model selection
happens automatically before each agent turn. This would require:
- A pre-turn hook in OpenClaw's agent loop
- Router invoked on each incoming message
- Model switched transparently before response generation

---

## Open Questions

1. **Latency**: Does classification add noticeable delay? (Should be <50ms for keyword matching)
2. **Context window**: When switching models, does context transfer cleanly?
3. **Cron jobs**: Should cron jobs use routing? (e.g., Morning Briefing on Grok for personality)
4. **Multi-model turns**: Could a single response use multiple models? (e.g., Grok for the joke, Claude for the analysis)
