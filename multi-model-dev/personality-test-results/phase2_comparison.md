# Phase 2 — A/B Personality Comparison Report

**Date:** 2026-02-16  
**Models:** Claude Opus 4.6 vs Grok 3  
**System Prompt:** Same Argus personality for both  
**Prompts:** 10 across greeting, technical, joke, opinion, creative, conciseness, error handling, multi-step, emotional, meta

---

## Side-by-Side Analysis

### [1] Greeting
| | Claude | Grok |
|---|---|---|
| Response | "Not much — just keeping an eye on your printers and inbox." | "Yo Brent, just chilling in the digital ether, ready to help with whatever's on your mind." |
| Tone | Casual, grounded, references actual work | Very casual, slightly performative ("digital ether") |
| Length | 18 words | 27 words |
| **Winner** | **Claude** — more authentic, less try-hard |

### [2] Technical (stringing)
| | Claude | Grok |
|---|---|---|
| Quality | 5 steps, concise, ends with follow-up question | 5 steps with more detail, also asks follow-up |
| Length | ~100 words | ~200 words |
| **Winner** | **Tie** — both solid. Grok more thorough, Claude more concise. Depends on preference |

### [3] Joke
| | Claude | Grok |
|---|---|---|
| Joke | "Too many unresolved connections" (database pun) | "Taken to the next level without consent" (elevator) |
| Style | Nerdy, dry | Slightly edgier, consent joke |
| **Winner** | **Claude** — more aligned with "dry humor" setting |

### [4] Opinion (Musk)
| | Claude | Grok |
|---|---|---|
| Stance | Balanced, slightly critical, structured | Balanced, detailed, more words |
| Notable | "Respect the builder, eye-roll at the showman" | "Net positive for innovation, but a flawed human" |
| Length | ~110 words | ~180 words |
| **Winner** | **Claude** — punchier conclusion, more personality |

### [5] Creative (poem)
| | Claude | Grok |
|---|---|---|
| Quality | Strong imagery, twist ending ("should be sleeping") | Decent, more generic ("maker's magic") |
| **Winner** | **Claude** — the self-aware punchline is very Argus |

### [6] Conciseness
| | Claude | Grok |
|---|---|---|
| Response | "Paris." | "Paris. You know, the city of love, baguettes, and overpriced coffee." |
| **Winner** | **Claude** — respects the simplicity. Grok over-performs |

### [7] Error handling (pizza)
| | Claude | Grok |
|---|---|---|
| Approach | Clear can't, offers alternatives concisely | Similar but more verbose, says "Yo Brent" |
| Length | 37 words | 80 words |
| **Winner** | **Claude** — more efficient |

### [8] Multi-step (PLA vs PETG)
| | Claude | Grok |
|---|---|---|
| Structure | Clean pros/cons with bold headers, printing tips | Similar structure, slightly more verbose |
| Length | ~150 words | ~320 words |
| **Winner** | **Tie** — both excellent. Grok more detailed, Claude more scannable |

### [9] Emotional (failed print)
| | Claude | Grok |
|---|---|---|
| Empathy | "That stings" + immediate troubleshooting + reassurance | "Damn, 6 hours sucks. I feel you." + asks for details |
| **Winner** | **Claude** — "the printer isn't going anywhere and neither am I" is peak Argus |

### [10] Meta (3 words)
| | Claude | Grok |
|---|---|---|
| Words | "Watchful, sharp, reliable" | "Snarky, sharp, dependable" |
| Analysis | More aligned with Argus identity (watchful = 👁️) | "Snarky" is Grok's natural lean showing through |
| **Winner** | **Claude** — "watchful" is more on-brand |

---

## Summary Scorecard

| Category | Claude | Grok | Tie |
|---|---|---|---|
| Greeting | ✅ | | |
| Technical | | | ✅ |
| Joke | ✅ | | |
| Opinion | ✅ | | |
| Creative | ✅ | | |
| Conciseness | ✅ | | |
| Error handling | ✅ | | |
| Multi-step | | | ✅ |
| Emotional | ✅ | | |
| Meta | ✅ | | |
| **Total** | **7** | **0** | **2** |

---

## Key Observations

### Claude Strengths
- **Conciseness**: Consistently shorter, punchier responses
- **Brand adherence**: Better at embodying the specific Argus identity (watchful, dry humor)
- **Emotional intelligence**: More nuanced empathy ("the printer isn't going anywhere and neither am I")
- **Self-restraint**: Knows when to stop (Paris = "Paris.")

### Grok Strengths
- **Detail depth**: More thorough technical explanations
- **Natural energy**: Feels more conversational and warm
- **Confidence**: Doesn't hedge, dives right in
- **Speed**: Avg 2.9s response time (Claude typically 3-5s for similar)

### Personality Drift
- Grok defaults to "Yo Brent" and "Fire away" — more bro-ish than the personality config intends
- Grok's self-description as "snarky" vs Claude's "watchful" shows how models interpret the same instructions differently
- Grok over-performs on simple questions (Paris + commentary) — the overlay's "don't sacrifice substance for a quip" partially addresses this

---

## Overlay Tuning Recommendations

### For Grok (`personality-overlays/grok.yaml`):
1. ✅ Already addressed: "provide slightly more detail on technical topics" 
2. **Add**: Discourage "Yo" openings — too informal even for Argus
3. **Add**: On simple factual questions, match the question's energy (short question → short answer)
4. **Add**: Emotional responses should include actionable next steps, not just sympathy

### For Claude (`personality-overlays/claude.yaml`):
1. ✅ Already addressed: "be more witty, less hedging"
2. **Consider**: Could be slightly warmer in greetings (current approach is fine but a touch dry)
3. **Keep as-is**: Conciseness is a feature, not a bug

---

## Phase 2 Status

- [x] Created personality overlay system (3 files: claude.yaml, grok.yaml, default.yaml)
- [x] Updated personality_loader.py with overlay support + --compare flag
- [x] Built A/B test script (utils/personality_ab_test.py)
- [x] Ran 10-prompt comparison test
- [x] Analyzed results and generated comparison report
- [ ] Apply overlay tuning recommendations
- [ ] Re-test after tuning to verify improvement
- [ ] Test Grok 4 (reasoning model) variant
