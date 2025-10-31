# Transform Army AI Platform

> Multi-agent AI platform for business transformation in services firms and mid-market operations teams

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/transform-army-ai/platform)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Overview

Transform Army AI is a white-label business transformation platform that provides multi-agent AI capabilities through a strategic three-phase migration architecture:

1. **Phase 1**: Relevance AI-native implementation for rapid time-to-market
2. **Phase 2**: Adapter layer introduction for vendor portability
3. **Phase 3**: Hybrid orchestration with LangGraph state machines
4. **Phase 4+**: Fully proprietary platform with on-premise deployment options

## Quick Start

### Prerequisites

- Node.js 18+ and pnpm
- Python 3.11+
- Docker and Docker Compose
- PostgreSQL 15+
- Redis 7+

### Installation

```bash
# Clone the repository
git clone https://github.com/transform-army-ai/platform.git
cd platform

# Install dependencies
pnpm install

# Copy environment variables
cp .env.example .env

# Start development environment
make dev
```

### Development Commands

```bash
make dev          # Start all services in development mode
make test         # Run all tests
make build        # Build all services
make clean        # Clean build artifacts
make lint         # Run linters
make format       # Format code
```

## Architecture

The platform follows a monorepo structure with clear separation of concerns:

```
transform-army-ai/
├── apps/          # Application services
│   ├── web/       # Next.js operator console
│   ├── adapter/   # FastAPI adapter service
│   └── evals/     # QA and evaluation harness
├── packages/      # Shared packages
│   ├── agents/    # Agent definitions
│   ├── tools/     # Vendor-agnostic tool wrappers
│   ├── schema/    # Shared data models
│   └── prompt-pack/ # System prompts
├── infra/         # Infrastructure as Code
└── .cursor/       # AI assistant configuration
```

For detailed architecture documentation, see [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Core Services

### Web Console (`/apps/web`)
Next.js application providing operator dashboard, tenant configuration, and analytics.

### Adapter Service (`/apps/adapter`)
FastAPI service providing vendor-agnostic interfaces for all external integrations.

### Evaluation Harness (`/apps/evals`)
QA and evaluation system for testing agent performance and quality.

## Key Features

- **6 Base Agents**: BDR, Support, Research, Ops, Librarian, QA
- **Multi-Tenant Architecture**: Strict data isolation and RBAC
- **Vendor-Agnostic Design**: Easy provider swapping through adapter contracts
- **Contract-First APIs**: Pydantic/Zod schemas ensure type safety
- **Metered Billing**: Actions/Credits model with BYO LLM key support

## Technology Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend | Next.js | 14+ |
| Backend | FastAPI | 0.109+ |
| Orchestration | LangGraph | 0.0.50+ |
| Database | PostgreSQL | 15+ |
| Vector DB | Pinecone/Weaviate | Latest |
| Cache | Redis | 7+ |

## Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [Adapter Contract Specification](docs/adapter-contract.md)
- [Agent Orchestration Guide](docs/agent-orchestration.md)
- [Deployment Guide](docs/deployment-guide.md)

## Development Workflow

### Running Services Locally

```bash
# Start all services
make dev

# Or start individual services
cd apps/web && pnpm dev
cd apps/adapter && poetry run uvicorn src.main:app --reload
```

### Running Tests

```bash
# Run all tests
make test

# Run specific test suites
cd apps/web && pnpm test
cd apps/adapter && poetry run pytest
cd apps/evals && poetry run pytest
```

### Code Quality

```bash
# Lint all code
make lint

# Format all code
make format

# Type check
pnpm type-check
```

## Deployment

### Development Environment

```bash
cd infra/compose
docker-compose -f docker-compose.dev.yml up
```

### Production Environment

See [Deployment Guide](docs/deployment-guide.md) for detailed production deployment instructions.

## Contributing

1. Create a feature branch from `main`
2. Make your changes with tests
3. Run `make lint` and `make test`
4. Submit a pull request

## Support

- Documentation: [docs/](docs/)
- Issues: GitHub Issues
- Email: support@transform-army.ai

## License

MIT License - see [LICENSE](LICENSE) for details

---

**Status**: Phase 1 - Design & Planning  
**Last Updated**: 2025-10-31