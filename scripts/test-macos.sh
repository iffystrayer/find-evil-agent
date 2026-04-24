#!/bin/bash
# Helper script for running tests on macOS with weasyprint support
# This sets the required library path for weasyprint to find gobject libraries

export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib

# Activate virtual environment if not already active
if [ -z "$VIRTUAL_ENV" ]; then
    source .venv/bin/activate
fi

# Run pytest with all arguments passed through
python -m pytest "$@"
