group "default" {
  targets = ["backend", "frontend"]
}

target "backend" {
  context = "./backend"
  dockerfile = "./backend/Dockerfile"
  tags = [
    "backend:${IMAGE_TAG}",
    "backend:latest"
  ]
  platforms = ["linux/amd64"]
  cache-from = ["type=gha,scope=backend"]
  cache-to = ["type=gha,scope=backend,mode=max"]
}

target "frontend" {
  context = "./frontend"
  dockerfile = "./frontend/Dockerfile"
  tags = [
    "frontend:${IMAGE_TAG}",
    "frontend:latest"
  ]
  platforms = ["linux/amd64"]
  cache-from = ["type=gha,scope=frontend"]
  cache-to = ["type=gha,scope=frontend,mode=max"]
}
