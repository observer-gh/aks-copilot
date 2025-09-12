import subprocess
import shlex

ALLOWED = {"kubectl", "az"}  # whitelist


def run(cmd: str, timeout: int = 5) -> tuple[int, str, str]:
    prog = shlex.split(cmd)[0]
    if prog not in ALLOWED:
        return 127, "", f"blocked command: {prog}"
    try:
        p = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=timeout
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
