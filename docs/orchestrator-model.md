# Repository Orchestrator Model

This repository operates as a **deterministic orchestration system**.

AI agents are treated as workers.
Validation scripts act as contract enforcement.
Pull requests are execution units.

---

## 1. Execution Units

- A pull request is the smallest executable unit
- A PR may contain one or more logical tasks
- Tasks must be idempotent and independently validatable

---

## 2. Worker Model (AI Agents)

Agents:
- Receive scoped instructions
- May propose diffs
- Must obey `AGENTS.md`
- Must stop on validation failure

Agents do NOT:
- Make architectural decisions
- Bypass invariants
- Execute side effects outside the repo

---

## 3. Preflight (Required)

Before any task is considered complete, agents MUST run:

```bash
./scripts/validate_all.sh
```

This validation script ensures all repository invariants are maintained.
