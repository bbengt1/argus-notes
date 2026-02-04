# Office 365 Integration Setup

**Created:** Feb 4, 2026 @ 6:50 AM CT  
**Status:** Gathering Information

## Goal

Set up ongoing Office 365 access for:
- **Exchange**: Read, summarize, send emails
- **Calendar**: Accept events, track invites, notify on conflicts
- **macOS**: Use native CLI for consistency with `gog` (Google Workspace)

## Approach

- **CLI**: Microsoft Graph CLI (recommended for macOS)
- **Auth**: OAuth (username/password)
- **Alternative**: PowerShell 7 + ExchangeOnline module

## Information Needed (from Brent)

- [ ] Tenant ID
- [ ] Client credentials (for app auth) OR username (for user OAuth)
- [ ] Office 365 tenant domain (e.g., company.onmicrosoft.com)
- [ ] Account type: Personal (Microsoft 365 subscription) or Corporate/Organizational (Azure tenant)?

## Implementation Plan

1. Install Microsoft Graph CLI on macOS
2. Set up OAuth authentication
3. Build Office365 skill (similar to `gog` for Google)
4. Integrate with heartbeat system:
   - Email summary (read, summarize, send)
   - Calendar conflict detection & notifications

## Next Steps

Waiting for info from Brent to proceed.
