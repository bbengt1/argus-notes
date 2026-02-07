# Use Cases

## Conversational Queries

### 1. Status Check
**User:** "Is everything okay at home?"

**Argus Response:**
> 👁️ Checking ArgusAI...
> 
> Everything looks normal! Last 2 hours:
> - 3 motion events (all low-activity)
> - No people or packages detected
> - All cameras online
> 
> Your red BMW is in the driveway. 🚗

---

### 2. Specific Camera Query
**User:** "What happened at the front door today?"

**Argus Response:**
> 📹 Front Door activity today:
> 
> **2:15 PM** — Doorbell ring 🔔
> "Person in dark jacket approached and rang doorbell, waited 30 seconds, then left"
> 
> **11:30 AM** — Package delivery 📦
> "FedEx driver placed a medium-sized box on the step"
> 
> **9:45 AM** — Motion detected
> "Mail carrier approached mailbox, no doorbell interaction"
> 
> Total: 3 events

---

### 3. Delivery Check
**User:** "Did any packages arrive today?"

**Argus Response:**
> 📦 Yes! 2 deliveries today:
> 
> 1. **11:30 AM** — Front Door
>    "FedEx driver with medium box"
>    
> 2. **5:04 PM** — Back Door  
>    "Delivery person in dark hoodie placed package on step"
>    
> Both still on the porch based on latest camera check.

---

### 4. Recent Activity
**User:** "Show me the last security event"

**Argus Response:**
> 🔔 Most recent event (5 min ago):
> 
> **Camera:** Back Door
> **Time:** 5:04 PM
> **Type:** Person detected
> 
> "Delivery person wearing dark jacket approached, placed package, departed left"
> 
> Confidence: 95% | Objects: person, package
> 
> [thumbnail would be here if supported]

---

## Proactive Notifications

### 5. Doorbell Alert (Real-time)
*ArgusAI detects doorbell ring → Webhook → OpenClaw → Telegram*

**Argus (via Telegram):**
> 🔔 **Doorbell rang!**
> 
> Someone's at the Front Door.
> "Person in blue uniform, appears to be delivery driver"
> 
> *5:32 PM*

---

### 6. Package Delivery (Real-time)
**Argus (via Telegram):**
> 📦 **Package delivered**
> 
> Back Door — just now
> "Amazon driver placed large box on the back step"
> 
> Confidence: 92%

---

### 7. Unknown Person Alert
**Argus (via Telegram):**
> ⚠️ **Unknown person at Driveway**
> 
> Someone I don't recognize is in the driveway.
> "Adult male in casual clothes, walking toward garage"
> 
> *Doesn't match any known entities*
> 
> Reply "who is that?" for more details.

---

## Scheduled Summaries

### 8. Morning Briefing
*Triggered at 7:00 AM via cron*

**Argus (via Telegram):**
> ☀️ **Good morning! Overnight security summary:**
> 
> All quiet overnight (11 PM - 7 AM):
> - 2 motion events (animals)
> - No people detected
> - All cameras operational
> 
> Today's weather: 28°F, snow expected
> *Driveway may need salting*

---

### 9. Daily Summary
*Triggered at 9:00 PM via cron*

**Argus (via Telegram):**
> 📊 **Daily Security Digest**
> 
> **Activity:**
> - 15 total events
> - 4 people detected
> - 2 package deliveries
> - 1 doorbell ring
> 
> **Highlights:**
> - FedEx delivery at 11:30 AM
> - Unknown visitor at 3:45 PM (stayed 2 min)
> - Your car left at 8:15 AM, returned 5:30 PM
> 
> **Status:** All cameras online, 103 MB storage used

---

## Control Commands (Phase 3)

### 10. Camera Control
**User:** "Disable the back door camera for an hour"

**Argus Response:**
> ⏸️ Back Door camera disabled until 7:20 PM.
> 
> I'll re-enable it automatically. You can also say "enable back door camera" anytime.

---

### 11. Sensitivity Adjustment
**User:** "The driveway camera is too sensitive, too many false alerts"

**Argus Response:**
> 🎚️ I can adjust that. Current settings:
> - Motion sensitivity: Medium
> - Cooldown: 60 seconds
> 
> Want me to:
> 1. Reduce sensitivity to Low
> 2. Increase cooldown to 120 seconds
> 3. Both

---

## Error Handling

### 12. System Down
**User:** "What's happening at the front door?"

**Argus Response:**
> ⚠️ I can't reach ArgusAI right now.
> 
> The backend appears to be down. Last successful check was 15 minutes ago.
> 
> Want me to:
> - SSH in and check the service?
> - Keep trying and notify you when it's back?

---

### 13. Camera Offline
**User:** "Check the driveway camera"

**Argus Response:**
> 🔴 Driveway camera is offline.
> 
> Last connected: 10 minutes ago
> Error: "Connection to Protect controller lost"
> 
> This might be a network issue. The Protect controller (10.0.1.254) may need attention.

---

## Contextual Awareness

### 14. Pattern Recognition
**User:** "Is there a pattern to the deliveries?"

**Argus Response:**
> 📈 Looking at the last 30 days:
> 
> **Delivery patterns:**
> - Most deliveries: 11 AM - 2 PM (68%)
> - FedEx usually comes around 11:30 AM
> - Amazon varies more (10 AM - 6 PM)
> - UPS typically afternoon (2-4 PM)
> 
> **Peak days:** Tuesday and Thursday
> **Quietest:** Sunday (rarely any deliveries)

---

### 15. Entity Context
**User:** "Who was at the door at 3pm?"

**Argus Response:**
> 🚶 At 3:00 PM, there was an unrecognized person at the Front Door.
> 
> Description: "Adult male, gray jacket, carrying clipboard"
> 
> This person has been seen once before (last Tuesday at 2:45 PM). Possibly a recurring salesperson or surveyor.
> 
> Want me to mark them as "known" or "blocked"?
