# GoAssist3 - Technical Master File (TMF)

## Document Control
| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-22 | - | Initial draft |

---

## 1. System Overview

### 1.1 Purpose
This Technical Master File documents the complete technical architecture, design decisions, and implementation details for GoAssist3 - a domain-configurable AI/LLM assistant platform.

### 1.2 Scope
This document covers:
- System architecture and design
- Technology stack decisions
- Component specifications
- Data architecture
- Security architecture
- Integration specifications
- Operational procedures

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Load Balancer / Ingress                        │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
┌─────────────────────────────────┴───────────────────────────────────────┐
│                              API Gateway                                 │
│                    (Authentication, Rate Limiting, Routing)              │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Chat Service  │    │  Document Svc   │    │ Workflow Engine │
│                 │    │                 │    │                 │
│ - Conversation  │    │ - Upload        │    │ - Task Exec     │
│ - Context Mgmt  │    │ - Processing    │    │ - Scheduling    │
│ - Response Gen  │    │ - Indexing      │    │ - Monitoring    │
└────────┬────────┘    └────────┬────────┘    └────────┬────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM Service   │    │ Embedding Svc   │    │  RAG Service    │
│                 │    │                 │    │                 │
│ - Provider Mgmt │    │ - Text Embed    │    │ - Retrieval     │
│ - Prompt Mgmt   │    │ - Doc Embed     │    │ - Ranking       │
│ - Token Mgmt    │    │ - Batch Process │    │ - Context Build │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
┌───────────────────────────────┴─────────────────────────────────────────┐
│                           Data Layer                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  PostgreSQL │  │   Redis     │  │ Vector DB   │  │ Object Store│    │
│  │  (Primary)  │  │  (Cache)    │  │ (Embeddings)│  │  (Files)    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Architecture Principles

| Principle | Description |
|-----------|-------------|
| Microservices | Loosely coupled, independently deployable services |
| API-First | All functionality exposed via well-defined APIs |
| Cloud-Native | Designed for containerized, Kubernetes deployment |
| Event-Driven | Async communication via message queues where appropriate |
| Security by Design | Security considered at every layer |

---

## 3. Technology Stack

### 3.1 Stack Decision Matrix

| Component | Options Considered | Selected | Rationale |
|-----------|-------------------|----------|-----------|
| Backend Language | Go, Python, Node.js | TBD | - |
| Web Framework | Gin, FastAPI, Express | TBD | - |
| Database | PostgreSQL, MySQL | PostgreSQL | JSONB support, extensions |
| Cache | Redis, Memcached | Redis | Pub/sub, persistence |
| Vector DB | Pinecone, Weaviate, pgvector | TBD | - |
| Message Queue | RabbitMQ, Redis Streams, NATS | TBD | - |
| Object Storage | S3, MinIO, GCS | MinIO/S3 | S3 API compatibility |
| Container Runtime | Docker, containerd | Docker | Tooling ecosystem |
| Orchestration | Kubernetes | Kubernetes | Industry standard |

### 3.2 Recommended Stack Options

#### Option A: Go-Based Stack
```yaml
Backend:
  Language: Go 1.22+
  Framework: Gin / Echo
  ORM: GORM / sqlc

Frontend:
  Framework: React 18+ / Next.js 14+
  State: Zustand / Redux Toolkit
  UI: shadcn/ui / Tailwind CSS

Data:
  Primary DB: PostgreSQL 15+
  Vector DB: pgvector extension
  Cache: Redis 7+
  Queue: NATS / Redis Streams

Infrastructure:
  Container: Docker
  Orchestration: Kubernetes
  Service Mesh: Istio (optional)
```

#### Option B: Python-Based Stack
```yaml
Backend:
  Language: Python 3.11+
  Framework: FastAPI
  ORM: SQLAlchemy 2.0

Frontend:
  Framework: React 18+ / Next.js 14+
  State: Zustand / Redux Toolkit
  UI: shadcn/ui / Tailwind CSS

Data:
  Primary DB: PostgreSQL 15+
  Vector DB: Weaviate / Qdrant
  Cache: Redis 7+
  Queue: Celery + Redis

Infrastructure:
  Container: Docker
  Orchestration: Kubernetes
```

---

## 4. Component Specifications

### 4.1 API Gateway

**Purpose**: Central entry point for all client requests

**Responsibilities**:
- Authentication & authorization
- Rate limiting
- Request routing
- API versioning
- Request/response transformation

**Technology Options**:
- Kong Gateway
- Traefik
- Custom (Go/Python)

**API Versioning Strategy**:
```
/api/v1/chat/...
/api/v1/documents/...
/api/v1/workflows/...
```

### 4.2 Chat Service

**Purpose**: Handle conversational interactions

**Responsibilities**:
- Conversation session management
- Context window management
- Response streaming
- Conversation history storage

**Key Interfaces**:
```
POST   /api/v1/chat/sessions           - Create session
GET    /api/v1/chat/sessions/{id}      - Get session
POST   /api/v1/chat/sessions/{id}/messages - Send message
GET    /api/v1/chat/sessions/{id}/messages - Get history
DELETE /api/v1/chat/sessions/{id}      - End session
```

**Data Model**:
```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL,
    domain_id UUID NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY,
    session_id UUID REFERENCES chat_sessions(id),
    role VARCHAR(20) NOT NULL, -- 'user', 'assistant', 'system'
    content TEXT NOT NULL,
    tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);
```

### 4.3 Document Service

**Purpose**: Handle document upload, processing, and indexing

**Responsibilities**:
- File upload handling
- Document parsing (PDF, DOCX, etc.)
- Text extraction and chunking
- Metadata extraction
- Indexing coordination

**Key Interfaces**:
```
POST   /api/v1/documents               - Upload document
GET    /api/v1/documents               - List documents
GET    /api/v1/documents/{id}          - Get document
DELETE /api/v1/documents/{id}          - Delete document
GET    /api/v1/documents/{id}/content  - Get processed content
POST   /api/v1/documents/{id}/reprocess - Reprocess document
```

**Processing Pipeline**:
```
Upload → Validate → Store → Parse → Chunk → Embed → Index
```

### 4.4 LLM Service

**Purpose**: Abstract LLM provider interactions

**Responsibilities**:
- Multi-provider support (OpenAI, Anthropic, local)
- Prompt template management
- Token counting and management
- Response streaming
- Fallback handling

**Supported Providers**:
| Provider | Models | Priority |
|----------|--------|----------|
| OpenAI | GPT-4, GPT-3.5 | P0 |
| Anthropic | Claude 3 | P0 |
| Local | Ollama, vLLM | P1 |
| Azure OpenAI | GPT-4 | P1 |

### 4.5 RAG Service

**Purpose**: Retrieval Augmented Generation pipeline

**Responsibilities**:
- Query understanding
- Vector similarity search
- Context retrieval and ranking
- Context window optimization
- Source attribution

**RAG Pipeline**:
```
Query → Embed → Search → Rank → Rerank → Build Context → Generate
```

### 4.6 Workflow Engine

**Purpose**: Define and execute automated workflows

**Responsibilities**:
- Workflow definition (DSL/YAML)
- Task execution
- State management
- Scheduling
- Event handling

**Workflow Definition Schema**:
```yaml
workflow:
  name: document_review
  trigger:
    type: event
    event: document.uploaded
  steps:
    - id: extract
      action: extract_content
      input: ${trigger.document_id}
    - id: analyze
      action: llm_analyze
      input: ${steps.extract.output}
      prompt_template: review_template
    - id: notify
      action: send_notification
      input:
        channel: slack
        message: ${steps.analyze.output}
```

---

## 5. Data Architecture

### 5.1 Database Schema Overview

```
┌──────────────────────────────────────────────────────────────┐
│                      Core Entities                           │
├──────────────────────────────────────────────────────────────┤
│  organizations  │  users  │  domains  │  api_keys            │
└──────────────────────────────────────────────────────────────┘
                              │
┌──────────────────────────────────────────────────────────────┐
│                    Feature Entities                          │
├──────────────────────────────────────────────────────────────┤
│  documents  │  chat_sessions  │  workflows  │  tasks         │
│  embeddings │  chat_messages  │  workflow_runs │  events     │
└──────────────────────────────────────────────────────────────┘
```

### 5.2 Data Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Input  │ -> │ Process │ -> │  Store  │ -> │  Index  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘
    │              │              │              │
    │              │              │              │
    ▼              ▼              ▼              ▼
 API/Upload    Transform     PostgreSQL     Vector DB
               & Validate    + S3/MinIO
```

### 5.3 Data Retention

| Data Type | Retention Period | Archive Strategy |
|-----------|-----------------|------------------|
| Chat Messages | 90 days active | Archive to cold storage |
| Documents | Indefinite | Owner-managed |
| Embeddings | Follows document | Delete with document |
| Audit Logs | 2 years | Compressed archive |
| Metrics | 30 days detailed | Aggregated long-term |

---

## 6. Security Architecture

### 6.1 Security Layers

```
┌─────────────────────────────────────────────────────────────┐
│                    Network Security                          │
│         (TLS 1.3, mTLS, Network Policies)                   │
├─────────────────────────────────────────────────────────────┤
│                  Application Security                        │
│    (Authentication, Authorization, Input Validation)         │
├─────────────────────────────────────────────────────────────┤
│                     Data Security                            │
│         (Encryption at Rest, Key Management)                 │
├─────────────────────────────────────────────────────────────┤
│                Infrastructure Security                       │
│       (Container Security, Secret Management)                │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Authentication

**Supported Methods**:
- JWT tokens (default)
- API keys (for service-to-service)
- SAML 2.0 (enterprise SSO)
- OIDC (OAuth 2.0)

**Token Structure**:
```json
{
  "sub": "user_id",
  "org": "organization_id",
  "roles": ["user", "admin"],
  "permissions": ["documents:read", "chat:write"],
  "exp": 1234567890,
  "iat": 1234567890
}
```

### 6.3 Authorization (RBAC)

**Default Roles**:
| Role | Description | Permissions |
|------|-------------|-------------|
| viewer | Read-only access | Read documents, view chats |
| user | Standard access | CRUD own resources |
| admin | Full org access | Manage users, settings |
| super_admin | System access | All permissions |

### 6.4 Data Encryption

| Data State | Encryption Method | Key Management |
|------------|-------------------|----------------|
| In Transit | TLS 1.3 | Cert-manager |
| At Rest (DB) | AES-256 | Vault/KMS |
| At Rest (Files) | AES-256-GCM | Vault/KMS |
| Secrets | Vault/K8s Secrets | Vault |

---

## 7. Integration Specifications

### 7.1 LLM Provider Integration

**Interface Contract**:
```go
type LLMProvider interface {
    Complete(ctx context.Context, req CompletionRequest) (*CompletionResponse, error)
    Stream(ctx context.Context, req CompletionRequest) (<-chan StreamChunk, error)
    Embed(ctx context.Context, texts []string) ([][]float32, error)
    CountTokens(text string) int
}
```

### 7.2 External Integrations

| Integration | Type | Priority | Protocol |
|-------------|------|----------|----------|
| Slack | Notification | P1 | REST/WebSocket |
| Microsoft Teams | Notification | P1 | REST |
| Email (SMTP) | Notification | P0 | SMTP |
| Webhook | Generic | P0 | HTTP POST |
| S3-compatible | Storage | P0 | S3 API |

### 7.3 API Contracts

**OpenAPI Specification**: See `/api/openapi.yaml`

**Response Format**:
```json
{
  "success": true,
  "data": { },
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO8601"
  }
}
```

**Error Format**:
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": { }
  },
  "meta": {
    "request_id": "uuid",
    "timestamp": "ISO8601"
  }
}
```

---

## 8. Observability

### 8.1 Logging

**Log Format** (structured JSON):
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "info",
  "service": "chat-service",
  "trace_id": "abc123",
  "span_id": "def456",
  "message": "Request processed",
  "attributes": {
    "user_id": "user123",
    "duration_ms": 150
  }
}
```

### 8.2 Metrics

**Key Metrics**:
| Metric | Type | Labels |
|--------|------|--------|
| request_duration_seconds | Histogram | service, method, status |
| request_total | Counter | service, method, status |
| active_sessions | Gauge | service |
| llm_tokens_used | Counter | provider, model |
| document_processed | Counter | type, status |

### 8.3 Tracing

**Distributed Tracing**: OpenTelemetry

**Trace Propagation**: W3C Trace Context

---

## 9. Deployment Architecture

See [PARALLEL_DEV_DEPLOY.md](./PARALLEL_DEV_DEPLOY.md) for detailed deployment procedures.

### 9.1 Environment Topology

```
┌─────────────────────────────────────────────────────────────┐
│                     Production                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Region A  │  │   Region B  │  │   Region C  │         │
│  │  (Primary)  │  │ (Secondary) │  │   (DR)      │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                      Staging                                 │
│  ┌─────────────────────────────────────────────────┐       │
│  │              Single Region Replica               │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────┐
│                    Development                               │
│  ┌─────────────────────────────────────────────────┐       │
│  │           Local K8s / Docker Compose             │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 10. Technical Decisions Log

| ID | Date | Decision | Rationale | Status |
|----|------|----------|-----------|--------|
| TD-001 | - | TBD: Backend language selection | - | Pending |
| TD-002 | - | TBD: Vector database selection | - | Pending |
| TD-003 | - | TBD: Message queue selection | - | Pending |

---

## 11. Appendix

### 11.1 Glossary

| Term | Definition |
|------|------------|
| RAG | Retrieval Augmented Generation |
| LLM | Large Language Model |
| Vector DB | Database optimized for vector similarity search |
| Embedding | Dense vector representation of text |
| mTLS | Mutual TLS authentication |

### 11.2 References

- [PRD](./PRD.md)
- [Deployment Guide](./PARALLEL_DEV_DEPLOY.md)
- [API Specification](./api/openapi.yaml)
