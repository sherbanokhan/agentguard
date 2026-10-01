# AgentGuard Engineering Log

This log documents the design decisions, security concepts, problems, testing, and lessons learned while building AgentGuard.

---

## Day 1 — Environment Setup and Vulnerable Agent Lab

### Date

September 30, 2026

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

Initially, `git status` returned:

`fatal: not a git repository`

This happened because the command was being executed from my home directory instead of inside the AgentGuard project.

### Resolution

Created the AgentGuard directory, moved into it, and initialized Git using `git init`.

### Key Lesson

Git commands operate relative to the repository I am currently working inside. I should use `pwd` when I am unsure which directory Terminal is currently using.

### Next Step

Create the vulnerable AI-agent lab and reproduce the first controlled AI-agent security failure.