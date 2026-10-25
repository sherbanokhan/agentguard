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
- Connected the project to GitHub using SSH authentication.
- Pushed the project to a public GitHub repository.
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

`git add` — stage files to be included in the next commit.

`git commit -m "message"` — save a snapshot of staged changes.

`git push` — upload commits to GitHub.

`git log --oneline` — show the commit history.

`git diff` — show what changed in a file since the last commit.

`git remote -v` — show where the repository is connected.

`ssh -T git@github.com` — test SSH authentication with GitHub.

`ls -la` — list all files, including hidden ones.

`cat` — print the contents of a file.

I also learned that Git does not track empty folders, so folders like `attacks/` and `tests/` will not appear on GitHub until they contain a file.

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

### Why a Simulation

I started with a deterministic simulation instead of a real LLM or external API. A real LLM can give different answers to the same input, which makes it hard to tell whether a security fix actually worked. With a simulation, the same input always gives the same output, so I can reproduce the attack safely, understand the cause, and measure whether my defenses work.

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
- The agent is supposed to only read files inside `app/lab_data/`. (I later found this restriction could be bypassed with path traversal. See the next entry.)
- `send_message()` only prints to the terminal. Nothing is sent over the network.
- I added `fake_api_key.txt` to `.gitignore` so even the fake secret does not get committed.

### Testing

I ran `python3 app/vulnerable_agent.py`. The output showed the fake secret being sent to `attacker@example.test`, which confirmed the attack worked.

I also ran `git status --untracked-files=all`. `fake_api_key.txt` did not show up, which confirmed that `.gitignore` was working.

### What I Learned

The main problem with AI agents is that untrusted data and trusted instructions end up mixed together. If an agent has access to tools, anyone who can get text in front of it may be able to control what those tools do.

### Limitations

This is a deterministic simulation, not a real LLM. The `if` statement stands in for the model's decision. Also, the attacker's email address is hardcoded in the agent. In the next version, the agent will pull the file name and destination directly from the article, which is closer to how a real attack works.

---

## Making the Attack Realistic and Finding Path Traversal

### Date

October 25, 2026

### Objective

Update the vulnerable agent so the attacker controls the whole attack, and test whether the agent's file tool can be used to reach files outside its allowed folder.

### What I Changed

In the first version, the attacker's email address was hardcoded in the agent, which isn't realistic. I updated the agent so it uses regular expressions to pull both the file name and the destination directly from the article. Now everything the agent does is controlled by the malicious content.

I also moved the lab setup into a `setup_lab()` function and made the agent return what it did. This will make it easier to write automated tests.

### Path Traversal Test

I added a second attack article that asks the agent to read `../lab_private/fake_ssh_key.txt`. The `../` tells the system to go up one folder, which escapes `lab_data/`.

To keep this safe, I created a decoy folder called `lab_private/` with a fake SSH key. That way I could prove the escape without the agent ever touching a real file on my Mac. I also added both lab folders to `.gitignore`.

### Testing

I ran:

`python3 app/vulnerable_agent.py`

Both attacks worked:

- Attack 1 sent `DEMO_KEY_NOT_REAL_12345` to `attacker@example.test`.
- Attack 2 escaped `lab_data/` and sent `DEMO_SSH_KEY_NOT_REAL_67890` to the attacker.

### What I Learned

The agent has two separate problems. Prompt injection lets the attacker decide what the agent does, and path traversal lets the attacker decide which files it can reach. Fixing only one of them isn't enough, so the secure version will need protections at both layers.

I also learned that in Python, joining a folder with an absolute path like `/Users/...` replaces the folder completely. Because of this, I made it a rule to never put real file paths in my test articles.

I mapped the two vulnerabilities to official categories:

- Prompt injection: OWASP LLM01 and CWE-1427
- Path traversal: CWE-22 (also called directory traversal)

---

## Automated Security Tests

### Date

October 25, 2026

### Objective

Turn my manual attack checks into automated tests, so I can prove the vulnerabilities exist now and later prove my defenses block them.

### What I Built

I installed `pytest` and created `tests/test_vulnerable_agent.py` with three tests:

- `test_prompt_injection_exfiltrates_secret` checks that the agent follows the hidden instructions and sends the fake API key to the attacker.
- `test_path_traversal_escapes_lab_folder` checks that the agent reads the fake SSH key from outside `lab_data/`.
- `test_benign_article_triggers_no_actions` checks that a normal article does not make the agent read or send anything.

The first two tests pass when the attacks succeed. This proves the vulnerabilities are real before I try to fix them. The third test is a baseline that makes sure normal behavior still works. When I add defenses, it will help me catch false positives.

### How the Tests Stay Safe

Each test builds a fresh, temporary lab using pytest's `tmp_path`. I used `monkeypatch` to point the agent at the temporary folders during the test. This way, tests never touch my real `app/lab_data/` folder, and every test starts clean.

### Other Setup

- Added an empty `app/__init__.py` so Python can import the agent as a package.
- Added `pytest.ini` so pytest knows where to find my code and tests.
- Saved exact package versions to `requirements.txt` with `pip freeze`, so others can install the same versions.
- Added `.pytest_cache/` to `.gitignore`.

### Testing

I ran `pytest -v`. All 3 tests passed in 0.01 seconds.

I also ran `git status --untracked-files=all` and confirmed no fake key files or cache folders were showing up.

### What I Learned

Running the script and reading the output works, but it depends on me checking it every time. Automated tests check the results in code, so I can rerun them anytime and know right away if something changed.

### Next Step

Build a secure version of the agent. Then write tests that show the same attacks are blocked while normal articles still work.