# Lead Flow

## Overview

The lead flow tracks a patient from first WhatsApp message through to completed appointment.

## Stages

```
1. LEAD_IN        → WhatsApp message received (Chatwoot)
2. CONTACT_SYNCED → Contact created in Twenty CRM
3. QUALIFIED      → Agent/human qualifies the lead
4. MEETING_SCHEDULED → Cal.com booking created
5. MEETING_COMPLETED → Appointment finished
6. CLOSED_WON     → Patient converted
```

## Detailed Flow

### Stage 1: Lead Capture (WhatsApp → Chatwoot)

```
Patient sends WhatsApp message
  → Evolution API receives
  → Routes to Chatwoot inbox "WhatsApp TPC"
  → Chatwoot creates contact + conversation
  → Webhook fires: contact_created
```

### Stage 2: Contact Sync (Chatwoot → Twenty)

```
POST /sync/webhooks/chatwoot
  event: "contact_created"
  → SyncService.sync_chatwoot_contact_to_twenty()
  → Twenty CRM contact created with:
    - firstName, lastName (split from name)
    - email (if provided)
    - phone (from WhatsApp number)
```

### Stage 3: Qualification

Currently manual. The Chatwoot agent reviews the conversation and determines if the lead is qualified.

Future: AI agent (`_route_message_to_agent`) will auto-qualify based on conversation content.

### Stage 4: Scheduling (Cal.com → Twenty + Chatwoot)

```
Agent shares Cal.com booking link in Chatwoot conversation
  → Patient books appointment on Cal.com
  → Cal.com webhook: BOOKING_CREATED
  → POST /sync/webhooks/calcom

Two parallel actions:
  1. sync_calcom_booking_to_twenty()
     → Find/create Twenty contact by email
     → Create opportunity: stage = MEETING_SCHEDULED

  2. send_booking_notification_to_chatwoot()
     → Find contact in Chatwoot
     → Find open conversation
     → Send confirmation message:
       "Agendamento confirmado! 📅 {title} 🕐 {time}"
```

### Stage 5: Meeting Completed

```
Cal.com webhook: MEETING_ENDED
  → Update Twenty opportunity: stage = MEETING_COMPLETED
```

### Stage 6: Rescheduling / Cancellation

```
Cal.com webhook: BOOKING_RESCHEDULED
  → Update Twenty opportunity
  → Notify Chatwoot: "Agendamento reagendado 🔄"

Cal.com webhook: BOOKING_CANCELLED
  → Update Twenty opportunity: stage = CANCELLED
  → Notify Chatwoot: "Agendamento cancelado ❌"
```

## Key Integration Points

| Source | Trigger | Target | Action |
|--------|---------|--------|--------|
| WhatsApp | Message | Chatwoot | Create conversation |
| Chatwoot | contact_created | Twenty | Create contact |
| Twenty | person.created | Chatwoot | Create contact |
| Cal.com | BOOKING_CREATED | Twenty | Create opportunity |
| Cal.com | BOOKING_CREATED | Chatwoot | Send notification |
| Cal.com | BOOKING_CANCELLED | Twenty | Update stage |
| Cal.com | BOOKING_CANCELLED | Chatwoot | Send notification |

## Event Types (Cal.com)

| Event | Duration | URL |
|-------|----------|-----|
| Reunião de 15 min | 15m | `/brian/15min` |
| Reunião de 30 min | 30m | `/brian/30min` |

## Opportunity Stages (Twenty)

| Stage | Meaning | Trigger |
|-------|---------|---------|
| QUALIFIED | Lead qualified by agent | Manual / AI |
| MEETING_SCHEDULED | Booking confirmed | Cal.com webhook |
| MEETING_COMPLETED | Appointment done | Cal.com webhook |
| PROPOSAL | Proposal sent | Manual |
| CANCELLED | Booking cancelled | Cal.com webhook |
