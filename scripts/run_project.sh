#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo
echo "========================================"
echo "ARMPy Development Run"
echo "========================================"
echo "Project: $PROJECT_ROOT"
echo

if [[ ! -f ".venv/bin/activate" ]]; then
    echo "ERROR: .venv was not found."
    echo "Expected: $PROJECT_ROOT/.venv"
    exit 1
fi

source .venv/bin/activate

echo "Python: $(python --version)"
echo

echo "----------------------------------------"
echo "Changed files"
echo "----------------------------------------"
git status --short || true
echo

echo "----------------------------------------"
echo "1/3 - Python syntax check"
echo "----------------------------------------"
python -m compileall -q src scripts tests
echo "SYNTAX OK"
echo

echo "----------------------------------------"
echo "2/3 - Unit tests"
echo "----------------------------------------"
python -m unittest discover \
    -s tests \
    -p "test_*.py" \
    -v
echo
echo "ALL TESTS PASSED"
echo

echo "----------------------------------------"
echo "3/3 - Robot control"
echo "----------------------------------------"
echo "Starting scripts/control_robot.py"
echo "Calibration scripts are NOT executed."
echo

exec python -u scripts/control_robot.py
