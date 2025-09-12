import json
import os


def log_llm(event: dict):
    os.makedirs("logs", exist_ok=True)
    with open("logs/llm.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")
