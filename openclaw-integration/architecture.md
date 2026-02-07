# Integration Architecture

## System Components

### ArgusAI (Security System)
- **Location:** `argusai.bengtson.local:3000`
- **Backend:** FastAPI on port 8000 (proxied)
- **Database:** SQLite with 808+ events
- **Cameras:** 3 UniFi Protect (Back Door, Driveway, Front Door)
- **AI Providers:** GPT-4o-mini, Claude 3 Haiku (fallback)

### OpenClaw (AI Assistant)
- **Location:** `brents-mac-mini.bengtson.local:18789`
- **Agent:** Argus (main session)
- **Channels:** Telegram, Webchat
- **Model:** Claude Opus 4.5

## Data Flow Patterns

### Pattern 1: Event Push (Webhook)

```
ArgusAI Event → Webhook POST → OpenClaw Gateway → Argus Agent → Telegram
     │                              │
     │   POST /webhooks/argusai     │
     │   {                          │
     │     "event_id": "uuid",      │
     │     "camera": "Front Door",  │
     │     "description": "...",    │
     │     "thumbnail_url": "...",  │
     │     "confidence": 85         │
     │   }                          │
     └──────────────────────────────┘
```

**Pros:** Real-time, low latency, efficient
**Cons:** Requires webhook endpoint configuration

### Pattern 2: Polling (Cron/Heartbeat)

```
┌─────────────────────────────────────────────────────┐
│  OpenClaw Heartbeat (every 30 min)                  │
│                                                     │
│  1. Check last_event_timestamp from memory          │
│  2. GET /api/v1/events?since={timestamp}            │
│  3. Process new events                              │
│  4. Notify if notable (person, package, etc.)       │
│  5. Update last_event_timestamp                     │
└─────────────────────────────────────────────────────┘
```

**Pros:** Simple, no ArgusAI changes needed
**Cons:** Latency (up to 30 min), API calls on schedule

### Pattern 3: WebSocket Subscription

```
OpenClaw ──WSS──▶ ArgusAI /ws
                    │
                    ├── event.created
                    ├── camera.status  
                    └── notification.new
```

**Pros:** Instant, bidirectional
**Cons:** Connection management complexity

## Recommended Architecture

### Phase 1: Polling + Skill (MVP)

```
┌────────────────────────────────────────────────────────────────┐
│                    OpenClaw Workspace                          │
│                                                                │
│  TOOLS.md                                                      │
│  └── ArgusAI API Key: argus_xxxxx                              │
│                                                                │
│  skills/argusai/SKILL.md                                       │
│  └── Commands:                                                 │
│      • "what happened at [camera] today?"                      │
│      • "any deliveries?"                                       │
│      • "show me the last event"                                │
│      • "security summary"                                      │
│                                                                │
│  HEARTBEAT.md                                                  │
│  └── Check ArgusAI for notable events (person/package)         │
│                                                                │
│  memory/argusai-state.json                                     │
│  └── { "last_checked": "...", "last_event_id": "..." }         │
└────────────────────────────────────────────────────────────────┘
```

### Phase 2: Webhook Push

```
┌─────────────────────────────────────────────────────────────────┐
│  ArgusAI Alert Rule                                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Name: "OpenClaw Notification"                           │   │
│  │  Trigger: person OR package detected                     │   │
│  │  Action: Webhook POST to OpenClaw                        │   │
│  │  URL: https://10.0.1.32:18789/webhooks/argusai           │   │
│  │  Headers: { "X-Webhook-Secret": "..." }                  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Phase 3: Full Integration

- WebSocket for real-time
- Voice summaries via TTS
- Camera control commands
- Entity recognition ("who's at the door?")

## Security Considerations

1. **API Key Storage:** Store ArgusAI API key in OpenClaw credentials (encrypted)
2. **Webhook Auth:** Use shared secret for webhook validation
3. **Network:** Both systems on LAN, TLS enabled
4. **Scope:** Use minimal API key scope (`read:events`, `read:cameras`)

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/events` | List recent events |
| `GET /api/v1/events/{id}` | Event details + thumbnail |
| `GET /api/v1/cameras` | Camera status |
| `GET /api/v1/events/stats` | Activity statistics |
| `GET /api/v1/system/health` | Health check |
| `WS /ws` | Real-time event stream |

## Event Filtering Logic

```python
def should_notify(event):
    """Determine if event warrants notification."""
    
    # Always notify
    if event.is_doorbell_ring:
        return True, "doorbell"
    
    if "package" in event.objects_detected:
        return True, "delivery"
    
    # Notify for people with high confidence
    if "person" in event.objects_detected and event.confidence >= 80:
        return True, "person"
    
    # Don't notify for low confidence or animals/vehicles only
    return False, None
```

## Message Templates

### Doorbell Ring
```
🔔 Doorbell rang at Front Door

Someone is at the door. [View thumbnail]
```

### Package Delivery
```
📦 Package delivered at Back Door

"FedEx delivery person placed a package on the step"
Confidence: 95%
```

### Person Detected
```
🚶 Person detected at Driveway

"Person in dark jacket approaching from left side"
Camera: Driveway | 2:15 PM
```

### Daily Summary (via Heartbeat)
```
📊 ArgusAI Daily Summary

Today's activity:
• 12 events detected
• 3 deliveries
• 2 doorbell rings
• Quiet overnight (no activity 11pm-7am)

Most active: Driveway (7 events)
```
