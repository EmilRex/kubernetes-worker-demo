import subprocess


def get_current_sha() -> dict:
    """Attempt to capture the current git SHA"""
    p = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"], capture_output=True, encoding="ascii"
    )
    return {"current_sha": p.stdout.strip() or "latest"}
