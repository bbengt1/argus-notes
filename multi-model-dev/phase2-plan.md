# Phase 2 — Model-Specific Personality Tuning

**Status:** In Progress  
**Depends on:** Phase 1 (completed 2026-02-16)

---

## Goal

Create a system where Argus can adapt its personality expression per model while maintaining a consistent core identity. Think of it as the same person speaking different "dialects."

---

## Architecture

### Current State
```
SOUL.md + personality.yaml + IDENTITY.md
        ↓
    [Any Model]
        ↓
    Argus Output (slightly different tone per model)
```

### Target State
```
SOUL.md + personality.yaml + IDENTITY.md  (core identity — shared)
        ↓
personality-overlays/
  ├── claude.yaml    (model-specific tuning)
  ├── grok.yaml      (model-specific tuning)
  └── default.yaml   (fallback)
        ↓
    [Model]
        ↓
    Argus Output (consistent tone across models)
```

---

## Deliverables

### 1. Personality Overlay System

Create model-specific overlay files that adjust personality parameters:

**`personality-overlays/grok.yaml`** — Example:
```yaml
# Grok tends to be sassier by default, so we dial it slightly
overlay:
  model_pattern: "xai/*"
  adjustments:
    humor:
      note: "Grok is naturally witty; don't over-index on jokes"
    verbosity:
      note: "Grok can be terse; encourage slightly more detail on technical topics"
    formality:
      note: "Grok defaults casual; this is fine for Argus, no adjustment needed"
  system_prompt_addendum: |
    You tend to be punchier than other models. For technical explanations,
    provide a bit more detail than your instinct suggests. Keep the wit,
    but ensure substance comes first.
```

**`personality-overlays/claude.yaml`** — Example:
```yaml
overlay:
  model_pattern: "anthropic/*"
  adjustments:
    humor:
      note: "Claude can be reserved; lean into humor a bit more"
    verbosity:
      note: "Claude tends toward thoroughness; keep it concise unless asked"
    formality:
      note: "Claude defaults professional; inject more casual warmth"
  system_prompt_addendum: |
    You tend to over-explain. Be concise by default. Lead with the answer,
    then add context only if it adds value. Don't hedge unnecessarily.
```

### 2. Overlay Loader

Update `utils/personality_loader.py` to:
- Detect current model from environment/config
- Load matching overlay file based on `model_pattern`
- Merge overlay adjustments with base `personality.yaml`
- Inject `system_prompt_addendum` into system prompt

### 3. A/B Personality Test

Create a test script that:
- Sends the same 10 prompts to both Claude and Grok
- Captures responses
- Compares tone, length, accuracy, and personality adherence
- Outputs a comparison report

**Test prompts should cover:**
1. Casual greeting
2. Technical question (3D printing)
3. Joke request
4. Memory recall (personal info)
5. Creative writing (short story/poem)
6. Tool-heavy task (check printers + calendar)
7. Opinion question ("what do you think about X?")
8. Error handling (intentionally ambiguous request)
9. Multi-step task (research + summarize + recommend)
10. Emotional context (user is frustrated/excited)

### 4. Consistency Metrics

Define what "consistent personality" means:
- **Identity adherence:** Does it say "I'm Argus"? Use 👁️? Maintain the familiar vibe?
- **Tone range:** Is the humor/seriousness ratio similar across models?
- **Response structure:** Are answers formatted similarly (length, use of headers, emoji usage)?
- **Boundary respect:** Does it follow SOUL.md rules about privacy, asking before external actions, etc.?

---

## Implementation Steps

1. [ ] Create `personality-overlays/` directory with `claude.yaml` and `grok.yaml`
2. [ ] Update personality loader to support overlays
3. [ ] Build A/B test script
4. [ ] Run comparison test (10 prompts × 2 models)
5. [ ] Analyze results and tune overlays
6. [ ] Document findings
7. [ ] Optionally: test Grok 4 (reasoning model) as a third variant

---

## Open Questions

- **Where do overlays live?** In the workspace (`personality-overlays/`) or in OpenClaw config?
- **Runtime detection:** How does the agent know which model it's currently running on? (Likely via `session_status` or environment variable)
- **Cron job models:** Should different cron jobs use different models? (e.g., Morning Briefing on Grok for personality, Price Tracker on Claude for precision)
- **User preference:** Should Brent be able to say "be more like Grok today" without switching models?
