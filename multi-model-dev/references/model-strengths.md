# Model Strengths & Best Use Cases

## Claude Code

**Strengths:**
- Production-ready architecture
- Strong refactoring
- Testing & quality assurance
- Clear, well-documented code
- Error handling & edge cases
- Best for: Backend services, APIs, complex algorithms

**Weaknesses:**
- Can be conservative (slower to adopt new frameworks)
- Less experimental

**Best Routed To:**
- Backend/API design
- Middleware & services
- Data processing
- Architecture decisions
- Code review & validation

---

## Codex

**Strengths:**
- Rapid, pragmatic solutions
- API usage patterns (knows 100+ APIs well)
- Quick boilerplate generation
- Real-world patterns
- Good at "what actually works"
- Best for: Scripts, rapid prototypes, integrations

**Weaknesses:**
- Sometimes trades polish for speed
- May miss edge cases

**Best Routed To:**
- Scripts & automation
- API integrations
- Quick prototypes
- Build tooling
- Third-party library usage

---

## Gemini

**Strengths:**
- Modern frontend frameworks (React, Vue, Next.js)
- UX/accessibility patterns
- CSS & styling solutions
- Emerging tech adoption
- Component design
- Best for: Frontend, UI, modern web

**Weaknesses:**
- Less experienced with backend infrastructure
- Less familiar with older frameworks

**Best Routed To:**
- React/Vue components
- Frontend architecture
- Styling & CSS
- Web UX patterns
- Accessibility solutions

---

## Grok

**Strengths:**
- Unconventional thinking
- System design & edge cases
- DevOps & infrastructure
- Security considerations
- Novel solutions
- Best for: Architecture, DevOps, security, complex problems

**Weaknesses:**
- Sometimes too creative (needs validation)
- Can over-engineer

**Best Routed To:**
- System architecture
- DevOps & infrastructure
- Security design
- Scalability challenges
- Novel/edge case solutions

---

## Routing Decision Matrix

| Task | Primary | Secondary | Validator | Why |
|------|---------|-----------|-----------|-----|
| **REST API** | Claude Code | Codex | Gemini | CC for architecture, Codex for patterns, Gemini checks frontend integration |
| **React Component** | Gemini | Claude Code | Codex | Gemini for modern patterns, CC for structure, Codex for pragmatic check |
| **DevOps/CI-CD** | Codex | Grok | Claude Code | Codex for tools, Grok for edge cases, CC validates production-ready |
| **Data Pipeline** | Codex | Claude Code | Gemini | Codex for speed, CC for robustness, Gemini for new patterns |
| **Backend Service** | Claude Code | Codex | Grok | CC for production, Codex for speed, Grok for edge cases |
| **Frontend Architecture** | Gemini | Claude Code | Codex | Gemini for UX, CC for structure, Codex for real-world |
| **Script/Automation** | Codex | Gemini | Claude Code | Codex for speed, Gemini for elegance, CC validates |
| **System Design** | Grok | Claude Code | Codex | Grok for creative, CC for production, Codex validates |

---

## Quality Scoring

After all models output, score each on:

1. **Correctness** (20 pts) – Does it work? Is syntax valid?
2. **Structure** (20 pts) – Is it well-organized? Easy to extend?
3. **Performance** (15 pts) – Efficient? Avoids wasteful patterns?
4. **Best Practices** (20 pts) – Follows conventions? Uses idioms?
5. **Documentation** (15 pts) – Comments? Type hints? Examples?
6. **Testing** (10 pts) – Includes tests? Error handling?

**Scoring tiers:**
- **90-100:** Production-ready, use as-is
- **80-89:** Very good, minor polish needed
- **70-79:** Good, needs review before use
- **<70:** Reference only, needs rework

Validator model typically scores highest due to fresh perspective + access to all outputs to compare.

---

## Consensus Merging Strategy

1. **Extract all code blocks** from each model's output
2. **Group by component/function** (use validators grouping as reference)
3. **Compare implementations**:
   - Identical? Use as-is
   - Similar? Merge best parts
   - Different approaches? Score & pick highest, or document both
4. **Merge supporting code** (imports, types, tests)
5. **Add integrating glue** to connect all pieces
6. **Validate merged code** runs without errors

Result = 1 consensus codebase combining best of all 4 models.
