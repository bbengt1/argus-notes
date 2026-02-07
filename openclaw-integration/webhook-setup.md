# Webhook Integration Setup

Real-time ArgusAI → OpenClaw → Telegram notifications.

## Overview

```
┌─────────────┐  POST /hooks/argusai  ┌─────────────┐              ┌─────────────┐
│   ArgusAI   │ ────────────────────▶ │  OpenClaw   │─────────────▶│  Telegram   │
│  (events)   │   native JSON         │  (webhook)  │   formatted  │   (Brent)   │
└─────────────┘                       └──────┬──────┘   message     └─────────────┘
                                             │
                                      Transform JS
                                      (payload → agent)
```

## Current Configuration

### OpenClaw Hooks

```json
{
  "hooks": {
    "enabled": true,
    "path": "/hooks",
    "token": "c5f62ff21092d77fb5c49060a43395607e46f1f2a8653df7",
    "transformsDir": "/Users/brentbengtson/.openclaw/hooks",
    "mappings": [
      {
        "id": "argusai",
        "match": { "path": "/argusai" },
        "action": "agent",
        "name": "ArgusAI",
        "deliver": true,
        "channel": "telegram",
        "to": "8310835415",
        "transform": {
          "module": "argusai-transform.js",
          "export": "transform"
        }
      }
    ]
  }
}
```

### Transform Module

Location: `~/.openclaw/hooks/argusai-transform.js`

```javascript
function transform(payload) {
  const cameraName = payload.camera?.name || 'Unknown Camera';
  const description = payload.description || 'Motion detected';
  const confidence = payload.confidence || 0;
  const objects = payload.objects_detected || [];
  const eventId = payload.event_id;
  
  // Emoji based on detection type
  let emoji = '📹';
  if (objects.includes('package')) emoji = '📦';
  else if (objects.includes('person')) emoji = '🚶';
  else if (objects.includes('vehicle')) emoji = '🚗';
  else if (objects.includes('animal')) emoji = '🐾';
  
  const message = `${emoji} **${cameraName}**\n\n${description}\n\n_Confidence: ${confidence}%_`;
  
  return {
    action: 'agent',
    message: message,
    name: 'ArgusAI',
    deliver: true,
    channel: 'telegram',
    to: '8310835415',
    sessionKey: `hook:argusai:${eventId || Date.now()}`
  };
}

module.exports = { transform };
```

### ArgusAI Alert Rule

| Field | Value |
|-------|-------|
| ID | `30abecb2-8aa8-4ee3-b103-74b6980c6415` |
| Name | OpenClaw - All Events |
| Enabled | ✅ |
| Triggers | Person, Package (≥70% confidence) |
| Webhook URL | `https://10.0.1.32:18789/hooks/argusai` |

## How It Works

1. **ArgusAI detects event** (person/package at any camera)
2. **Webhook fires** to `/hooks/argusai` with native ArgusAI JSON:
   ```json
   {
     "event_id": "abc123",
     "camera": {"name": "Front Door"},
     "description": "Person in dark jacket waiting at door",
     "confidence": 87,
     "objects_detected": ["person"],
     "timestamp": "2026-02-07T08:30:00Z"
   }
   ```
3. **Transform converts** payload to OpenClaw agent format
4. **Agent processes** message and formats for Telegram
5. **Telegram delivers** notification to Brent

## Testing

### Manual Test

```bash
curl -sk -X POST "https://10.0.1.32:18789/hooks/argusai" \
  -H "Authorization: Bearer c5f62ff21092d77fb5c49060a43395607e46f1f2a8653df7" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "test-001",
    "camera": {"name": "Front Door"},
    "description": "Package detected on front porch",
    "confidence": 92,
    "objects_detected": ["package"]
  }'
```

Expected response:
```json
{"ok": true, "runId": "..."}
```

### Live Test

Walk in front of a camera with person detection enabled.

## Troubleshooting

### Check webhook firing
```bash
curl -sk "https://argusai.bengtson.local:3000/api/v1/alert-rules" \
  -H "X-API-Key: argus_xDpZdCLpnk74KR15Xvc5vHFbb-I7covy" | \
  jq '.data[] | select(.name | contains("OpenClaw")) | {trigger_count, last_triggered_at}'
```

### Check OpenClaw logs
```bash
openclaw logs --follow | grep -i argusai
```

### Verify transform loads
```bash
node -e "console.log(require('/Users/brentbengtson/.openclaw/hooks/argusai-transform.js'))"
```

## Security Notes

- Webhook token is separate from gateway auth token
- TLS enabled (self-signed cert, ArgusAI has `verify_ssl: false`)
- LAN-only access (not exposed to internet)

## Quick Reference

| Component | Value |
|-----------|-------|
| OpenClaw Webhook | `https://10.0.1.32:18789/hooks/argusai` |
| Webhook Token | `c5f62ff21092d77fb5c49060a43395607e46f1f2a8653df7` |
| Transform File | `~/.openclaw/hooks/argusai-transform.js` |
| ArgusAI API | `https://argusai.bengtson.local:3000/api/v1` |
| ArgusAI Key | `argus_xDpZdCLpnk74KR15Xvc5vHFbb-I7covy` |
| Telegram Chat ID | `8310835415` |
| Alert Rule ID | `30abecb2-8aa8-4ee3-b103-74b6980c6415` |

---
*Last updated: 2026-02-07*
