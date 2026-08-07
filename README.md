# AI Factory

An autonomous AI system that designs, builds, tests, deploys, and improves other AI agents and automated systems.

## Phase 1 — Factory Core

The first milestone establishes a dependency-free orchestration core:

- **FactoryJob** — tracks an AI-system build request and its lifecycle.
- **PlanStep** — represents an executable factory step and its agent role.
- **FactoryOrchestrator** — coordinates the lifecycle and isolates provider-specific integrations.
- **Baseline planner** — creates a deterministic specification → build → test → improve plan.
- **CLI** — accepts a natural-language goal and prints the generated plan.

### Project structure

```text
factory/
├── __init__.py
├── main.py
└── core/
    ├── __init__.py
    ├── models.py
    ├── orchestrator.py
    └── planner.py
```

### Run

```bash
python -m factory.main "Build an AI assistant that summarizes YouTube videos"
```

## Roadmap

1. Core orchestration ✅
2. Agent specification and memory
3. LLM provider abstraction
4. Code builder
5. Automated test runner
6. Self-improvement loop
7. Deployment adapters
8. GitHub project automation
9. Monitoring and autonomous iteration

The architecture is intentionally modular so the factory can evolve from a deterministic local prototype into an autonomous multi-agent system without locking the project to a single model provider.
