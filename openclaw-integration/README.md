# OpenClaw ↔ ArgusAI Integration

This document outlines how to integrate OpenClaw (Argus the AI assistant) with ArgusAI (the security camera system).

## Overview

**Goal:** Enable Argus (OpenClaw) to receive, process, and act on security events from ArgusAI, providing intelligent notifications, natural language queries, and proactive monitoring.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              ArgusAI System                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐  │
│  │   Cameras   │───▶│   Events    │───▶│  AI Vision  │───▶│  Database   │  │
│  │  (Protect)  │    │  Pipeline   │    │  (Claude)   │    │  (SQLite)   │  │
│  └─────────────┘    └─────────────┘    └─────────────┘    └──────┬──────┘  │
│                                                                   │         │
│                     ┌─────────────────────────────────────────────┼───────┐ │
│                     │              API Layer                      │       │ │
│                     │  ┌─────────┐  ┌─────────┐  ┌─────────────┐ │       │ │
│                     │  │  REST   │  │Webhooks │  │  WebSocket  │◀┘       │ │
│                     │  │  API    │  │ (push)  │  │ (realtime)  │         │ │
│                     │  └────┬────┘  └────┬────┘  └──────┬──────┘         │ │
│                     └───────┼────────────┼──────────────┼────────────────┘ │
└─────────────────────────────┼────────────┼──────────────┼──────────────────┘
                              │            │              │
                              ▼            ▼              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            OpenClaw Gateway                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     Integration Layer                                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │   │
│  │  │  ArgusAI     │  │   Webhook    │  │  WebSocket   │              │   │
│  │  │  Skill       │  │   Receiver   │  │   Client     │              │   │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │   │
│  └─────────┼─────────────────┼─────────────────┼────────────────────────┘   │
│            │                 │                 │                            │
│            ▼                 ▼                 ▼                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      Argus (AI Agent)                                │   │
│  │  • Natural language processing                                       │   │
│  │  • Context-aware responses                                           │   │
│  │  • Proactive notifications                                           │   │
│  │  • Multi-channel delivery (Telegram, etc.)                           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Integration Methods

### 1. REST API Polling (Simple)
Argus periodically queries ArgusAI for new events.

### 2. Webhook Push (Recommended)  
ArgusAI pushes events to OpenClaw webhook endpoint.

### 3. WebSocket Realtime
Persistent connection for instant event notifications.

## Documents

| Document | Description |
|----------|-------------|
| [architecture.md](./architecture.md) | Detailed system architecture |
| [api-integration.md](./api-integration.md) | API endpoints and usage |
| [action-items.md](./action-items.md) | Implementation checklist |
| [use-cases.md](./use-cases.md) | Example scenarios |

## Quick Start

1. Configure ArgusAI API key in OpenClaw
2. Create ArgusAI skill for natural language queries
3. Set up webhook endpoint for push notifications
4. Test with sample queries

See [action-items.md](./action-items.md) for the full implementation plan.
