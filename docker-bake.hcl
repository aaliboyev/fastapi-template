variable "DOCKER_IMAGE" { default = "fastapi-template/api" }
variable "TAG"          { default = "latest" }

# Reuse common context/dockerfile
target "base-common" {
  context    = "."
  dockerfile = "Dockerfile"
}

# --- Canonical targets (no output; good for CI + --push) ---
target "app" {
  inherits = ["base-common"]
  target   = "runtime"
  tags     = ["${DOCKER_IMAGE}:${TAG}"]
  # For CI multi-arch; leave output unset and use --push
  platforms = ["linux/amd64", "linux/arm64"]

  # Optional cross-run cache (uncomment when you have a registry cache)
  # cache-from = ["type=registry,ref=${DOCKER_IMAGE}:buildcache"]
  # cache-to   = ["type=registry,ref=${DOCKER_IMAGE}:buildcache,mode=max"]
}

target "migrate" {
  inherits = ["base-common"]
  target   = "migrate"
  tags     = ["${DOCKER_IMAGE}:${TAG}-migrate"]
  platforms = ["linux/amd64", "linux/arm64"]
  # cache-from / cache-to like above if desired
}

# --- Local dev variants (single-arch, load into daemon) ---
target "app-local" {
  inherits  = ["app"]
  output    = ["type=docker"]       # makes image show up in `docker images`
}

target "migrate-local" {
  inherits  = ["migrate"]
  output    = ["type=docker"]
}

# Groups
group "default" {   # `docker buildx bake` → local dev images loaded
  targets = ["app-local", "migrate-local"]
}

group "ci" {        # `docker buildx bake ci --push` → multi-arch pushed
  targets = ["app", "migrate"]
}
