#!/usr/bin/env bash
set -euo pipefail # Enable strict error handling and debugging

# Move to the folder where this script is located
cd "$(dirname "$0")"

# Find a usable Python command for common platforms (Linux, macOS, Windows)
if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=(python3)
elif command -v python >/dev/null 2>&1; then
    PYTHON_CMD=(python)
elif command -v py >/dev/null 2>&1; then
    PYTHON_CMD=(py -3)
else
    echo "Error: Python 3 is not installed or not found in PATH."
    exit 1
fi

# Install dependencies
"${PYTHON_CMD[@]}" -m pip install -r requirements.txt