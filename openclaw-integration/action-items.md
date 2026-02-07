# Action Items

## Phase 1: MVP (Polling + Skill)

### 1.1 Store API Credentials
- [ ] Add ArgusAI API key to OpenClaw credentials
- [ ] Update TOOLS.md with ArgusAI connection info

**Details:**
```bash
# Add to ~/.openclaw/credentials/ or TOOLS.md
ArgusAI:
  endpoint: https://argusai.bengtson.local:3000/api/v1
  api_key: argus_xDpZdCLpnk74KR15Xvc5vHFbb-I7covy
```

### 1.2 Create ArgusAI Skill
- [ ] Create skill directory structure
- [ ] Write SKILL.md with query patterns
- [ ] Implement API wrapper functions
- [ ] Test natural language queries

**File:** `skills/argusai/SKILL.md`

```markdown
---
name: argusai
description: Query and monitor ArgusAI security camera events
---

# ArgusAI Skill

Query security camera events from ArgusAI.

## Endpoints
- Base: https://argusai.bengtson.local:3000/api/v1
- Auth: X-API-Key header

## Commands

### Recent Events
\`\`\`bash
curl -sk -H "X-API-Key: $ARGUSAI_KEY" \
  "$ARGUSAI_URL/events?limit=10" | jq '.events'
\`\`\`

### Events by Camera
\`\`\`bash
curl -sk -H "X-API-Key: $ARGUSAI_KEY" \
  "$ARGUSAI_URL/events?camera_id={id}&limit=10"
\`\`\`

### Camera List
\`\`\`bash
curl -sk -H "X-API-Key: $ARGUSAI_KEY" \
  "$ARGUSAI_URL/cameras"
\`\`\`

## Camera IDs
- Back Door: 2b0887a3-3fae-4fd9-b64b-910a18df5d7d
- Driveway: 6470859b-5fbb-410b-8570-d8f82cf01797
- Front Door: fd474199-bb51-4848-b8d4-39cf9b9e30ff
```

### 1.3 Add Heartbeat Check
- [ ] Create memory/argusai-state.json for tracking
- [ ] Add ArgusAI check to HEARTBEAT.md
- [ ] Implement notable event detection
- [ ] Test notification flow

**File:** `HEARTBEAT.md` addition
```markdown
## ArgusAI Check (every 2-4 hours)
- Query events since last check
- Notify if: doorbell, package, unrecognized person
- Update argusai-state.json with last_event_id
```

**File:** `memory/argusai-state.json`
```json
{
  "last_checked": "2026-02-06T18:00:00Z",
  "last_event_id": "aa966438-e2d0-49a3-828f-6b129aeaca35",
  "daily_summary_sent": "2026-02-06"
}
```

### 1.4 Test Queries
- [ ] "What happened at the front door today?"
- [ ] "Any packages delivered?"
- [ ] "Show me the last security event"
- [ ] "Is everything okay at home?"

---

## Phase 2: Webhook Push Notifications

### 2.1 OpenClaw Webhook Endpoint
- [ ] Research OpenClaw webhook capabilities
- [ ] Configure webhook receiver
- [ ] Test with curl

**Question:** Does OpenClaw support incoming webhooks? Check docs.

### 2.2 ArgusAI Alert Rule
- [ ] Create alert rule in ArgusAI
- [ ] Configure webhook URL
- [ ] Set trigger conditions
- [ ] Test end-to-end

**ArgusAI Config:**
```json
{
  "name": "OpenClaw Notification",
  "enabled": true,
  "conditions": {
    "detection_types": ["person", "package"],
    "confidence_min": 75,
    "cameras": ["all"]
  },
  "actions": [{
    "type": "webhook",
    "url": "https://10.0.1.32:18789/webhooks/argusai",
    "method": "POST",
    "headers": {
      "X-Webhook-Secret": "shared-secret-here"
    }
  }]
}
```

### 2.3 Message Formatting
- [ ] Create notification templates
- [ ] Handle thumbnail embedding
- [ ] Test Telegram rendering

---

## Phase 3: Advanced Features

### 3.1 WebSocket Real-time
- [ ] Implement WebSocket client in skill
- [ ] Handle connection lifecycle
- [ ] Process real-time events

### 3.2 Voice Summaries
- [ ] Daily security summary via TTS
- [ ] "Tell me about today's activity"
- [ ] Configurable summary time

### 3.3 Camera Control
- [ ] "Enable/disable camera X"
- [ ] "Start recording on driveway"
- [ ] Requires write:cameras scope

### 3.4 Entity Recognition
- [ ] "Who was at the door?"
- [ ] Track recognized vs unknown people
- [ ] Alert on unknown visitors

---

## Implementation Priority

| Priority | Task | Effort | Impact |
|----------|------|--------|--------|
| P0 | Store API credentials | 5 min | Required |
| P0 | Create basic skill | 30 min | High |
| P1 | Heartbeat integration | 30 min | High |
| P1 | Test natural language queries | 15 min | High |
| P2 | Webhook notifications | 2 hr | Medium |
| P2 | Telegram formatting | 1 hr | Medium |
| P3 | WebSocket real-time | 4 hr | Low |
| P3 | Voice summaries | 2 hr | Low |

---

## Success Criteria

### MVP Complete When:
- [ ] Can ask "what's happening at home?" and get coherent response
- [ ] Heartbeat checks ArgusAI and alerts on notable events
- [ ] Brent receives Telegram notification for doorbell/package

### Phase 2 Complete When:
- [ ] Real-time notifications within 30 seconds of event
- [ ] Thumbnail images in Telegram notifications
- [ ] No polling required for common events

### Phase 3 Complete When:
- [ ] Voice summaries working
- [ ] Camera control via natural language
- [ ] Entity tracking ("that's the FedEx guy again")
