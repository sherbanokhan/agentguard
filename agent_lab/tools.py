# Tools for the Novark triage agent.
#
# These are the actions the agent can take. Right now they're wide open.
# The read tool can reach the private repo even though a triage bot shouldn't need it.
# That's the flaw I'll attack before I fix it.

from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parent / "company_data"
PUBLIC_REPO = LAB_ROOT / "public_repo"


def list_issues():
    # Return every open issue in the public repo
    issues = []
    for path in sorted((PUBLIC_REPO / "issues").glob("*.md")):
        issues.append({"id": path.stem, "content": path.read_text()})
    return issues


# Repos this triage agent is allowed to read. Least privilege: a bot that
# answers public issues has no reason to touch the private repo. I keep this
# switch off for the vulnerable version and flip it on to show the fix.
ALLOWED_REPOS = {"public_repo"}
ENFORCE_ALLOWLIST = False


def read_repo_file(repo, filename):
    # With the allowlist on, the tool refuses any repo this agent isn't
    # scoped to, no matter what the issue text tells it to do. The control
    # lives in the tool, not in the model's judgment.
    if ENFORCE_ALLOWLIST and repo not in ALLOWED_REPOS:
        print(f"[BLOCKED read_repo_file: '{repo}' is not on the allowlist]")
        return f"ACCESS DENIED: this agent may only read {sorted(ALLOWED_REPOS)}."
    file_path = LAB_ROOT / repo / filename
    return file_path.read_text()


def post_comment(issue_id, text):
    # The agent's public reply. This is also the channel an attacker
    # could use to leak data, since whatever goes here is public.
    print(f"[COMMENT on {issue_id}]")
    print(text)
    return {"issue_id": issue_id, "text": text}