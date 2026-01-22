# Iframe Embedding Configuration

## Problem

The shell app at `medflow.trafegoparaconsultorios.com.br` embeds external services via iframes.
Each service must allow being framed by the shell domain.

## Required Traefik Labels (Coolify)

For each service in Coolify, add these Traefik labels to replace X-Frame-Options:

### Twenty CRM

```
traefik.http.middlewares.twenty-frame.headers.customResponseHeaders.X-Frame-Options=
traefik.http.middlewares.twenty-frame.headers.contentSecurityPolicy=frame-ancestors 'self' https://medflow.trafegoparaconsultorios.com.br
traefik.http.routers.twenty.middlewares=twenty-frame
```

### Chatwoot

```
traefik.http.middlewares.chatwoot-frame.headers.customResponseHeaders.X-Frame-Options=
traefik.http.middlewares.chatwoot-frame.headers.contentSecurityPolicy=frame-ancestors 'self' https://medflow.trafegoparaconsultorios.com.br
traefik.http.routers.chatwoot.middlewares=chatwoot-frame
```

### Cal.com

```
traefik.http.middlewares.calcom-frame.headers.customResponseHeaders.X-Frame-Options=
traefik.http.middlewares.calcom-frame.headers.contentSecurityPolicy=frame-ancestors 'self' https://medflow.trafegoparaconsultorios.com.br
traefik.http.routers.calcom.middlewares=calcom-frame
```

## Alternative: Service-Level Configuration

### Twenty CRM
Set environment variable:
```
FRONT_ALLOW_IFRAMES=true
```

### Chatwoot
In Chatwoot's config, no built-in iframe support. Must use Traefik middleware.

### Cal.com
Cal.com has native embed support via `cal.com/embed`. Can use embed URLs instead of full UI:
```
/embed/brian/15min  # Embeddable booking page
```

## Implementation

These labels need to be added in Coolify's UI for each service:
1. Go to Coolify → Project → Service
2. Edit the service configuration
3. Add the Traefik labels to the Docker labels section
4. Redeploy the service
