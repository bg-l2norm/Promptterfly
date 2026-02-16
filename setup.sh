#!/usr/bin/env bash
set -euo pipefail

# Promptterfly Setup Script
# Creates a lightweight venv and installs the package. Safe and idempotent.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
PYTHON="${PYTHON:-python3}"

echo "==> Promptterfly Setup"

# Check Python version
if ! "$PYTHON" --version > /dev/null 2>&1; then
    echo "Error: python3 not found. Please install Python 3.11+."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment in $VENV_DIR..."
    "$PYTHON" -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Upgrade pip/setuptools/wheel
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install package in editable mode
echo "Installing promptterfly..."
pip install -e "$PROJECT_ROOT"

# Verify installation
echo "Verifying installation..."
if command -v promptterfly > /dev/null 2>&1; then
    echo "✓ promptterfly installed successfully"
    echo ""
    echo "Run 'promptterfly --help' to get started."
    echo "If you get 'command not found', try: source $VENV_DIR/bin/activate"
else
    echo "✗ Installation seems incomplete. Try manually:"
    echo "  source $VENV_DIR/bin/activate"
    echo "  pip install -e $PROJECT_ROOT"
    exit 1
fi

echo ""
echo "Setup complete! To use Promptterfly in the future:"
echo "  source $VENV_DIR/bin/activate"
echo "  promptterfly <command>"
