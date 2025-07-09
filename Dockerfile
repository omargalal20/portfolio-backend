# ─── Stage 1: Builder ─────────────────────────────────────────
FROM python:3.13-alpine AS builder
RUN apk add --no-cache build-base libffi-dev openssl-dev musl-dev

WORKDIR /build
COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

COPY app app
COPY gunicorn.conf.py entrypoint.sh ./
RUN chmod +x entrypoint.sh && python -m compileall -q app

# ─── Stage 2: Runtime ─────────────────────────────────────────
FROM python:3.13-alpine
RUN apk add --no-cache libffi openssl  # only runtime libs
WORKDIR /app

COPY --from=builder /install /usr/local
COPY --from=builder /build/app ./app
COPY --from=builder /build/entrypoint.sh ./entrypoint.sh
COPY --from=builder /build/gunicorn.conf.py ./gunicorn.conf.py

ENTRYPOINT ["/bin/sh", "/app/entrypoint.sh"]
