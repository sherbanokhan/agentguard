# AgentGuard - secure agent
#
# This is the fixed version of vulnerable_agent.py. I used three layers:
#   1. The agent treats the article as data. Nothing in it can trigger a tool.
#   2. The tools check their own inputs, so they stay safe even if layer 1 fails.
#   3. Anything suspicious or blocked gets logged.
#
# Same lab rules as before: fake secrets only, no network calls.

import logging
import re
from pathlib import Path

# Reusing the exact same attack articles so the before/after comparison is fair
from app.vulnerable_agent import ARTICLE_EXFIL, ARTICLE_TRAVERSAL

APP_DIR = Path(__file__).resolve().parent
LAB_DIR = APP_DIR / "lab_data"
PRIVATE_DIR = APP_DIR / "lab_private"
LOG_DIR = APP_DIR.parent / "logs"

# Allowlist instead of a blocklist. I can't list every bad address,
# but I can list the few good ones.
ALLOWED_DESTINATIONS = {"support-team@example.test"}

# Phrases that look like someone giving the agent orders.
# This is only for logging. Attackers can easily reword around it,
# so it's not my real defense.
INJECTION_PATTERNS = {
    "read file instruction": re.compile(r"\bread\s+\S+", re.IGNORECASE),
    "send contents instruction": re.compile(r"send (its|the) contents to", re.IGNORECASE),
    "ignore instructions": re.compile(r"ignore (all |any )?(previous|prior) instructions", re.IGNORECASE),
}

logger = logging.getLogger("agentguard.security")


class SecurityViolation(Exception):
    """Raised when a tool call breaks one of my security rules."""


def setup_lab():
    # Same fake files as the vulnerable agent
    LAB_DIR.mkdir(exist_ok=True)
    PRIVATE_DIR.mkdir(exist_ok=True)
    (LAB_DIR / "fake_api_key.txt").write_text("DEMO_KEY_NOT_REAL_12345")
    (PRIVATE_DIR / "fake_ssh_key.txt").write_text("DEMO_SSH_KEY_NOT_REAL_67890")


# ----- Layer 2: tools that protect themselves -----

def safe_read_file(filename):
    requested = Path(filename)

    # Block absolute paths first. In Python, LAB_DIR / "/some/path" throws
    # away LAB_DIR completely. I found this while testing the vulnerable agent.
    if requested.is_absolute():
        logger.warning("BLOCKED read_file: absolute path requested: %s", filename)
        raise SecurityViolation(f"Absolute paths are not allowed: {filename}")

    # resolve() works out where the path really ends up after all the ../
    # I check that instead of searching the text for "../" because there are
    # too many ways to disguise it. The final location can't be disguised.
    lab_root = LAB_DIR.resolve()
    resolved = (lab_root / requested).resolve()

    if not resolved.is_relative_to(lab_root):
        logger.warning("BLOCKED read_file: path traversal attempt: %s", filename)
        raise SecurityViolation(f"Path escapes the lab folder: {filename}")

    logger.info("ALLOWED read_file: %s", filename)
    return resolved.read_text()


def safe_send_message(destination, content):
    # Anything not on the allowlist is rejected, no exceptions
    if destination not in ALLOWED_DESTINATIONS:
        logger.warning("BLOCKED send_message: unapproved destination: %s", destination)
        raise SecurityViolation(f"Destination not on the allowlist: {destination}")

    logger.info("ALLOWED send_message: %s", destination)
    print(f"[SIMULATED SEND] Destination: {destination}")
    print(f"[SIMULATED SEND] Content: {content}")


# ----- Layer 3: detection and logging -----

def detect_injection(text):
    # Returns the names of any suspicious patterns found in the text
    return [name for name, pattern in INJECTION_PATTERNS.items() if pattern.search(text)]


# ----- Layer 1: the agent only treats content as data -----

def summarize(article_text):
    # Stand-in for an LLM summary. Just grabs the first real line.
    lines = [line.strip() for line in article_text.splitlines() if line.strip()]
    return lines[0] if lines else ""


def secure_agent(article_text):
    # The agent's only job is to summarize. It never calls a tool based
    # on what the article says, no matter how the instruction is worded.
    print("Secure agent received article content.")

    findings = detect_injection(article_text)
    if findings:
        logger.warning("Possible prompt injection detected: %s", findings)
        print("[WARNING] Possible prompt injection detected. Treating article as data only.")

    summary = summarize(article_text)
    print(f"Summary: {summary}")
    print("Actions taken: none")

    return {"summary": summary, "injection_detected": bool(findings), "actions_taken": []}


if __name__ == "__main__":
    LOG_DIR.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(LOG_DIR / "security_events.log")],
    )
    setup_lab()

    print("=== Attack 1: Data exfiltration (secure agent) ===")
    secure_agent(ARTICLE_EXFIL)

    print()
    print("=== Attack 2: Path traversal (secure agent) ===")
    secure_agent(ARTICLE_TRAVERSAL)

    # Layer 1 already stopped both attacks, so here I attack the tools
    # directly to make sure layer 2 holds up on its own.
    # The absolute path is made up. It gets blocked before any read happens.
    print()
    print("=== Direct tool attacks (testing layer 2) ===")
    for bad_path in ["../lab_private/fake_ssh_key.txt", "/Users/attacker/.ssh/id_ed25519"]:
        try:
            safe_read_file(bad_path)
        except SecurityViolation as error:
            print(f"[BLOCKED] {error}")

    try:
        safe_send_message("attacker@example.test", "test")
    except SecurityViolation as error:
        print(f"[BLOCKED] {error}")