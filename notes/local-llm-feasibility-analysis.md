# Local LLM Feasibility Analysis

**Date:** March 10, 2026
**Hardware:** Mac Mini M4 (10-core CPU, 10-core GPU, 16GB unified memory)
**Current Setup:** OpenClaw agent (Claude Opus 4) + Grok 3 for cron jobs

---

## Executive Summary

Running a local LLM on the current Mac Mini M4 with 16GB unified memory is **not recommended as a primary replacement** for cloud-based models. The memory constraint is too tight to run models that match the quality needed for Argus's core tasks (tool orchestration, vision analysis, complex reasoning). However, a **hybrid approach** — using a small local model for simple classification tasks alongside cloud models — could offer modest cost savings if the workload justifies the setup.

---

## Hardware Assessment

| Spec | Value |
|------|-------|
| Chip | Apple M4 (T8132) |
| CPU Cores | 10 (4 performance + 6 efficiency) |
| GPU Cores | 10 |
| Neural Engine | 16-core |
| Unified Memory | 16GB |
| Memory Bandwidth | ~120 GB/s |
| Available for LLM | ~10-12GB (after macOS + services) |

### Current Memory Pressure

The Mac Mini is already running:
- macOS system (~4GB)
- OpenClaw gateway + Node.js
- Background services (Whisper, ffmpeg, various CLIs)
- Occasional browser automation (Playwright/Chromium)

Typical usage: **~15GB of 16GB in use**, leaving very little headroom.

### Why Unified Memory Matters

Apple Silicon's unified memory architecture means CPU and GPU share the same RAM pool. This is actually an advantage for LLM inference — the model doesn't need to be copied between CPU and GPU memory. But it also means there's no dedicated VRAM; everything competes for the same 16GB.

---

## What Models Fit in 16GB

Using **4-bit quantization** (Q4_K_M), which is the sweet spot for quality vs. size:

| Model | VRAM Needed | Quality Tier | Expected Speed | Fits? |
|-------|-------------|-------------|----------------|-------|
| Qwen 3 4B (Q4) | ~3GB | Basic | ~50+ tok/s | ✅ Comfortable |
| Llama 3.2 8B (Q4) | ~5GB | Good | ~30-40 tok/s | ✅ With headroom |
| Qwen 3 8B (Q4) | ~5GB | Good | ~30-40 tok/s | ✅ With headroom |
| Gemma 3 12B (Q4) | ~7GB | Solid | ~20-25 tok/s | ⚠️ Tight |
| Phi-4 14B (Q4) | ~8GB | Decent | ~15-20 tok/s | ⚠️ Very tight |
| Qwen 2.5 14B (Q4) | ~8GB | Good | ~10-15 tok/s | ⚠️ Borderline |
| Mistral Small 24B (Q3) | ~12GB | Strong | ~5-8 tok/s | ❌ Would swap |
| Llama 3.1 70B (Q4) | ~40GB | Excellent | N/A | ❌ Impossible |

**Note:** "Fits" assumes ~10GB available after system overhead. Models marked ⚠️ would cause memory pressure and potential swapping, degrading performance of both the LLM and other services.

---

## Benefits of Local LLM

### 1. Cost Elimination for Simple Tasks
Routine classification tasks (email triage, notification filtering, simple yes/no decisions) could run locally at zero marginal cost. Currently these consume cloud API tokens.

### 2. Zero Network Latency
Local inference has no round-trip delay. For simple queries, responses arrive in milliseconds rather than the 500ms-2s typical of cloud APIs.

### 3. Full Data Privacy
All data stays on-device. No text sent to external servers. Relevant for processing personal emails, messages, or documents.

### 4. No Rate Limits or API Outages
Cloud providers occasionally rate-limit or experience downtime. A local model has 100% uptime as long as the machine is running.

### 5. Offline Capability
If internet connectivity drops, a local model continues to function. Useful for basic assistant tasks during outages.

---

## Limitations and Tradeoffs

### 1. Memory Is the Hard Ceiling
At 16GB total, fitting a useful LLM alongside existing services is a constant balancing act. The M4's memory bandwidth (~120 GB/s) is good for its class, but the capacity just isn't there for larger models.

**Comparison:** The M4 Pro (48GB, $1,599) or M4 Max (64-128GB) are where local LLMs become genuinely practical.

### 2. Quality Gap vs. Cloud Models
The tasks that provide the most value — multi-step tool orchestration, long-context reasoning, nuanced code generation, personality consistency — require frontier-class models (100B+ parameters). An 8B local model would represent a significant quality regression:

- **Tool calling:** Small models frequently hallucinate function names, produce malformed JSON, and fail to chain multiple tool calls. This is critical for Argus's workflow (e.g., checking printer status → capturing snapshot → analyzing image → sending notification).
- **Context window:** Local 8B models typically support 8K-32K tokens. Cloud models offer 128K-200K tokens. Many of Argus's tasks involve long system prompts, memory files, and multi-turn conversations.
- **Reasoning depth:** Complex debugging, architecture decisions, and multi-factor analysis require larger models.

### 3. No Local Vision at 16GB
Vision-language models (LLaVA, Llama 3.2 Vision 11B) require ~8GB+ just for the model. This would consume most available memory and make the print monitoring camera analysis — one of Argus's most valuable features — infeasible locally.

### 4. Maintenance Overhead
Local models require:
- Model downloads and updates (multi-GB files)
- Quantization format management
- Prompt template compatibility
- Performance tuning per model
- Monitoring for OOM kills and memory pressure

### 5. No Improvement Over Time
Cloud models improve continuously (new releases, fine-tuning, expanded capabilities). A local model is static until manually updated.

---

## Hybrid Architecture (Recommended If Pursuing)

Rather than replacing cloud models entirely, use local models for specific low-complexity tasks:

```
┌──────────────────────────────────────────────┐
│              Task Router                      │
│                                              │
│  Complex tasks ──→ Cloud (Claude/Grok)       │
│  Simple tasks  ──→ Local (Ollama 8B)         │
└──────────────────────────────────────────────┘

Cloud Model (Claude Opus / Sonnet / Grok)     Local Model (Ollama + Qwen 3 8B)
─────────────────────────────────────────     ───────────────────────────────────
✓ Main conversations                          ✓ Email triage (spam/important/skip)
✓ Complex reasoning & analysis                ✓ Simple classification tasks
✓ Tool orchestration (multi-step)             ✓ Text summarization
✓ Vision / image analysis                     ✓ Notification filtering
✓ Code generation & review                    ✓ Embedding generation
✓ Morning briefings                           ✓ Basic Q&A without tools
✓ Print monitoring (camera + ML)              ✓ Log parsing
```

### Implementation Path (If Desired)
1. Install Ollama (`brew install ollama`)
2. Pull a lightweight model (`ollama pull qwen3:8b-q4_K_M`)
3. Run as a service (`ollama serve`)
4. Expose OpenAI-compatible API on localhost
5. Route specific cron tasks to local endpoint
6. Monitor memory pressure and quality

### Estimated Savings
- **Current cron costs:** ~$5-15/month (print monitoring, package tracking, price tracking, email checks)
- **Potential local offload:** ~$3-8/month of those tasks could use a local model
- **Net savings after electricity:** ~$2-6/month
- **Setup time:** 2-4 hours

---

## Cost Comparison

| Approach | Monthly Cost | Quality | Maintenance |
|----------|-------------|---------|-------------|
| Cloud only (current) | ~$30-60 (API usage) | Excellent | Low |
| Hybrid (cloud + local 8B) | ~$25-55 | Excellent + adequate | Medium |
| Local only (8B) | ~$3 (electricity) | Poor for complex tasks | High |
| Local only (requires 48GB+ Mac) | ~$3 (electricity) | Good with 32B+ model | High |

---

## Recommendation

### For Current Hardware (16GB M4)
**Stay with cloud models.** The cost savings (~$2-6/month) don't justify the memory pressure, quality tradeoffs, and maintenance overhead on a 16GB machine. The existing Grok 3 strategy for cost-sensitive cron jobs is already a good optimization.

### For Future Consideration
If local LLM capability becomes a priority, the upgrade path would be:
- **M4 Pro Mac Mini (48GB)** — ~$1,599 — Can run 32B models comfortably alongside all services
- **M4 Pro Mac Mini (64GB)** — ~$1,999 — Can run 70B quantized models, true cloud-quality replacement for many tasks
- **Mac Studio M4 Ultra (192GB)** — ~$5,999+ — Can run full 405B Llama or multiple models simultaneously

At 48GB+, the calculus changes significantly. A Qwen 3 32B or Llama 3.1 70B (Q4) running locally would handle most of Argus's non-vision tasks at near-cloud quality, and the $30-60/month API savings would pay for the hardware upgrade within 2-3 years.

---

## Tools & Frameworks Reference

| Tool | Description | Best For |
|------|-------------|----------|
| **Ollama** | Easy model management, OpenAI-compatible API | Quick setup, serving |
| **MLX / mlx-lm** | Apple's ML framework, optimized for Apple Silicon | Maximum M-chip performance |
| **LM Studio** | GUI app for local models | Experimentation, testing |
| **llama.cpp** | Low-level C++ inference | Maximum control, performance tuning |
| **vLLM** | High-throughput serving | Multi-user scenarios |

---

*Analysis by Argus • March 2026*
