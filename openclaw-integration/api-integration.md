# API Integration Guide

## Connection Details

```
Base URL: https://argusai.bengtson.local:3000/api/v1
Auth Header: X-API-Key: argus_xDpZdCLpnk74KR15Xvc5vHFbb-I7covy
```

## Authentication

All requests require the `X-API-Key` header:

```bash
curl -sk -H "X-API-Key: $ARGUSAI_KEY" "$ARGUSAI_URL/cameras"
```

## Core Endpoints

### List Events

```bash
GET /events?limit=10&offset=0
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| limit | int | Max events (default 20) |
| offset | int | Pagination offset |
| camera_id | uuid | Filter by camera |
| detection_type | string | person, vehicle, package, animal |
| since | datetime | Events after this time (ISO 8601) |

**Response:**
```json
{
  "events": [
    {
      "id": "uuid",
      "camera_id": "uuid",
      "camera_name": "Front Door",
      "timestamp": "2026-02-06T17:04:47Z",
      "description": "Person approached door...",
      "confidence": 95,
      "objects_detected": ["person", "package"],
      "thumbnail_path": "/api/v1/thumbnails/...",
      "is_doorbell_ring": false,
      "smart_detection_type": "person",
      "entity_name": "FedEx Driver"
    }
  ],
  "total_count": 808,
  "has_more": true
}
```

### Get Single Event

```bash
GET /events/{event_id}
```

### List Cameras

```bash
GET /cameras
```

**Response:**
```json
[
  {
    "id": "2b0887a3-3fae-4fd9-b64b-910a18df5d7d",
    "name": "Back Door",
    "type": "rtsp",
    "is_enabled": true,
    "source_type": "protect",
    "is_doorbell": false
  }
]
```

### Camera Map (for queries)

| Name | ID | Type |
|------|-----|------|
| Back Door | `2b0887a3-3fae-4fd9-b64b-910a18df5d7d` | Camera |
| Driveway | `6470859b-5fbb-410b-8570-d8f82cf01797` | Camera |
| Front Door | `fd474199-bb51-4848-b8d4-39cf9b9e30ff` | Doorbell |

### System Health

```bash
GET /system/health
```

### Storage Stats

```bash
GET /system/storage
```

**Response:**
```json
{
  "database_mb": 82.88,
  "thumbnails_mb": 20.5,
  "total_mb": 103.38,
  "event_count": 808
}
```

### Protect Controllers

```bash
GET /protect/controllers
```

**Response:**
```json
{
  "data": [{
    "name": "Home UDM",
    "host": "10.0.1.254",
    "is_connected": true,
    "last_error": null
  }],
  "meta": { "count": 1 }
}
```

## WebSocket Connection

```javascript
const ws = new WebSocket('wss://argusai.bengtson.local:3000/ws');

ws.onmessage = (msg) => {
  const data = JSON.parse(msg.data);
  
  switch(data.type) {
    case 'event.created':
      // New event detected
      handleNewEvent(data.event);
      break;
    case 'camera.status':
      // Camera online/offline
      break;
  }
};
```

## Thumbnail Access

Thumbnails require authentication:

```bash
curl -sk -H "X-API-Key: $KEY" \
  "https://argusai.bengtson.local:3000/api/v1/thumbnails/2026-02-06/camera_timestamp.jpg" \
  -o thumbnail.jpg
```

## Example: Get Today's Events

```bash
TODAY=$(date -u +%Y-%m-%dT00:00:00Z)

curl -sk -H "X-API-Key: $ARGUSAI_KEY" \
  "$ARGUSAI_URL/events?since=$TODAY&limit=50" | \
  jq '.events[] | {time: .timestamp, camera: .camera_name, desc: .description}'
```

## Example: Check for Recent People

```bash
curl -sk -H "X-API-Key: $ARGUSAI_KEY" \
  "$ARGUSAI_URL/events?detection_type=person&limit=5" | \
  jq '.events[] | "\(.camera_name) @ \(.timestamp): \(.description)"'
```

## Example: Count Deliveries Today

```bash
curl -sk -H "X-API-Key: $ARGUSAI_KEY" \
  "$ARGUSAI_URL/events?since=$TODAY" | \
  jq '[.events[] | select(.objects_detected | contains(["package"]))] | length'
```

## Error Responses

| Status | Meaning |
|--------|---------|
| 401 | Invalid or missing API key |
| 403 | Insufficient scope |
| 404 | Resource not found |
| 429 | Rate limited |
| 500 | Server error |

**Error Format:**
```json
{
  "detail": "Error message here"
}
```

## Rate Limits

- Default: 100 requests/minute per API key
- Headers show remaining quota:
  ```
  X-RateLimit-Limit: 100
  X-RateLimit-Remaining: 95
  X-RateLimit-Reset: 1735123456
  ```
