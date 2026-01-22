# Runbook

## Operations & Troubleshooting

### Quick Health Checks

```bash
# MedFlow API
curl https://api.trafegoparaconsultorios.com.br/health

# Twenty CRM
curl http://twenty-m8w8gso08k44wc0cs4oswosg.72.61.37.176.sslip.io/api/open-api/core

# Chatwoot
curl -H "api_access_token: <TOKEN>" \
  http://chatwoot-d8gc84okgccw84g444wgswko.72.61.37.176.sslip.io/api/v1/accounts/1/contacts

# Cal.com
curl http://calcom-bk0k00wkoog8ck48c4k8k4gc.72.61.37.176.sslip.io

# Evolution API
curl https://evo.trafegoparaconsultorios.com.br
```

### Common Issues

#### 1. Container Not Accessible (504 Gateway Timeout)

**Symptoms:** Traefik returns 504 when accessing service URL.

**Cause:** Container not connected to the `coolify` Docker network.

**Fix:**
```bash
# SSH into server
docker network connect coolify <container-name>
docker restart coolify-proxy
```

#### 2. Webhook Signature Verification Failed

**Symptoms:** Webhook endpoint returns 401 "Invalid signature".

**Diagnosis:**
```bash
# Check logs
docker logs <integration-container> | grep "Signature verification"
```

**Common Causes:**
- Secret mismatch between sender and receiver
- Payload modified in transit (encoding issues)
- Timestamp drift (for Twenty format)

**Fix:** Verify the webhook secret matches in both the sending service and the `WEBHOOK_SECRET` env var.

#### 3. CHATWOOT_API_URL Empty

**Symptoms:** Contact sync fails silently, logs show connection errors.

**Cause:** Docker Compose multi-service projects have separate env var sets. The env var may be set for one service but not the integration service.

**Fix:**
1. Go to Coolify → Project → Environment Variables
2. Find CHATWOOT_API_URL for the `integration` service specifically
3. Set to: `http://chatwoot-d8gc84okgccw84g444wgswko.72.61.37.176.sslip.io`
4. Redeploy (Stop + Deploy, not just Restart)

#### 4. Contacts Not Syncing to Chatwoot

**Diagnosis:**
```bash
# Test webhook manually
curl -X POST https://api.trafegoparaconsultorios.com.br/sync/webhooks/twenty \
  -H "Content-Type: application/json" \
  -d '{
    "eventName": "person.created",
    "record": {
      "id": "test-123",
      "name": {"firstName": "Test", "lastName": "User"},
      "email": {"primaryEmail": "test@example.com"},
      "phone": {"primaryPhoneNumber": "+5511999990000"}
    }
  }'

# Check Chatwoot contacts
curl -H "api_access_token: <TOKEN>" \
  "http://chatwoot-d8gc84okgccw84g444wgswko.72.61.37.176.sslip.io/api/v1/accounts/1/contacts"
```

#### 5. Database Connection Failed

**Symptoms:** API returns 500, logs show SQLAlchemy connection errors.

**Fix:**
```bash
# Check DB status via API
curl https://api.trafegoparaconsultorios.com.br/api/admin/db-status

# If tables missing, run migrations
curl -X POST https://api.trafegoparaconsultorios.com.br/api/admin/run-migrations
```

### Deployment

#### Redeploy via Coolify
1. Navigate to Coolify dashboard
2. Select the MedFlow project
3. Click "Redeploy" on the integration service
4. Wait for status: "Finished (healthy)"

#### Environment Variables (Critical)
| Variable | Required | Purpose |
|----------|----------|---------|
| DATABASE_URL | Yes | PostgreSQL connection |
| JWT_SECRET | Yes (prod) | Token signing |
| WEBHOOK_SECRET | Yes (prod) | Webhook HMAC verification |
| CHATWOOT_API_URL | Yes | Chatwoot base URL |
| CHATWOOT_API_KEY | Yes | Chatwoot API token |
| TWENTY_API_URL | Yes | Twenty CRM base URL |
| TWENTY_API_KEY | No* | Twenty API key (*uses webhook only) |
| CALCOM_API_URL | Yes | Cal.com base URL |

### Database Operations

```bash
# Check current state
curl https://api.trafegoparaconsultorios.com.br/api/admin/db-status

# Run migrations
curl -X POST https://api.trafegoparaconsultorios.com.br/api/admin/run-migrations

# Seed initial data (creates agency + superusers)
curl -X POST https://api.trafegoparaconsultorios.com.br/api/admin/seed \
  -H "Content-Type: application/json" \
  -d '{"password": "your-password"}'

# Full reset (DESTRUCTIVE)
curl -X POST https://api.trafegoparaconsultorios.com.br/api/admin/reset-db
```

### Monitoring

#### Logs
```bash
# On server via SSH
docker logs <container-name> --tail 100 -f

# Filter for errors
docker logs <container-name> 2>&1 | grep -i error
```

#### Key Log Patterns
- `Twenty webhook received: event=X` - Webhook received
- `Triggering sync to Chatwoot` - Sync started
- `Failed to sync contact` - Sync error (check Chatwoot connectivity)
- `Signature verification: expected=...` - Signature debug info

### Scaling Considerations

- **Contact Sync:** Runs as BackgroundTask (async), limited by Chatwoot API rate limits
- **Full Clinic Sync:** Iterates up to 100 contacts per batch
- **Message Routing:** Currently synchronous within BackgroundTask
- **WhatsApp:** Single Evolution API instance, single phone number
