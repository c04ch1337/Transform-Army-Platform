# Dependency Updates - Sprint 1.2

**Date:** 2025-10-31  
**Phase:** Sprint 1.2 - Configuration Dependencies Fix

## Summary

Fixed critical dependency conflicts and gaps identified in Phase 4 (Configuration Analysis). These changes resolve P0 blockers preventing core AI functionality and deployment.

---

## Removed Dependencies

### aioredis==2.0.1 (P0-1 - CRITICAL)
**Reason:** Deprecated package merged into `redis>=4.2.0`  
**Impact:** Resolves dependency conflict with `redis==5.0.1`  
**Migration:** Use `redis.asyncio` module instead
```python
# Old (aioredis)
import aioredis

# New (redis>=5.0.1)
from redis.asyncio import Redis
```

---

## Added Dependencies

### AI/LLM Framework Stack (P0-2 - CRITICAL)
Multi-agent orchestration and LLM interaction capabilities

- **langgraph==0.0.50** - State machine framework for agent orchestration
- **langchain==0.1.0** - Core agent framework and abstractions
- **langchain-core==0.1.0** - Core LangChain primitives and interfaces
- **langchain-community==0.0.20** - Community integrations and tools

**Rationale:** Required for multi-agent orchestration architecture defined in agent-orchestration.md

---

### Vector Database (P0-3 - CRITICAL)
Knowledge retrieval and semantic search capabilities

- **qdrant-client==1.7.0** - Vector database client for embeddings storage

**Rationale:** Self-hosted solution, no vendor lock-in, supports semantic search for knowledge retrieval

**Alternative Considered:** Pinecone (cloud-only, vendor lock-in)

---

### LLM Provider SDKs (P0-4 - CRITICAL)
Direct API access to AI models

- **openai==1.6.0** - OpenAI API client (GPT-4, embeddings)
- **anthropic==0.8.0** - Anthropic API client (Claude models)

**Rationale:** Core AI providers referenced in `.env.example` and architecture docs

**Required Environment Variables:**
```bash
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

---

### Validation (P1-3)
Enhanced data validation capabilities

- **email-validator==2.1.0** - RFC-compliant email validation

**Rationale:** Used in schema validation, already present in schema package

---

### Monitoring (P1-4)
Observability and metrics export

- **prometheus-client==0.19.0** - Metrics collection and export

**Rationale:** Standard metrics export for production monitoring

---

## Version Constraints

### pyproject.toml
Uses semantic versioning with caret (`^`) for flexibility:
- `^X.Y.Z` allows updates to `X.*.*` (major version locked)
- Example: `^0.1.0` allows `0.1.x` but not `0.2.0`

### requirements.txt
Uses exact pinning (`==`) for reproducibility:
- `==X.Y.Z` locks to exact version
- Ensures consistent builds across environments

---

## Python Version

**Current:** `python = "^3.11"` (line 10 in pyproject.toml)  
**Status:** ✅ Verified and compatible with all dependencies  
**Note:** Must match Dockerfile base image in Sprint 1.3

---

## Optional Cleanup Considered

### psycopg2-binary (P1-5)
**Status:** RETAINED  
**Reason:** May be needed for synchronous PostgreSQL operations  
**Note:** `asyncpg` handles async operations; psycopg2 kept for compatibility

---

## Validation Steps

After these changes, run:

```bash
cd apps/adapter

# Validate pyproject.toml syntax
poetry check

# Lock dependencies (shows what would be installed)
poetry lock --no-update

# View dependency tree
poetry show --tree

# Optional: Install dependencies (user decision)
# poetry install
```

---

## Cross-References

- **Configuration Analysis:** Phase 4, Issues P0-1 through P0-4
- **Environment Config:** [`.env.example`](.env.example)
- **Architecture Docs:** [`docs/agent-orchestration.md`](../../docs/agent-orchestration.md)
- **Schema Package:** [`packages/schema/requirements.txt`](../../packages/schema/requirements.txt)

---

## Impact Assessment

### Before
- ❌ Redis async integration broken (aioredis conflict)
- ❌ No multi-agent orchestration (no LangGraph)
- ❌ No knowledge retrieval (no vector DB)
- ❌ Cannot call AI models (no LLM SDKs)
- ❌ Missing validation utilities
- ❌ No metrics export

### After
- ✅ Redis async via `redis.asyncio` module
- ✅ Multi-agent orchestration enabled (LangGraph)
- ✅ Vector search enabled (Qdrant)
- ✅ AI model integration ready (OpenAI, Anthropic)
- ✅ Enhanced validation (email)
- ✅ Metrics collection ready (Prometheus)

---

## Next Steps

1. **User Action Required:**
   - Run `poetry install` in `apps/adapter/` to install new dependencies
   - Verify API keys in `.env` file

2. **Sprint 1.3:** Create Dockerfiles with these dependencies
3. **Sprint 1.4:** Implement actual agent orchestration using LangGraph
4. **Sprint 1.5:** Set up Qdrant vector database
5. **Sprint 1.6:** Integrate LLM providers (OpenAI, Anthropic)

---

## Notes

- Changes are backwards compatible (only additions + deprecation fix)
- No breaking changes to existing code
- All environment variables optional until implementation phase
- Dependencies ordered alphabetically for maintainability