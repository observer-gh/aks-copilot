#!/usr/bin/env bash
set -euo pipefail

DIR="examples/enemy"

echo "== 0) Clean old outputs =="
rm -f report.md patch.json
mkdir -p logs
: > logs/llm.jsonl
echo "OK"

echo
echo "== 1) Validate (quick spot check) =="
python -m src.cli.main validate "$DIR/pvc.yml" || true
python -m src.cli.main validate "$DIR/deploy.yml" || true
python -m src.cli.main validate "$DIR/ing.yml" || true


echo
echo "== 2) Fix (folder, full flow: Inspect → Explain → Patch[LLM+guards]) =="
python -m src.cli.main fix-folder "$DIR"
echo "OK"

echo
echo "== 3) Report (tail) =="
echo "----- report.md (last 60 lines) -----"
tail -n 60 report.md || true
echo
echo "-------------------------------------"

echo
echo "== 4) Patch ops preview =="
if [ -f patch.json ]; then
  cat patch.json
else
  echo "patch.json not found"
fi

echo
echo "== 5) Apply (stub) =="
python -m src.cli.main apply

echo
echo "== 6) Health (stub) =="
python -m src.cli.main health

echo
echo "== 7) AI Safety Logs (tail) =="
if [ -f logs/llm.jsonl ]; then
  echo "----- logs/llm.jsonl (last 20 lines) -----"
  tail -n 20 logs/llm.jsonl || true
  echo "------------------------------------------"
else
  echo "logs/llm.jsonl not found"
fi

echo
echo "== DONE =="