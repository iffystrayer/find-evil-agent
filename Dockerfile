# Dockerfile for Find Evil Agent

FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install basic system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for rapid dependency resolution
RUN pip install uv

# Copy project definition and source code
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY tools/ ./tools/

# Install project dependencies onto system Python via uv
RUN uv pip install --system -e .

# Expose ports for Web (17000) and API (18000)
EXPOSE 17000 18000

# Default to starting the Gradio Web Interface
CMD ["python", "-m", "find_evil_agent.cli.main", "web", "--host", "0.0.0.0", "--port", "17000"]
