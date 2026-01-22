# Integrations

## Webhook Configuration

All webhooks use a shared secret for HMAC-SHA256 signature verification.

### Twenty CRM → MedFlow

| Field | Value |
|-------|-------|
| URL | `https://api.trafegoparaconsultorios.com.br/sync/webhooks/twenty` |
| Events | All Objects / All Events |
| Secret | Configured in Twenty webhook settings |
| Signature Header | `X-Twenty-Webhook-Signature` |
| Timestamp Header | `X-Twenty-Webhook-Timestamp` |
| Webhook ID | `7cf2adbd-3f41-449e-b0cf-fc2e8e65b242` |

**Payload Format:**
```json
{
  "eventName": "person.created",
  "record": {
    "id": "uuid",
    "name": { "firstName": "...", "lastName": "..." },
    "email": { "primaryEmail": "..." },
    "phone": { "primaryPhoneNumber": "..." }
  }
}
```

**Processed Events:**
- `person.created` / `person.updated` → Sync contact to Chatwoot
- `opportunity.updated` → Trigger stage-based automation

---

### Cal.com → MedFlow

| Field | Value |
|-------|-------|
| URL | `https://api.trafegoparaconsultorios.com.br/sync/webhooks/calcom` |
| Events | BOOKING_CREATED, BOOKING_RESCHEDULED, BOOKING_CANCELLED, MEETING_ENDED |
| Secret | Configured in Cal.com webhook settings |
| Signature Header | `X-Cal-Signature-256` |
| Format | `sha256=<hex>` |

**Payload Format:**
```json
{
  "triggerEvent": "BOOKING_CREATED",
  "payload": {
    "title": "Reunião de 15 min",
    "startTime": "2026-01-23T10:00:00Z",
    "attendees": [
      { "email": "patient@example.com", "name": "Patient Name" }
    ],
    "metadata": {
      "twenty_opportunity_id": "optional-uuid"
    }
  }
}
```

**Actions per Event:**
| Event | Twenty Action | Chatwoot Action |
|-------|--------------|-----------------|
| BOOKING_CREATED | Create opportunity (MEETING_SCHEDULED) | Send confirmation message |
| BOOKING_RESCHEDULED | Update opportunity | Send reschedule notification |
| BOOKING_CANCELLED | Update stage (CANCELLED) | Send cancellation notification |

---

### Chatwoot → MedFlow

| Field | Value |
|-------|-------|
| URL | `https://api.trafegoparaconsultorios.com.br/sync/webhooks/chatwoot` |
| Name | TPC Integration Sync |
| Events | conversation_created, message_created, contact_created, conversation_status_changed |
| Signature Header | `X-Chatwoot-Signature` |

**Payload Format (contact_created):**
```json
{
  "event": "contact_created",
  "contact": {
    "id": 1,
    "name": "Patient Name",
    "email": "patient@example.com",
    "phone_number": "+5511999990000",
    "custom_attributes": {}
  }
}
```

**Actions per Event:**
| Event | Action |
|-------|--------|
| contact_created | Sync contact to Twenty CRM |
| message_created | Route to AI agent (if incoming + AI enabled) |

---

### Evolution API → Chatwoot

| Field | Value |
|-------|-------|
| Type | Direct integration (not via MedFlow) |
| Chatwoot URL | Internal Docker URL |
| Account ID | 1 |
| Inbox Name | WhatsApp TPC |
| Auto Create | true |

**Flow:**
```
WhatsApp → Evolution API → Chatwoot Inbox (WhatsApp TPC)
```

No MedFlow involvement - this is a direct Evolution API ↔ Chatwoot integration.

---

## Signature Verification

The `verify_webhook_signature()` function in `services/sync_service.py` handles multiple formats:

1. **`sha256=<hex>`** - Cal.com format
2. **`sha1=<hex>`** - Legacy format
3. **Raw hex** - When no prefix present
4. **Timestamp-based** - Twenty format: `HMAC(timestamp:payload, secret)`

```python
# Verification flow:
1. Parse prefix (sha256= or sha1=) to determine algorithm
2. Build string_to_sign (with optional timestamp prefix)
3. Compute HMAC with shared secret
4. Constant-time comparison via hmac.compare_digest()
```

## Service APIs Used

### Twenty CRM API (GraphQL)
- `list_contacts(filter_, limit)` - Query contacts
- `create_contact(first_name, last_name, email, phone)` - Create person
- `update_contact(id, ...)` - Update person fields
- `create_opportunity(name, stage, contact_id, closeDate)` - Create deal
- `update_opportunity_stage(id, stage)` - Move pipeline stage
- `register_webhook(url, events)` - Register webhook

### Chatwoot API (REST)
- `GET /api/v1/accounts/{id}/contacts/search?q=` - Search contacts
- `POST /api/v1/accounts/{id}/contacts` - Create contact
- `PUT /api/v1/accounts/{id}/contacts/{id}` - Update contact
- `GET /api/v1/accounts/{id}/conversations` - List conversations
- `POST /api/v1/accounts/{id}/conversations/{id}/messages` - Send message
- `POST /api/v1/accounts/{id}/webhooks` - Create webhook

### Cal.com API (REST)
- `POST /api/v1/bookings` - Create booking
- `POST /api/v1/webhooks` - Create webhook
