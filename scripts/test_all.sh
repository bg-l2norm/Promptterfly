#!/usr/bin/env bash
# Run all tests with coverage for Promptterfly

set -e

# Ensure we are in the project root
cd "$(dirname "$0")/.." || exit 1

# Set PYTHONPATH to include src for imports
export PYTHONPATH=src

# Run pytest with coverage
pytest -v --cov=promptterfly --cov-report=term-missing
