# Deployment Guide

This guide covers bundling and deploying the service in your cloud or network.

## Docker

Create an image and run the service with Redis:

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

# System deps for qrcode/Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libjpeg-dev zlib1g-dev \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /app/
RUN pip install --upgrade pip && pip install poetry && poetry config virtualenvs.create false \
 && poetry install --no-root --only main

COPY . /app

EXPOSE 8000
ENV HOST=0.0.0.0 PORT=8000
CMD ["python", "server/protected_server.py"]
```

Build and run:
```bash
docker build -t ztai-portal .
docker run --rm -p 8000:8000 \
  -e STRIPE_SECRET_KEY={{STRIPE_SECRET_KEY}} \
  -e STRIPE_PRICE_ID={{STRIPE_PRICE_ID}} \
  -e STRIPE_WEBHOOK_SECRET={{STRIPE_WEBHOOK_SECRET}} \
  -e REDIS_URL=redis://redis:6379/0 \
  --name ztai-portal ztai-portal
```

## Docker Compose

```yaml
version: "3.9"
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      STRIPE_SECRET_KEY: ${STRIPE_SECRET_KEY}
      STRIPE_PRICE_ID: ${STRIPE_PRICE_ID}
      STRIPE_WEBHOOK_SECRET: ${STRIPE_WEBHOOK_SECRET}
      STRIPE_MODE: ${STRIPE_MODE:-payment}
      ENABLE_DEV_PAY: ${ENABLE_DEV_PAY:-0}
      RETURN_VERIFICATION_CODE: ${RETURN_VERIFICATION_CODE:-0}
      REDIS_URL: redis://redis:6379/0
    depends_on:
      - redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

Run:
```bash
docker compose up --build
```

For local Stripe webhooks:
```bash
stripe listen --forward-to localhost:8000/pay/webhook
```

## Kubernetes (Helm chart skeleton)

Directory: `deploy/helm/ztai-portal`

- `Chart.yaml`:
```yaml
apiVersion: v2
name: ztai-portal
version: 0.1.0
appVersion: "0.1.0"
```

- `values.yaml`:
```yaml
image: ztai-portal:latest
replicaCount: 1
service:
  type: ClusterIP
  port: 8000
env:
  STRIPE_MODE: payment
  ENABLE_DEV_PAY: "0"
  RETURN_VERIFICATION_CODE: "0"
redis:
  enabled: true
  url: redis://ztai-redis:6379/0
```

- `templates/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ztai-portal
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: ztai-portal
  template:
    metadata:
      labels:
        app: ztai-portal
    spec:
      containers:
        - name: app
          image: {{ .Values.image }}
          ports:
            - containerPort: 8000
          env:
            - name: REDIS_URL
              value: {{ .Values.redis.url | quote }}
            - name: STRIPE_MODE
              value: {{ .Values.env.STRIPE_MODE | quote }}
            - name: ENABLE_DEV_PAY
              value: {{ .Values.env.ENABLE_DEV_PAY | quote }}
            - name: RETURN_VERIFICATION_CODE
              value: {{ .Values.env.RETURN_VERIFICATION_CODE | quote }}
```

- `templates/service.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: ztai-portal
spec:
  type: {{ .Values.service.type }}
  selector:
    app: ztai-portal
  ports:
    - port: {{ .Values.service.port }}
      targetPort: 8000
```

- `templates/ingress.yaml` (optional):
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ztai-portal
spec:
  rules:
    - host: portal.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: ztai-portal
                port:
                  number: 8000
```

## Network/Cloud Bundling
- Place behind your existing API gateway/ingress with TLS termination.
- Restrict `/pay/webhook` to Stripe IPs or rely on signature verification (already implemented) and rate limiting.
- Use Redis (managed) for session durability.
- Set Secure, SameSite, and HttpOnly cookies; terminate HTTPS at the edge.
