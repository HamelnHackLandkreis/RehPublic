# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install uv
RUN pip install uv

# Set the working directory in the container
WORKDIR /app

# Copy the entire project context
COPY . .

# Install the project and its dependencies
# The '.' installs the project defined in pyproject.toml in the current directory
RUN uv pip install --system .

# Expose the port the app runs on
EXPOSE 8000

# Run the application
# Use 0.0.0.0 to make it accessible from outside the container
# --reload is removed for production
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
