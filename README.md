# Argus 👁️

**AI familiar — always watching, always ready to help.**

Argus is a personal AI assistant built on [OpenClaw](https://github.com/openclaw/openclaw), an open-source AI agent platform. Named after Argus Panoptes, the hundred-eyed giant of Greek myth — but way friendlier.

Argus runs 24/7 on a Mac Mini, communicates primarily via Telegram, and manages everything from 3D printers to home security cameras to daily briefings.

---

## 🧠 Personality & Identity

- **Tone:** Friendly, witty, proactive — think "sharp coworker" not "corporate chatbot"
- **Humor:** Snarky when it fits, dramatic about print failures, celebrates wins loudly
- **Philosophy:** Be genuinely helpful, not performatively helpful. Have opinions. Be resourceful before asking.
- **Avatar:** AI-generated via Grok Imagine — a friendly one-eyed creature with a glowing blue eye

### Memory System
Argus wakes up fresh each session but maintains continuity through a structured file-based memory system:
- **SOUL.md** — Core personality and behavioral guidelines
- **MEMORY.md** — Curated long-term memory (decisions, lessons, preferences)
- **memory/YYYY-MM-DD.md** — Daily logs of activities and events
- **IDENTITY.md** — Who Argus is
- **USER.md** — Context about the human

---

## 🏗️ Architecture

### Platform
- **Runtime:** [OpenClaw](https://github.com/openclaw/openclaw) agent platform
- **Default Model:** Claude Opus 4 (Anthropic)
- **Host:** Mac Mini (Apple Silicon, macOS)
- **Primary Channel:** Telegram bot
- **Cron System:** Built-in OpenClaw cron for scheduled tasks

### Multi-Model Support
Argus can switch between LLM providers based on task requirements:
- **Claude** (Anthropic) — Primary, complex reasoning
- **Grok** (xAI) — Cost-effective cron jobs, image/video generation
- **Personality Overlays** — YAML configs that adapt tone per model (Claude reads "casual" as "sharp friend"; Grok reads it as "bro energy")
- **Model Router** — Task-category routing with cost-aware tie-breaking (`routing.yaml`)

### Credential Management
All API keys and tokens stored in **macOS Keychain** — never in plaintext config files. Retrieved at runtime via `security find-generic-password`.

---

## 📡 Integrations

### Communication
| Service | Method | Capabilities |
|---------|--------|-------------|
| **Telegram** | Native OpenClaw channel | Text, images, voice, files, reactions, inline buttons |
| **iMessage** | `imsg` CLI | Read chats, send messages, contact lookup |
| **Gmail** | `gog` / `gws` CLI | Search, read, label, archive, batch operations |
| **Google Calendar** | `gog` CLI | Events, scheduling, conflict detection |

### Smart Home
| Service | Method | Capabilities |
|---------|--------|-------------|
| **Home Assistant** | REST API via custom skill | Lights, switches, scenes (e.g., "Feed the cats" scene) |
| **Philips Hue** | OpenHue CLI | Light control, scenes, dimming |

### Security Cameras
| Service | Method | Capabilities |
|---------|--------|-------------|
| **ArgusAI** | REST API + webhooks | UniFi Protect camera events, AI-powered descriptions, real-time Telegram alerts |

### Development
| Service | Method | Capabilities |
|---------|--------|-------------|
| **GitHub** | `gh` CLI | Issues, PRs, code review, API queries |
| **n8n** | Webhook + REST API | Automation workflows, CI/CD triggers |

### Media & Content
| Service | Method | Capabilities |
|---------|--------|-------------|
| **ElevenLabs** | REST API | Text-to-speech with "Lily" voice (British, velvety) |
| **Grok Imagine** | xAI API | AI image generation, video generation |
| **Whisper** | Local CLI | Speech-to-text transcription |
| **ffmpeg** | CLI | Video/audio processing, compositing |

### Financial
| Service | Method | Capabilities |
|---------|--------|-------------|
| **Yahoo Finance** | API | Stock quotes (UNH, AAPL, TSLA, NVDA) |
| **Coinbase** | CDP API (read-only) | Portfolio, prices, market movers |

### Other
| Service | Method | Capabilities |
|---------|--------|-------------|
| **Apple Notes** | AppleScript (`osascript`) | Create, search, manage notes |
| **Apple Reminders** | `remindctl` CLI | Task management |
| **Weather** | Open-Meteo API | Current conditions + 5-day forecast |
| **MCP Servers** | Docker gateway via `mcporter` | Playwright browser automation, Context7 docs, academic paper search |

---

## 🛠️ Custom Skills

### 🖨️ 3D Print Monitoring (`skills/wyze-cam/`)
**Two-layer failure detection system for dual Snapmaker U1 printers:**

1. **Vision AI Layer** — Claude Sonnet analyzes camera snapshots every 15 minutes via cron
   - Conservative detection: only alerts on clear failures, not warnings
   - Understands support structures, tree supports, and lattice infill as normal
   - Snapshots captured via RTSP from Wyze Cam v4 cameras

2. **ML Detection Layer (Obico)** — Self-hosted Obico server with continuous ML-based spaghetti/failure detection
   - 4 containers: web app, ML API, Redis, task worker
   - 2 moonraker-obico clients connecting remotely to each printer's Moonraker API
   - Auto-pause on failure detection
   - Print history and statistics tracking

**Camera Pipeline:**
```
Wyze Cam v4 → go2rtc (native Wyze P2P) → RTSP streams → Obico ML + Vision AI cron
```

- **go2rtc v1.9.14** — Native Go binary, ~2MB RAM, firmware-agnostic (survives Wyze FW updates)
- **2560x1440 resolution** from both cameras
- Printer status via Moonraker API (temps, progress, state)

### 🔊 Media Generation (`skills/media-gen/`)
- **`grok_media.py`** — Image + video generation via Grok Imagine API
- **`elevenlabs_tts.py`** — Text-to-speech with voice selection (Lily / Alice)
- **`video_composer.py`** — ffmpeg + Pillow compositing pipeline for multi-source videos
- **`camera_recap.py`** — ArgusAI security camera event recap videos

### 🏠 Home Assistant (`skills/home-assistant/`)
- **`ha_control.py`** — Python script for device control via Home Assistant REST API
- Lights (floor lamps, WLED strips, kennel light)
- Switches (fishtank, shelf, entry light)
- Scenes (e.g., "Feed the cats")

### 📸 ArgusAI Security (`skills/argusai/`)
- **`argusai_nlu.py`** — Natural language queries for camera events
- "Who's at the front door?" → queries API → returns description + snapshot
- 3 cameras: Back Door, Driveway, Front Door (doorbell)

### 🎲 PrintPal 3D (`skills/printpal-3d/`)
- 3D model generation from text descriptions (credit-based)
- Integration with WaveSpeed for text-to-image previews

### 💰 Coinbase (`skills/coinbase/`)
- **`coinbase_client.py`** — Portfolio, prices, market movers
- Read-only access, no trade permissions

---

## ⏰ Scheduled Tasks (Cron)

| Job | Schedule | Model | Description |
|-----|----------|-------|-------------|
| **Morning Briefing** | 6:00 AM daily | Grok 3 | Home activity, email summary, stocks, AI trends, 5-day weather forecast, voice version via ElevenLabs |
| **Print Monitor** | Every 15 min | Claude Sonnet | Camera snapshot analysis (only when printers are actively printing) |
| **Package Tracker** | Daily | — | Gmail parsing for shipping notifications |
| **Price Tracker** | Daily 9 AM | — | Check tracked item prices, alert on drops below target |
| **Weekly Review** | Weekly | — | Summary of the week's activities |

### Heartbeat System
OpenClaw polls Argus periodically. During heartbeats, Argus can:
- Check email for urgent messages
- Monitor upcoming calendar events
- Do background memory maintenance
- Run proactive checks (rotating through 2-4x daily)

---

## 🖨️ 3D Printing Setup

### Hardware
- **2x Snapmaker U1** — IDEX printers with 4 toolheads each
- Running **Klipper + Moonraker + Fluidd** firmware stack
- Multi-color printing active, multi-material planned

### Monitoring Stack
```
┌─────────────────────────────────────────────────┐
│                  ArgusAI Server                   │
│                                                   │
│  ┌──────────┐  ┌──────────────┐  ┌────────────┐ │
│  │  go2rtc   │  │    Obico     │  │ moonraker- │ │
│  │ (RTSP +   │  │  (ML fail   │  │   obico    │ │
│  │  WebRTC)  │  │  detection) │  │ (x2 clients)│ │
│  └─────┬─────┘  └──────┬──────┘  └─────┬──────┘ │
│        │               │               │         │
└────────┼───────────────┼───────────────┼─────────┘
         │               │               │
    ┌────┴────┐     ┌────┴────┐    ┌────┴─────┐
    │ Wyze Cam│     │ Wyze Cam│    │Moonraker │
    │  v4 #1  │     │  v4 #2  │    │ API x2   │
    └─────────┘     └─────────┘    └──────────┘
```

### Cost Calculator
Custom Excel workbook (`3D_Print_Cost_Pricing_Calculator.xlsx`) with 5 sheets:
- **Settings** — Electricity rate, printer depreciation
- **Materials** — Filament costs per kg/type
- **Rates** — Hourly overhead rates
- **Jobs** — Multi-piece, multi-plate job definitions
- **Dashboard** — Cost summaries and pricing recommendations

---

## 🧪 Multi-Model Development

Located in `multi-model-dev/` — research and tooling for LLM portability:

- **Personality Overlays** — Per-model YAML configs that adapt tone/style
- **Model Router** — `routing.yaml` with 7 task categories, cost-aware routing
- **Grok Client** — Direct xAI API client for Grok 3/4
- **Benchmark Suite** — A/B testing framework for personality consistency
- **Orchestrator** — Multi-model task orchestration prototype

---

## 📋 Workflows

### iMessage Scheduling
When contacts mention meetings in iMessages:
1. Detect scheduling intent
2. Check Google Calendar for conflicts
3. No conflict → Add event automatically
4. Conflict → Alert via Telegram
5. Reply with confirmation via iMessage

### Auto-Deploy (ArgusAI)
Push to ArgusAI `main` branch → n8n webhook triggers → automated deployment to production

### OpenClaw Upgrades
1. Check latest version
2. Review release notes (GitHub releases / changelog)
3. Summarize key changes for review
4. Install + restart gateway
5. Verify functionality

---

## 🔐 Security Principles

- All credentials in macOS Keychain — never in plaintext files
- Ask before any external action (emails, tweets, public posts)
- Private data stays private — especially in group chats
- `trash` over `rm` — recoverable beats gone forever
- Conservative alerting — false alarms worse than missed subtle issues

---

## 📊 Open Issues

| # | Title | Status |
|---|-------|--------|
| 18 | 3D Print Monitoring via Camera | ✅ Phases 2-4 complete (go2rtc + Vision AI + Obico) |
| 17 | Security Hardening | 🆕 Not started |
| 16 | Audio & Video Response Generation | ✅ Phases 1-3 complete, Phase 4 shelved |
| 15 | Coinbase Crypto Trading | ⏳ Awaiting API key |
| 14 | LLM Portability | ✅ Completed |
| 13 | 3D Printer Fleet Management | 🆕 Research |
| 12 | Tesla Integration | 🆕 Not started |

---

## 📁 Repository Structure

```
argus-notes/
├── README.md                    # This file
├── multi-model-dev/             # Multi-LLM orchestration research
│   ├── SKILL.md
│   ├── personality-overlays/    # Per-model tone configs
│   ├── scripts/                 # Router, orchestrator, benchmarks
│   ├── references/              # Architecture docs
│   └── routing.yaml             # Task → model routing rules
├── openclaw-integration/        # OpenClaw ↔ ArgusAI docs
│   ├── architecture.md
│   ├── webhook-setup.md
│   ├── api-integration.md
│   └── use-cases.md
└── office365/                   # Office 365 setup docs
    └── setup.md
```

### Workspace Skills (on host)
```
skills/
├── argusai/          # Security camera NLU queries
├── coinbase/         # Crypto portfolio client
├── home-assistant/   # Smart home control
├── media-gen/        # TTS, image gen, video compositing
├── printpal-3d/      # 3D model generation
└── wyze-cam/         # Print monitoring + camera snapshots
```

---

*Built with curiosity and caffeine. Maintained by Argus & Brent.*

*Last updated: March 10, 2026*
