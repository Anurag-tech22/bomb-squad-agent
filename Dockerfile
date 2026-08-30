# syntax=docker/dockerfile:1
FROM python:3.11-slim

LABEL org.opencontainers.image.title="Bomb Squad Agent" \
      org.opencontainers.image.description="Autonomous DevOps Zero-Trust Remediation Runtime" \
      org.opencontainers.image.licenses="Apache-2.0"

WORKDIR /app

# Install only the OS packages required at runtime (no git, no build tools)
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Create a dedicated non-root user for least-privilege execution
RUN groupadd --gid 1001 bombsquad \
    && useradd --uid 1001 --gid 1001 --shell /bin/sh --create-home bombsquad

# Install Python dependencies before copying source (preserves Docker layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt || \
    pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ ./src/

# Drop privileges
USER bombsquad

# Expose the FastMCP server port
EXPOSE 8000

# Liveness probe: import the module to verify the server is healthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src.mcp_servers.cache_cleaner_server; print('healthy')" \
    || exit 1

# Default entrypoint
CMD ["python", "-m", "src.mcp_servers.cache_cleaner_server"]
