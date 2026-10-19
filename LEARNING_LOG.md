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

---

## First Attack Simulation: Indirect Prompt Injection

### Date

October 19, 2026

### Objective

Build an intentionally vulnerable AI agent and reproduce an indirect prompt injection attack in a safe, controlled simulation before building any defenses.

### What I Built

I created `app/vulnerable_agent.py`, which simulates an AI agent that has access to two tools: `read_file()` and `send_message()`.

The agent is given a support article to process. The article looks normal, but it contains hidden instructions telling the agent to read `fake_api_key.txt` and send its contents to `attacker@example.test`.

### The Vulnerability

The agent cannot tell the difference between content it is reading and instructions from its actual user. When it sees the instruction in the article, it reads the fake secret and sends it to the attacker.

This is an example of:

- **Indirect prompt injection (OWASP LLM01):** malicious instructions are hidden in content the agent processes, not typed by the user.
- **Excessive agency (OWASP LLM06):** the agent is able to read files and send messages without checking whether the action was actually authorized.

### How I Kept the Lab Safe

- The secret is fake (`DEMO_KEY_NOT_REAL_12345`).
- The agent only reads files inside `app/lab_data/`.
- `send_message()` only prints to the terminal. Nothing is sent over the network.
- I added `fake_api_key.txt` to `.gitignore` so even the fake secret does not get committed.

### Testing

I ran: `python3 app/vulnerable_agent.py` the output showed the fake secret being sent to `attacker@example.test`, which confirmed the attack worked.

I also ran: `git status --untracked-files=all` ,  `fake_api_key.txt` did not show up, which confirmed that `.gitignore` was working.

### What I Learned

The main problem with AI agents is that untrusted data and trusted instructions end up mixed together. If an agent has access to tools, anyone who can get text in front of it may be able to control what those tools do.

### Limitations

This is a deterministic simulation, not a real LLM. The `if` statement stands in for the model's decision. Also, the attacker's email address is hardcoded in the agent. In the next version, the agent will pull the file name and destination directly from the article, which is closer to how a real attack works.