# AgentGuard Engineering Log

This log documents the design decisions, security concepts, problems, testing, and lessons learned while building AgentGuard.

---

## Day 1 — Environment Setup and Vulnerable Agent Lab

### Date

Oct 19, 2026

### Objective

Set up the AgentGuard development environment and begin building a controlled vulnerable AI-agent lab for security testing.

### Work Completed

- Created the AgentGuard project directory.
- Initialized a Git repository.
- Created a Python virtual environment.
- Created the initial project structure.
- Added a `.gitignore` file.
- Prevented the virtual environment, secrets, logs, and credentials from being committed to Git.
- Created initial project documentation.

### Commands Learned

`cd` — change the current directory.

`pwd` — display the current working directory.

`mkdir` — create a directory.

`touch` — create an empty file.

`git init` — initialize a Git repository.

`git status` — show the current state of the Git repository.

`python3 -m venv .venv` — create an isolated Python environment.

`source .venv/bin/activate` — activate the project's Python environment.

### Security Concepts Learned

#### Secret Management

Credentials, API keys, environment variables, and cloud credentials should never be committed to a public source-code repository.

#### Development Environment Isolation

Python virtual environments isolate project dependencies from the system Python installation and other projects.

#### Source Control Hygiene

`.gitignore` helps prevent temporary files, credentials, logs, and development artifacts from accidentally entering source control.

### Problems Encountered

#### Problem 1: GitHub SSH Authentication and Key Security

Pushing over HTTPS failed because GitHub no longer accepts account passwords
for Git operations. I switched to SSH authentication using an Ed25519 key pair.

While generating the key, the key files were accidentally created inside the
project folder instead of `~/.ssh/`. I noticed them in `git status` as untracked
files before committing.

**Fix:** Moved both key files to `~/.ssh/`, confirmed they no longer appeared in
`git status`, and verified authentication with `ssh -T git@github.com`.

**Lesson:** Always review `git status` before committing. A private key pushed
to a public repository should be treated as compromised and rotated immediately.
I added SSH key patterns to `.gitignore` as a second layer of protection.

### Next Step

Create the vulnerable AI-agent lab and reproduce the first controlled AI-agent security failure.