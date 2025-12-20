# syntax=docker/dockerfile:1.4

# Build stage - install dependencies and build artifacts
FROM python:3.13-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock* README.md ./
COPY src/wildlife_processor/__init__.py src/wildlife_processor/
COPY src/api/__init__.py src/api/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system --no-cache .

# Runtime stage - smaller final image
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV MODEL_PATH=/app/models/deepfaune-vit_large_patch14_dinov2.lvd142m.v4.pt

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libgomp1 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

RUN python download_deepfaune_model.py || \
    (echo "WARNING: Failed to download model. It will be attempted at runtime." && exit 0)

RUN python -c "import PytorchWildlife; print('PyTorch Wildlife installed successfully')" || \
    (echo "ERROR: PyTorch Wildlife installation failed!" && exit 1)

RUN find /usr/local/lib/python3.13 -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true && \
    find /usr/local/lib/python3.13 -type f -name "*.pyc" -delete && \
    find /usr/local/lib/python3.13 -type f -name "*.pyo" -delete

EXPOSE 8000

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
