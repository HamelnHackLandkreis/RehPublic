variable "IMAGE_TAG" {
  default = "latest"
}

variable "REGISTRY" {
  default = ""
}

group "default" {
  targets = ["backend", "frontend"]
}

target "backend" {
  context = "./backend"
  dockerfile = "Dockerfile"
  tags = [
    "${REGISTRY}backend:${IMAGE_TAG}",
    "${REGISTRY}backend:latest"
  ]
  platforms = ["linux/amd64"]
  cache-from = [
    "type=gha,scope=backend",
    "type=registry,ref=${REGISTRY}backend:buildcache"
  ]
  cache-to = [
    "type=gha,scope=backend,mode=max",
    "type=inline"
  ]
  args = {
    BUILDKIT_INLINE_CACHE = "1"
  }
}

target "frontend" {
  context = "./frontend"
  dockerfile = "Dockerfile"
  tags = [
    "${REGISTRY}frontend:${IMAGE_TAG}",
    "${REGISTRY}frontend:latest"
  ]
  platforms = ["linux/amd64"]
  cache-from = [
    "type=gha,scope=frontend",
    "type=registry,ref=${REGISTRY}frontend:buildcache"
  ]
  cache-to = [
    "type=gha,scope=frontend,mode=max",
    "type=inline"
  ]
  args = {
    BUILDKIT_INLINE_CACHE = "1"
  }
}

target "celery-worker" {
  inherits = ["backend"]
  dockerfile = "Dockerfile.celery"
  tags = [
    "${REGISTRY}celery-worker:${IMAGE_TAG}",
    "${REGISTRY}celery-worker:latest"
  ]
}
