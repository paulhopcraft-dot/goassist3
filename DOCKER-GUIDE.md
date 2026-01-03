# Docker Deployment Guide

## Quick Start

### 1. Production Deployment

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f goassist

# Check health
curl http://localhost:8000/health

# Open test client
open http://localhost:8080
```

### 2. Development Mode

```bash
# Start with dev overrides (live reload, mocks)
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Access services:
# - API: http://localhost:8000
# - Test Client: http://localhost:8080
# - Jaeger UI: http://localhost:16686
# - Mock LLM: http://localhost:8001
```

### 3. Stop Everything

```bash
docker-compose down

# Remove volumes too
docker-compose down -v
```

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Core
ENVIRONMENT=production
MAX_CONCURRENT_SESSIONS=100

# LLM (Required)
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4

# ASR
ASR_MODEL_PATH=/models/whisper-large-v3

# TTS
TTS_ENGINE=mock  # or 'coqui', 'bark'

# Avatar (Optional)
ENABLE_AVATAR=false
AUDIO2FACE_GRPC_URL=audio2face:50051

# Security
CSRF_ENABLED=true

# Observability
OTLP_ENDPOINT=http://jaeger:4318

# Models directory (local path)
MODEL_DIR=/path/to/your/models
```

---

## Services

### GoAssist API (`goassist`)

**Ports:**
- 8000: API server

**Health Check:**
```bash
curl http://localhost:8000/health
```

**Logs:**
```bash
docker-compose logs -f goassist
```

**Restart:**
```bash
docker-compose restart goassist
```

### Jaeger Tracing (`jaeger`)

**Ports:**
- 16686: Jaeger UI
- 4318: OTLP HTTP
- 4317: OTLP gRPC

**Access:**
```bash
open http://localhost:16686
```

**View Traces:**
1. Open Jaeger UI
2. Select "goassist" service
3. Click "Find Traces"

### Test Client (`test-client`)

**Ports:**
- 8080: Web client

**Access:**
```bash
open http://localhost:8080
```

Simple nginx server hosting `examples/web-client/`.

---

## Building

### Build Image

```bash
# Build without cache
docker-compose build --no-cache

# Build specific service
docker-compose build goassist
```

### Multi-platform Build

```bash
# For ARM64 (Apple Silicon, AWS Graviton)
docker buildx build --platform linux/arm64 -t goassist:latest .

# For AMD64 (Intel/AMD)
docker buildx build --platform linux/amd64 -t goassist:latest .

# Both
docker buildx build --platform linux/amd64,linux/arm64 -t goassist:latest .
```

---

## Production Deployment

### Docker Compose (Simple)

```bash
# Start production stack
docker-compose up -d

# Scale horizontally
docker-compose up -d --scale goassist=3

# Behind nginx/traefik for load balancing
```

### Kubernetes (Recommended for Production)

```bash
# See k8s/ directory (to be created)
kubectl apply -f k8s/
```

---

## Troubleshooting

### Container won't start

**Check logs:**
```bash
docker-compose logs goassist
```

**Common issues:**
- Missing LLM_API_KEY in .env
- Port 8000 already in use
- Model path not mounted correctly

**Solution:**
```bash
# Check environment
docker-compose config

# Rebuild
docker-compose build --no-cache
docker-compose up
```

### Health check failing

**Check health endpoint:**
```bash
docker-compose exec goassist curl localhost:8000/health
```

**Check dependencies:**
```bash
# Is LLM reachable?
docker-compose exec goassist curl $LLM_BASE_URL/models

# Is Jaeger reachable?
docker-compose exec goassist curl http://jaeger:4318
```

### Can't connect to API from host

**Check container is running:**
```bash
docker-compose ps
```

**Check port mapping:**
```bash
docker-compose port goassist 8000
```

**Test from inside container:**
```bash
docker-compose exec goassist curl localhost:8000/health
```

### Test client can't reach API

**CORS issue:**

If test client is on different domain, add CORS middleware.

**Network issue:**

```bash
# Check networks
docker network ls
docker network inspect goassist_goassist-net

# Ensure goassist and test-client are on same network
```

### High memory usage

**Check container stats:**
```bash
docker stats goassist-api
```

**Set memory limits:**
```yaml
# In docker-compose.yml
services:
  goassist:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

---

## Development Workflow

### Live Reload

Development mode mounts source code:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Edit src/main.py
# Server auto-reloads
```

### Run Tests in Container

```bash
# Enter container
docker-compose exec goassist bash

# Run tests
pytest
```

### Debug Container

```bash
# Shell into running container
docker-compose exec goassist bash

# Check environment
env | grep LLM

# Check Python packages
pip list

# Check file permissions
ls -la /app
```

---

## Performance Tuning

### Uvicorn Workers

For production, use multiple workers:

```dockerfile
# In Dockerfile, change CMD to:
CMD ["gunicorn", "src.main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000"]
```

### Resource Limits

```yaml
# docker-compose.yml
services:
  goassist:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

---

## Monitoring

### Health Checks

Built-in Docker health check:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 5s
  retries: 3
```

### Logs

```bash
# Follow logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f goassist

# Export logs
docker-compose logs > logs.txt
```

### Metrics (Jaeger)

Access Jaeger UI at http://localhost:16686:

1. View request traces
2. See latency distributions
3. Find slow requests
4. Debug errors

---

## CI/CD Integration

### Build in CI

```yaml
# .github/workflows/docker.yml
- name: Build Docker image
  run: docker build -t goassist:${{ github.sha }} .

- name: Test
  run: |
    docker run goassist:${{ github.sha }} pytest

- name: Push to registry
  run: |
    docker tag goassist:${{ github.sha }} registry/goassist:latest
    docker push registry/goassist:latest
```

---

## Next Steps

1. **Test locally:**
   ```bash
   docker-compose up
   open http://localhost:8080
   ```

2. **Configure real models:**
   - Set LLM_API_KEY
   - Mount model directory
   - Test voice conversation

3. **Deploy to production:**
   - Use docker-compose.yml
   - Set ENVIRONMENT=production
   - Configure proper secrets management
   - Set up monitoring/alerts

4. **Scale horizontally:**
   ```bash
   docker-compose up -d --scale goassist=5
   ```
