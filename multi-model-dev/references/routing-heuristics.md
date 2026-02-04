# Task Routing Heuristics

## Automatic Routing Logic

When a task arrives, analyze these dimensions to route to appropriate models:

### 1. **Task Category** (Primary Classifier)

#### Backend / API / Services
**Keywords:** API, endpoint, service, middleware, database, server, microservice, backend
**Route to:** Claude Code + Codex | Validate: Gemini
**Why:** CC for architecture, Codex for patterns, Gemini checks frontend integration

#### Frontend / React / Web UI
**Keywords:** component, React, Vue, React Native, frontend, UI, button, form, page, dashboard
**Route to:** Gemini + Claude Code | Validate: Codex
**Why:** Gemini for modern patterns, CC for structure, Codex for pragmatism

#### DevOps / Infrastructure / CI-CD
**Keywords:** Docker, Kubernetes, CI/CD, pipeline, terraform, ansible, deploy, infrastructure, orchestration
**Route to:** Codex + Grok | Validate: Claude Code
**Why:** Codex knows tools, Grok thinks edge cases, CC validates production-ready

#### Scripts / Automation / Tools
**Keywords:** script, automation, bash, Python, CLI, tool, workflow, schedule, cron
**Route to:** Codex + Gemini | Validate: Claude Code
**Why:** Codex for speed & patterns, Gemini for elegance, CC validates structure

#### Data Processing / Analytics
**Keywords:** data, pipeline, ETL, analytics, SQL, big data, batch, stream
**Route to:** Codex + Claude Code | Validate: Gemini
**Why:** Codex for pragmatic patterns, CC for structure, Gemini for new approaches

#### System Design / Architecture
**Keywords:** architecture, design, system, scale, performance, structure, pattern, topology
**Route to:** Grok + Claude Code | Validate: Codex
**Why:** Grok for creative edge cases, CC for production, Codex validates real-world

---

### 2. **Complexity Level** (Secondary Classifier)

#### Simple (< 50 LOC)
- Single-model routing sufficient
- Run: Primary model only (no consensus needed)
- Validator: Skip (overhead not worth it)

#### Medium (50-500 LOC)
- Dual-model routing (standard)
- Run: 2 primary models + 1 validator
- Consensus: Merge best parts

#### Complex (> 500 LOC)
- Dual-model routing + secondary validator
- Run: 2 primary + 2 validators (different angles)
- Consensus: Cross-validate all outputs, pick best, merge

#### Architectural (system-wide)
- All 4 models (no validator, all are workers)
- Run: All 4 in parallel
- Consensus: Score all, merge top 2-3 approaches

---

### 3. **Performance Sensitivity** (Tertiary Classifier)

#### Real-time / High-throughput (< 100ms latency)
- Emphasize: Codex + Grok (pragmatic, unconventional thinking for optimization)
- Validator: Claude Code (production readiness)
- Merge strategy: Prioritize lowest-latency implementation

#### Batch / Background (seconds-minutes OK)
- Standard routing (all models)
- Validator: Highest quality scorer
- Merge strategy: Best practices first

#### Not time-sensitive (hours+ OK)
- Standard routing (all models)
- Validator: Most thorough scorer
- Merge strategy: Most features + best documentation

---

### 4. **Language / Framework** (Routing Fine-tuning)

If task specifies language:

| Language | Recommendation |
|----------|---|
| **Python** | Codex + Claude Code → Validate: Gemini |
| **JavaScript/TypeScript** | Gemini + Claude Code → Validate: Codex |
| **Go / Rust** | Claude Code + Codex → Validate: Grok |
| **Terraform / HCL** | Grok + Codex → Validate: Claude Code |
| **SQL** | Codex + Claude Code → Validate: Gemini |
| **Bash / Shell** | Codex + Grok → Validate: Claude Code |

---

## Examples

### Example 1: "Build a React component to display user analytics dashboard"

1. **Category:** Frontend / React → Gemini + Claude Code
2. **Complexity:** Medium (150 LOC estimated) → Add validator
3. **Performance:** Not time-sensitive (normal priority)
4. **Framework:** React → Gemini primary (very strong here)

**Final routing:**
- Primary: Gemini, Claude Code
- Validator: Codex
- Consensus: Merge best UX + best structure + best real-world pragmatism

---

### Example 2: "Create a CI/CD pipeline for our Node.js app to Kubernetes"

1. **Category:** DevOps / Infrastructure → Codex + Grok
2. **Complexity:** Complex (500+ LOC, many moving parts) → Add secondary validator
3. **Performance:** Not time-sensitive
4. **Language:** YAML + Bash → Codex strong here

**Final routing:**
- Primary: Codex, Grok
- Validators: Claude Code (production-ready), Gemini (modern DevOps)
- Consensus: Cross-validate all 4, merge best practices + edge cases + production-ready

---

### Example 3: "Optimize database query that's taking 5 seconds"

1. **Category:** Backend / Data → Claude Code + Codex
2. **Complexity:** Simple/Medium (usually <100 LOC change)
3. **Performance:** Real-time sensitive (latency critical)
4. **Framework:** SQL/Database → Emphasize Codex + Grok

**Final routing:**
- Primary: Codex (knows optimization patterns), Grok (edge cases)
- Validator: Claude Code
- Emphasis: Speed + pragmatism over polish

---

### Example 4: "Design a multi-tenant SaaS architecture"

1. **Category:** System Design / Architecture → Grok + Claude Code
2. **Complexity:** Architectural (multi-faceted)
3. **Performance:** Not immediately time-sensitive (design phase)
4. **Scope:** System-wide → Use all models

**Final routing:**
- Workers: Grok, Claude Code, Codex, Gemini (all perspectives)
- No single validator; consensus from all 4
- Merge: Best from each angle, cross-validate assumptions

---

## Decision Tree

```
START: Analyze Task
│
├─ Category identified?
│  ├─ YES → Go to Complexity Check
│  └─ NO → Classify by keywords (see Category list above)
│
├─ Complexity estimated?
│  ├─ Simple (<50 LOC) → Route to 1 primary model, no validator
│  ├─ Medium (50-500 LOC) → Route to 2 primary + 1 validator
│  ├─ Complex (>500 LOC) → Route to 2 primary + 2 validators
│  └─ Architectural → Route to all 4 models
│
├─ Performance constraint?
│  ├─ YES (Real-time/High-throughput) → Emphasize Codex + Grok
│  └─ NO → Use standard routing
│
└─ OUTPUT: [Primary Models] → [Validators] → Consensus Merge

END: Return merged solution
```

---

## Customization

Edit this file to adjust routing based on observed quality patterns. For example:
- If Gemini consistently scores low for your task type, deprioritize it
- If Grok edge cases rarely matter for your domains, route less frequently
- Add custom categories if you have repeated task patterns
