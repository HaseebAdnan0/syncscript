# syntax=docker/dockerfile:1.4
# SyncScript Backend - Multi-stage Docker Build
# Django 6.0 + Channels + Daphne ASGI Server

# =============================================================================
# STAGE 1: Builder - Install Python dependencies
# =============================================================================
FROM python:3.12-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /build/wheels -r requirements.txt

# =============================================================================
# STAGE 2: Runtime - Final production image
# =============================================================================
FROM python:3.12-slim-bookworm AS runtime

LABEL org.opencontainers.image.source="https://github.com/HaseebAdnan0/syncscript"
LABEL org.opencontainers.image.description="SyncScript - Collaborative Research & Citation Engine"
LABEL org.opencontainers.image.licenses="Proprietary"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_HOME=/app \
    APP_USER=syncscript \
    DJANGO_SETTINGS_MODULE=config.settings

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client library
    libpq5 \
    # PDF processing (for pdf2image)
    poppler-utils \
    # Image processing
    libjpeg62-turbo \
    libpng16-16 \
    # Health check and debugging tools
    curl \
    netcat-openbsd \
    # libmagic for file type detection
    libmagic1 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 ${APP_USER} \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash ${APP_USER}

WORKDIR ${APP_HOME}

# Copy wheels from builder and install
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY --chown=${APP_USER}:${APP_USER} . .

# Create necessary directories
RUN mkdir -p ${APP_HOME}/staticfiles \
    ${APP_HOME}/media \
    ${APP_HOME}/logs \
    && chown -R ${APP_USER}:${APP_USER} ${APP_HOME}

# Copy and set permissions for entrypoint script
COPY --chmod=755 docker/scripts/entrypoint.sh /entrypoint.sh

# Switch to non-root user
USER ${APP_USER}

# Expose Daphne port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]

# Default command: Run Daphne ASGI server
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]
