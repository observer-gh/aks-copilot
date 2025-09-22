#!/bin/sh
set -e

# Execute the main copilot CLI with passed arguments
exec python -m src.cli.main "$@"
