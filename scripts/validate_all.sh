#!/bin/bash
#
# validate_all.sh - Repository validation script for the Orchestrator
#
# Description:
#   This script validates that the repository meets all required invariants
#   before any task is considered complete. It must be run as part of the
#   preflight process by AI agents operating in this repository.
#
# Usage:
#   ./scripts/validate_all.sh
#
# Exit Codes:
#   0 - All validations passed
#   1 - Validation failed (missing files or invalid structure)
#

set -euo pipefail

echo "=== Running Repository Validation ==="

# Validate that required files exist
echo "Checking required files..."

if [ ! -f "AGENTS.md" ]; then
    echo "ERROR: AGENTS.md not found"
    exit 1
fi

if [ ! -f "README.md" ]; then
    echo "ERROR: README.md not found"
    exit 1
fi

if [ ! -f "LICENSE" ]; then
    echo "ERROR: LICENSE not found"
    exit 1
fi

echo "All required files present."

# Validate that AGENTS.md contains required sections
echo "Validating AGENTS.md structure..."

if ! grep -q "Agent Responsibilities" AGENTS.md; then
    echo "ERROR: AGENTS.md missing 'Agent Responsibilities' section"
    exit 1
fi

if ! grep -q "Agent Restrictions" AGENTS.md; then
    echo "ERROR: AGENTS.md missing 'Agent Restrictions' section"
    exit 1
fi

if ! grep -q "Preflight Requirements" AGENTS.md; then
    echo "ERROR: AGENTS.md missing 'Preflight Requirements' section"
    exit 1
fi

echo "AGENTS.md structure validated."

echo "=== All validations passed ==="
exit 0
