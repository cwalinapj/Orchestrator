# Agent Guidelines

This document defines the rules and constraints for AI agents operating in this repository.

## Agent Responsibilities

Agents:
- Receive scoped instructions
- May propose diffs
- Must obey this `AGENTS.md` document
- Must stop on validation failure

## Agent Restrictions

Agents do NOT:
- Make architectural decisions
- Bypass invariants
- Execute side effects outside the repo

## Preflight Requirements

Before any task is considered complete, agents MUST run:

```bash
./scripts/validate_all.sh
```

Agents must not proceed if validation fails.

## Execution Model

- A pull request is the smallest executable unit
- A PR may contain one or more logical tasks
- Tasks must be idempotent and independently validatable
