#!/usr/bin/env bash
set -euo pipefail

# Promptterfly Start Script
# Bootstraps environment on first run, then activates venv and runs commands.

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
BOOTSTRAP_FLAG="$PROJECT_ROOT/.promptterfly/.bootstrapped"
PYTHON="${PYTHON:-python3}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Check if first run (no venv or not bootstrapped)
first_run=0
if [ ! -d "$VENV_DIR" ] || [ ! -f "$BOOTSTRAP_FLAG" ]; then
    first_run=1
fi

bootstrap() {
    log_info "Welcome to Promptterfly! Let's set things up."

    # Check Python
    if ! "$PYTHON" --version > /dev/null 2>&1; then
        log_error "python3 not found. Please install Python 3.11+ and try again."
        exit 1
    fi

    # Ask about venv creation if not present
    if [ ! -d "$VENV_DIR" ]; then
        read -p "Create a virtual environment in .venv/? [Y/n] " -r
        if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
            log_info "Creating virtual environment..."
            "$PYTHON" -m venv "$VENV_DIR"
        else
            log_warn "Skipping venv creation. You may need to install dependencies globally."
        fi
    fi

    # If venv exists, activate and upgrade pip
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
        log_info "Upgrading pip..."
        pip install --upgrade pip
    fi

    # Ask about extras
    log_info "Choose which dependency groups to install (default: core only):"
    read -p "  Install test dependencies? [y/N] " -r
    install_test=0
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_test=1
    fi

    read -p "  Install dev dependencies (linters, pre-commit)? [y/N] " -r
    install_dev=0
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_dev=1
    fi

    # Install package
    log_info "Installing promptterfly..."
    if [ -d "$VENV_DIR" ]; then
        pip install -e "$PROJECT_ROOT" || pip install -e "$PROJECT_ROOT" --break-system-packages
    else
        pip install "$PROJECT_ROOT" || pip install "$PROJECT_ROOT" --break-system-packages
    fi

    # Install extras if chosen
    if [ $install_test -eq 1 ]; then
        log_info "Installing test dependencies..."
        pip install -e "$PROJECT_ROOT[test]" || pip install "promptterfly[test]" --break-system-packages
    fi
    if [ $install_dev -eq 1 ]; then
        log_info "Installing dev dependencies..."
        pip install -e "$PROJECT_ROOT[dev]" || pip install "promptterfly[dev]" --break-system-packages
    fi

    # Mark bootstrapped
    mkdir -p "$PROJECT_ROOT/.promptterfly"
    touch "$BOOTSTRAP_FLAG"
    log_success "Bootstrap complete! You can now use 'promptterfly'."
}

activate_venv() {
    if [ -d "$VENV_DIR" ]; then
        # shellcheck source=/dev/null
        source "$VENV_DIR/bin/activate"
    fi
}

# Run bootstrap if needed
if [ $first_run -eq 1 ]; then
    bootstrap
else
    activate_venv
fi

# Execute the command (passed as arguments to this script)
if [ $# -eq 0 ]; then
    # No command given; show help
    if command -v promptterfly > /dev/null 2>&1; then
        promptterfly --help
    else
        log_error "promptterfly not found in PATH. Try running ./start.sh init to set up."
        exit 1
    fi
else
    "$@"
fi
