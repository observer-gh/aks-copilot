#!/usr/bin/env bash
set -euo pipefail

# Colors
BOLD_CYAN='\033[1;36m'
GREEN='\033[32m'
GRAY='\033[90m'
RED='\033[31m'
BOLD_GREEN='\033[1;32m'
RESET='\033[0m'

DIR="examples/enemy"

echo -e "${BOLD_CYAN}== 0) Clean old outputs ==${RESET}"
> report.md
> patch.json
mkdir -p logs
: > logs/llm.jsonl
echo -e "${GREEN}OK${RESET}"

echo
echo -e "${BOLD_CYAN}== 1) Validate (quick spot check) ==${RESET}"
python -m src.cli.main validate "$DIR/pvc.yml" || true
python -m src.cli.main validate "$DIR/deploy.yml" || true
python -m src.cli.main validate "$DIR/ing.yml" || true


echo
echo -e "${BOLD_CYAN}== 2) Fix (folder, full flow: Inspect → Explain → Patch[LLM+guards]) ==${RESET}"
python -m src.cli.main fix-folder "$DIR"
echo -e "${GREEN}OK${RESET}"

echo
echo -e "${BOLD_CYAN}== 3) Report (tail) ==${RESET}"
echo -e "${GRAY}----- report.md (last 60 lines) -----${RESET}"
if command -v bat >/dev/null 2>&1; then
  bat --style=plain --paging=never report.md | tail -n 60
elif command -v pygmentize >/dev/null 2>&1; then
  pygmentize -l markdown report.md | tail -n 60
else
  tail -n 60 report.md || true
fi
echo
echo -e "${GRAY}-------------------------------------${RESET}"

echo
echo -e "${BOLD_CYAN}== 4) Patch ops preview ==${RESET}"
if [ -f patch.json ]; then
  if command -v jq >/dev/null 2>&1; then
    jq . patch.json
  else
    cat patch.json
  fi
else
  echo -e "${RED}patch.json not found${RESET}"
fi

echo
echo -e "${BOLD_CYAN}== 5) Apply (stub) ==${RESET}"
python -m src.cli.main apply

echo
echo -e "${BOLD_CYAN}== 6) Health (stub) ==${RESET}"
python -m src.cli.main health

echo
echo -e "${BOLD_CYAN}== 7) AI Safety Logs (tail) ==${RESET}"
if [ -f logs/llm.jsonl ]; then
  echo -e "${GRAY}----- logs/llm.jsonl (last 20 lines) -----${RESET}"
  if command -v jq >/dev/null 2>&1; then
    tail -n 20 logs/llm.jsonl | while read -r line; do
      echo "$line" | jq . 2>/dev/null || echo "$line"
    done
  else
    tail -n 20 logs/llm.jsonl || true
  fi
  echo -e "${GRAY}------------------------------------------${RESET}"
else
  echo -e "${RED}logs/llm.jsonl not found${RESET}"
fi

echo
echo -e "${BOLD_GREEN}== DONE ==${RESET}"