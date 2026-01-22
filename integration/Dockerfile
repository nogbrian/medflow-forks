# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy Python packages from builder
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Cache buster for forced rebuilds
ARG BUILD_VERSION=1
ENV BUILD_VERSION=${BUILD_VERSION}

# Copy application code
COPY . .

# Make startup script executable
RUN chmod +x startup.sh

# Fix ownership
RUN chown -R appuser:appuser /app /home/appuser/.local

# Security: Drop privileges
USER appuser

# Health check - increased start-period for slow initialization
HEALTHCHECK --interval=60s --timeout=30s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Use startup script that seeds the database and starts the app
CMD ["./startup.sh"]
