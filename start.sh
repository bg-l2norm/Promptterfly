#!/usr/bin/env bash
set -euo pipefail

# Promptterfly Start Script
# Launches the interactive REPL with the virtual environment activated.
# For first-time setup, run ./setup.sh first.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Check if venv exists
if [ ! -d "$VENV_DIR" ]; then
    log_error "Virtual environment not found!"
    log_info "Please run './setup.sh' first to set up Promptterfly."
    exit 1
fi

# Activate venv
source "$VENV_DIR/bin/activate"

# Check if promptterfly is installed
if ! python -c "import promptterfly" > /dev/null 2>&1; then
    log_error "promptterfly is not installed in the virtual environment."
    log_info "Run './setup.sh' to install dependencies."
    exit 1
fi

# If arguments are provided, pass them to the REPL as commands
# The REPL will execute them and exit
if [ $# -gt 0 ]; then
    python -m promptterfly.repl -- "$@"
    exit $?
fi

# Otherwise, start interactive REPL
python -m promptterfly.repl
