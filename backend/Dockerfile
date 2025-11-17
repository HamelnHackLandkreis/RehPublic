# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV MODEL_PATH=/app/models/deepfaune-vit_large_patch14_dinov2.lvd142m.v4.pt

# Install system dependencies required for PyTorch and PyTorch Wildlife
# This layer is cached unless system dependencies change
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install uv (cached unless uv version changes)
RUN pip install --no-cache-dir uv

# Set the working directory in the container
WORKDIR /app

# Copy dependency files and minimal project structure for installation
# These files change less frequently than application code
COPY pyproject.toml uv.lock* README.md ./
COPY src/wildlife_processor/__init__.py src/wildlife_processor/
COPY src/api/__init__.py src/api/

# Install dependencies and project
# This layer is cached unless dependency files or package structure changes
RUN uv pip install --system --no-cache .

# Verify pytorchwildlife is installed (fail build if not available)
RUN python -c "import PytorchWildlife; print('PyTorch Wildlife installed successfully')" || \
    (echo "ERROR: PyTorch Wildlife installation failed!" && exit 1)

# Copy the rest of the application code
# This is done last so code changes don't invalidate the dependency cache
# Use .dockerignore to exclude unnecessary files (node_modules, __pycache__, etc.)
COPY . .

# Download the DeepFaune v4 model during build
# This ensures the model is available when the container starts
RUN python download_deepfaune_model.py || \
    (echo "WARNING: Failed to download model. It will be attempted at runtime." && exit 0)

# Expose the port the app runs on
EXPOSE 8000

# Run the application
# Use 0.0.0.0 to make it accessible from outside the container
# --reload is removed for production
# --proxy-headers enables X-Forwarded-* header support for HTTPS redirect handling
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--app-dir", "/app/src"]
