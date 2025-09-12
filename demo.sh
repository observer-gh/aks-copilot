#!/usr/bin/env bash
set -euo pipefail

DIR="examples/enemy"

echo "== Validate =="
python -m src.cli.main validate "$DIR/deploy.yml" || true
python -m src.cli.main validate "$DIR/pvc.yml" || true

echo
echo "== Fix (folder) =="
python -m src.cli.main fix-folder "$DIR"
echo
echo "report.md:"
sed -n '1,80p' report.md

echo
echo "== Apply (stub) =="
python -m src.cli.main apply

echo
echo "== Health (stub) =="
python -m src.cli.main health