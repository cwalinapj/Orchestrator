# Orchestrator

This repository operates as a **deterministic orchestration system**.

AI agents are treated as workers.
Validation scripts act as contract enforcement.
Pull requests are execution units.

## Quick Start

Before any task is considered complete, agents MUST run:

```bash
./scripts/validate_all.sh
```

## Documentation

- [AGENTS.md](AGENTS.md) - Guidelines for AI agents operating in this repository
- [Orchestrator Model](docs/orchestrator-model.md) - Detailed documentation of the orchestration system
