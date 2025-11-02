# Transform Army AI Platform

> Enterprise-grade multi-agent AI platform for business transformation

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/transform-army-ai/platform)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![CI Status](https://img.shields.io/badge/CI-passing-brightgreen.svg)](https://github.com/transform-army-ai/platform/actions)
[![Coverage](https://img.shields.io/badge/coverage-85%25-green.svg)](https://codecov.io/gh/transform-army-ai/platform)
[![Security](https://img.shields.io/badge/security-A+-brightgreen.svg)](https://github.com/transform-army-ai/platform/security)
[![API Docs](https://img.shields.io/badge/API-docs-orange.svg)](https://api.transform-army.ai/docs)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)

Transform Army AI is a white-label business transformation platform that provides multi-agent AI capabilities through a strategic phased migration architecture, offering vendor-agnostic APIs, enterprise-grade security, and comprehensive observability.

## ✨ Key Features

- 🤖 **6 Specialized AI Agents**: BDR, Support, Research, Ops, Knowledge Librarian, QA
- 🔒 **Enterprise Security**: Multi-tenant with row-level security, API key auth, rate limiting
- 🔄 **Vendor-Agnostic**: Seamless provider switching (HubSpot, Salesforce, Zendesk, Google, etc.)
- ⚡ **High Performance**: Async operations, connection pooling, Redis caching
- 📊 **Complete Observability**: Structured logging, metrics, distributed tracing
- 🛡️ **Production-Ready**: Automatic retries, circuit breakers, health checks
- 📚 **Excellent DX**: Interactive docs, SDKs, code examples, comprehensive guides

## 🚀 Quick Start

### Prerequisites

- **Python** 3.11+ ([download](https://www.python.org/downloads/))
- **Node.js** 18+ and pnpm ([install pnpm](https://pnpm.io/installation))
- **Docker** and Docker Compose ([install](https://docs.docker.com/get-docker/))
- **PostgreSQL** 15+ (or use Docker)
- **Redis** 7+ (or use Docker)

### Installation

```bash
# Clone the repository
git clone https://github.com/transform-army-ai/platform.git
cd platform

# Install dependencies
pnpm install

# Copy environment files
cp .env.example .env
cp apps/adapter/.env.example apps/adapter/.env

# Configure your environment variables
# Edit .env and apps/adapter/.env with your settings

# Start infrastructure (PostgreSQL, Redis)
docker-compose -f infra/compose/docker-compose.dev.yml up -d

# Run database migrations
cd apps/adapter
poetry install
poetry run alembic upgrade head

# Start the adapter service
poetry run uvicorn src.main:app --reload

# In another terminal, start the web app
cd apps/web
pnpm dev
```

### Verify Installation

```bash
# Check API health
curl http://localhost:8000/health/

# View interactive API docs
open http://localhost:8000/docs

# Access web console
open http://localhost:3000
```

## 📖 Architecture

Transform Army AI follows a microservices architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                     Transform Army AI                        │
├─────────────────────────────────────────────────────────────┤
│  Web Console (Next.js)          API Explorer               │
│  ├─ Dashboard                   ├─ Swagger UI               │
│  ├─ Agent Config                ├─ ReDoc                    │
│  └─ Analytics                   └─ Interactive Testing      │
├─────────────────────────────────────────────────────────────┤
│               Adapter Service (FastAPI)                      │
│  ├─ REST API (vendor-agnostic)                             │
│  ├─ Provider System (pluggable)                            │
│  ├─ Workflow Engine                                        │
│  └─ Security & Observability                               │
├─────────────────────────────────────────────────────────────┤
│                  External Integrations                       │
│  CRM: HubSpot, Salesforce                                   │
│  Helpdesk: Zendesk, Intercom                               │
│  Calendar: Google, Outlook                                  │
│  Email: Gmail, SendGrid                                     │
│  LLM: OpenAI, Anthropic, Cohere                            │
└─────────────────────────────────────────────────────────────┘
```

For detailed architecture documentation, see [`ARCHITECTURE.md`](ARCHITECTURE.md).

## 📚 Phase Migration Strategy

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

## 📚 Documentation

### API Documentation
- 📖 **[API Guide](docs/API_GUIDE.md)** - Comprehensive integration guide with examples
- 📚 **[API Reference](docs/API_REFERENCE.md)** - Complete endpoint catalog with schemas
- 💻 **[SDK Examples](docs/SDK_EXAMPLES.md)** - Python, TypeScript, JavaScript examples
- 🔔 **[Webhooks Guide](docs/WEBHOOKS.md)** - Real-time event notifications
- 📋 **[API Changelog](docs/API_CHANGELOG.md)** - Version history and migration guides
- 🌐 **[Interactive Docs](http://localhost:8000/docs)** - Swagger UI (when running)

### Architecture & Guides
- 🏗️ **[Architecture Overview](ARCHITECTURE.md)** - System design and components
- 🔌 **[Adapter Contract](docs/adapter-contract.md)** - Provider integration specification
- 🤖 **[Agent Orchestration](docs/agent-orchestration.md)** - Multi-agent workflows
- 🚀 **[Deployment Guide](docs/deployment-guide.md)** - Production deployment
- 🔒 **[Security Guide](docs/SECURITY.md)** - Security implementation details
- 📊 **[Monitoring](docs/MONITORING.md)** - Observability and metrics
- 🧪 **[Testing Guide](docs/TESTING.md)** - Testing strategies

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

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** with tests and documentation
4. **Run quality checks**:
   ```bash
   make lint        # Run linters
   make test        # Run tests
   make type-check  # Type checking
   ```
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Guidelines

- Write tests for new features
- Update documentation
- Follow code style conventions
- Add type hints (Python) / types (TypeScript)
- Keep commits atomic and well-described
- Ensure CI passes before requesting review

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 🆘 Support & Community

### Get Help
- 📖 **Documentation**: [docs.transform-army.ai](https://docs.transform-army.ai)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/transform-army-ai/platform/discussions)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/transform-army-ai/platform/issues)
- 📧 **Email**: support@transform-army.ai
- 💼 **Enterprise Support**: enterprise@transform-army.ai

### Stay Updated
- ⭐ **Star this repo** to follow updates
- 🔔 **Watch releases** for new versions
- 📰 **Newsletter**: [Subscribe](https://transform-army.ai/newsletter)
- 🐦 **Twitter**: [@TransformArmyAI](https://twitter.com/TransformArmyAI)

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses

This project uses several open-source libraries. See [LICENSES.md](LICENSES.md) for details.

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Next.js](https://nextjs.org/) - React framework for production
- [LangChain](https://langchain.com/) - LLM application framework
- [Pydantic](https://pydantic.dev/) - Data validation
- [PostgreSQL](https://www.postgresql.org/) - Robust database
- [Redis](https://redis.io/) - In-memory data structure store

Special thanks to all our [contributors](https://github.com/transform-army-ai/platform/graphs/contributors)!

## 🗺️ Roadmap

### v1.1.0 (Q1 2025)
- [ ] Additional CRM providers (Pipedrive, Close.com)
- [ ] Webhook support for real-time events
- [ ] Batch operations
- [ ] GraphQL API

### v1.2.0 (Q2 2025)
- [ ] Advanced workflow features (conditionals, loops)
- [ ] Custom integration plugins
- [ ] Real-time data synchronization
- [ ] Analytics dashboard

### v2.0.0 (Q4 2025)
- [ ] Breaking changes with migration guide
- [ ] Enhanced performance and scalability
- [ ] New AI capabilities

See [API_CHANGELOG.md](docs/API_CHANGELOG.md) for detailed version history.

---

<div align="center">

**Status**: 🟢 Production Ready | **Version**: v1.0.0 | **Last Updated**: 2025-10-31

Made with ⚡ by the Transform Army team

[Website](https://transform-army.ai) · [Documentation](https://docs.transform-army.ai) · [API Reference](https://api.transform-army.ai/docs) · [Support](mailto:support@transform-army.ai)

</div>