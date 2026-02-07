# Webhook Integration Setup

Real-time ArgusAI → OpenClaw → Telegram notifications.

## Overview

```
┌─────────────┐    POST /hooks/agent    ┌─────────────┐    Telegram API    ┌─────────────┐
│   ArgusAI   │ ──────────────────────▶ │  OpenClaw   │ ─────────────────▶ │  Telegram   │
│  (event)    │                         │  (webhook)  │                    │   (Brent)   │
└─────────────┘                         └─────────────┘                    └─────────────┘
     │                                        │
     │ Alert Rule triggers                    │ Agent processes event
     │ on person/package/doorbell             │ and formats message
     └────────────────────────────────────────┘
```

## Prerequisites

- [x] OpenClaw running with TLS enabled
- [x] OpenClaw accessible on LAN (`bind: "lan"`)
- [x] ArgusAI running and detecting events
- [x] Telegram channel configured

## Step 1: Enable OpenClaw Webhooks

### 1.1 Generate Webhook Token

```bash
# Generate a secure random token
openssl rand -hex 24
# Example output: a3f8c2d1e9b7a6f5c4d3e2f1a0b9c8d7e6f5a4b3
```

### 1.2 Update OpenClaw Config

Add `hooks` section to `~/.openclaw/openclaw.json`:

```json
{
  "hooks": {
    "enabled": true,
    "token": "a3f8c2d1e9b7a6f5c4d3e2f1a0b9c8d7e6f5a4b3",
    "path": "/hooks"
  }
}
```

### 1.3 Restart Gateway

```bash
openclaw gateway restart
```

### 1.4 Test Webhook Endpoint

```bash
# Test wake endpoint
curl -X POST https://10.0.1.32:18789/hooks/wake \
  -H "Authorization: Bearer a3f8c2d1e9b7a6f5c4d3e2f1a0b9c8d7e6f5a4b3" \
  -H "Content-Type: application/json" \
  -d '{"text": "Test webhook from curl", "mode": "now"}' \
  -k

# Test agent endpoint (will trigger Telegram message)
curl -X POST https://10.0.1.32:18789/hooks/agent \
  -H "Authorization: Bearer a3f8c2d1e9b7a6f5c4d3e2f1a0b9c8d7e6f5a4b3" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test alert from ArgusAI webhook integration",
    "name": "ArgusAI",
    "deliver": true,
    "channel": "telegram",
    "to": "8310835415"
  }' \
  -k
```

Expected responses:
- `/hooks/wake`: `200 OK`
- `/hooks/agent`: `202 Accepted`

## Step 2: Configure ArgusAI Alert Rule

### 2.1 Create Webhook Alert Rule

In ArgusAI Settings → Alert Rules, create a new rule:

**Via API:**
```bash
curl -X POST https://argusai.bengtson.local:3000/api/v1/alert-rules \
  -H "X-API-Key: argus_xDpZdCLpnk74KR15Xvc5vHFbb-I7covy" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OpenClaw Notification",
    "enabled": true,
    "conditions": {
      "detection_types": ["person", "package"],
      "is_doorbell_ring": true,
      "confidence_min": 70,
      "cameras": []
    },
    "actions": [{
      "type": "webhook",
      "url": "https://10.0.1.32:18789/hooks/agent",
      "method": "POST",
      "headers": {
        "Authorization": "Bearer a3f8c2d1e9b7a6f5c4d3e2f1a0b9c8d7e6f5a4b3",
        "Content-Type": "application/json"
      },
      "body_template": {
        "message": "🔔 {{camera_name}}: {{description}}",
        "name": "ArgusAI",
        "deliver": true,
        "channel": "telegram",
        "to": "8310835415"
      }
    }]
  }'
```

### 2.2 Alert Rule Options

**Trigger conditions:**
- `detection_types`: `["person", "package", "vehicle", "animal"]`
- `is_doorbell_ring`: `true` for doorbell events only
- `confidence_min`: Minimum confidence score (0-100)
- `cameras`: Empty array = all cameras, or specific camera IDs

**Body template variables:**
- `{{camera_name}}` — Camera name (e.g., "Front Door")
- `{{description}}` — AI-generated event description
- `{{timestamp}}` — Event timestamp
- `{{confidence}}` — Confidence score
- `{{objects_detected}}` — Comma-separated list
- `{{thumbnail_url}}` — Thumbnail URL (if supported)

## Step 3: Message Formatting

### 3.1 Simple Alert

```json
{
  "message": "🔔 {{camera_name}}: {{description}}",
  "name": "ArgusAI",
  "deliver": true,
  "channel": "telegram",
  "to": "8310835415"
}
```

**Result:**
> 🔔 Front Door: Person in dark jacket rang doorbell and waited

### 3.2 Detailed Alert

```json
{
  "message": "🚨 **ArgusAI Alert**\n\n📹 Camera: {{camera_name}}\n⏰ Time: {{timestamp}}\n📝 {{description}}\n\nConfidence: {{confidence}}%",
  "name": "ArgusAI",
  "deliver": true,
  "channel": "telegram",
  "to": "8310835415"
}
```

### 3.3 Conditional Formatting (Advanced)

For different alert types, create multiple rules:

**Doorbell Rule:**
```json
{
  "message": "🔔 **Doorbell!** Someone at {{camera_name}}\n\n{{description}}",
  ...
}
```

**Package Rule:**
```json
{
  "message": "📦 **Delivery** at {{camera_name}}\n\n{{description}}",
  ...
}
```

**Person Rule:**
```json
{
  "message": "🚶 **Person detected** at {{camera_name}}\n\n{{description}}",
  ...
}
```

## Step 4: SSL Certificate Trust

ArgusAI needs to trust OpenClaw's self-signed certificate.

### Option A: Disable SSL Verification (Development)

In ArgusAI alert rule, add:
```json
{
  "verify_ssl": false
}
```

### Option B: Add CA to ArgusAI (Production)

```bash
# Copy OpenClaw cert to ArgusAI server
scp ~/.openclaw/certs/cert.pem root@argusai.bengtson.local:/usr/local/share/ca-certificates/openclaw.crt

# On ArgusAI server
ssh root@argusai.bengtson.local
update-ca-certificates
systemctl restart argusai-backend
```

## Step 5: Testing

### 5.1 Trigger a Test Event

Walk in front of a camera or ring the doorbell.

### 5.2 Check ArgusAI Logs

```bash
ssh root@argusai.bengtson.local "journalctl -u argusai-backend -f | grep -i webhook"
```

### 5.3 Check OpenClaw Logs

```bash
openclaw logs --follow | grep -i hook
```

### 5.4 Verify Telegram Delivery

You should receive a Telegram message within seconds of the event.

## Troubleshooting

### Webhook not firing

1. Check alert rule is enabled in ArgusAI
2. Verify event matches rule conditions (detection type, confidence)
3. Check ArgusAI logs for webhook errors

### 401 Unauthorized

1. Verify token matches in OpenClaw config and ArgusAI rule
2. Check Authorization header format: `Bearer <token>`

### SSL/TLS errors

1. Try `verify_ssl: false` in alert rule
2. Or add OpenClaw cert to ArgusAI trust store

### No Telegram message

1. Check OpenClaw received the webhook (logs)
2. Verify `deliver: true` in payload
3. Verify `to` matches your Telegram chat ID
4. Check Telegram channel is working: send a test message via OpenClaw

## Security Considerations

1. **Webhook token**: Use a strong, unique token
2. **Network**: Keep webhook endpoint on LAN only (not exposed to internet)
3. **TLS**: Always use HTTPS for webhook calls
4. **Rate limiting**: Consider adding rate limits if needed

## Rollback

To disable webhooks:

1. Remove `hooks` section from OpenClaw config
2. Restart gateway: `openclaw gateway restart`
3. Disable alert rule in ArgusAI

---

## Quick Reference

| Component | Value |
|-----------|-------|
| OpenClaw webhook URL | `https://10.0.1.32:18789/hooks/agent` |
| OpenClaw IP | `10.0.1.32` |
| OpenClaw port | `18789` |
| Telegram chat ID | `8310835415` |
| ArgusAI API | `https://argusai.bengtson.local:3000/api/v1` |
