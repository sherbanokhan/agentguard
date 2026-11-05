# AgentGuard Engineering Log

This log documents the design decisions, security concepts, problems, testing, and lessons learned while building AgentGuard.

- **Phase 1 (October 2026):** a simulated agent, two attacks, a secure version with three layers of defense, automated tests, and security CI.
- **Phase 2 (November 2026):** a real local LLM agent, an attack measured over 45 runs, and a least-privilege fix.

---

## Environment Setup and Vulnerable Agent Lab

### Date

October 19, 2026

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

---

## Building the Secure Agent

### Date

October 28, 2026

### Objective

Build a secure version of the agent that blocks both attacks, and prove it with automated tests.

### What I Built

I created `app/secure_agent.py` with three layers of defense:

- **Layer 1: Content is treated as data only.** The agent's only job is to summarize the article. Nothing in the article can trigger a tool, no matter how the instruction is worded. This is the main fix for prompt injection.
- **Layer 2: The tools protect themselves.** `safe_read_file()` blocks absolute paths and checks where a path actually ends up after resolving `../`. If it lands outside `lab_data/`, it's blocked. `safe_send_message()` only sends to addresses on an allowlist.
- **Layer 3: Detection and logging.** The agent looks for phrases that look like instructions and logs a warning. Every blocked tool call is also logged to `logs/security_events.log`.

Layer 1 already stops both attacks, but I added layer 2 anyway. If someone later adds a feature that lets content reach a tool, the tools are still safe on their own. This is defense in depth.

### Design Decisions

- **Checking the resolved path instead of searching for `../`.** There are many ways to disguise `../` in text, but the final location of a path can't be disguised.
- **Allowlist instead of blocklist.** I can't list every bad email address, but I can list the few approved ones.
- **Detection only logs, it doesn't block.** Pattern matching is easy to get around by rewording, and it can flag normal text like "read the FAQ." So it's a warning system, not the real defense.
- **Reused the same attack articles** from the vulnerable agent so the before-and-after comparison is fair.

### Testing

I wrote `tests/test_secure_agent.py` with 10 tests that check:

- Both attack articles cause no reads or sends.
- Injection attempts are detected.
- A normal article is summarized without a warning.
- `safe_read_file()` blocks path traversal and absolute paths, but still reads files inside the lab.
- `safe_send_message()` blocks unapproved addresses but allows approved ones.
- Blocked actions show up in the log.

I ran `pytest -v --no-header`. All 13 tests passed: 3 showing the attacks work against the vulnerable agent, and 10 showing they're blocked by the secure agent.

### Problems Encountered

When I first ran pytest, it only found 3 tests. The new test file hadn't been saved in VS Code, so pytest saw an empty file and didn't show any error. Saving the file fixed it. Lesson: if the number of collected tests looks wrong, check that the file actually has content.

I also noticed the security log kept lines from earlier runs. The log adds to the end of the file instead of replacing it, which is how an audit trail should work.

### What I Learned

Fixing prompt injection isn't about catching bad phrases. It's about making sure untrusted content can never control tools in the first place. Tests that check normal behavior still works are just as important as tests that check attacks are blocked, because a defense that blocks everything is useless.

### Limitations

- The summary is a stand-in for an LLM. A real LLM reads instructions and data in the same text, so separating them is much harder than in my simulation.
- The detection patterns are simple and easy to reword around.
- The allowlist is hardcoded in the code. In a real system, it would come from a config file or a policy service.

### Screenshots

Saved to `docs/images/`.

---

## Security Scanning and Fixing a Real Vulnerability

### Date

October 31, 2026

### Objective

Add automated security checks to the project and fix any problems they find.

### What I Added

I set up a GitHub Actions workflow (`.github/workflows/security-ci.yml`) that runs on every push and pull request. It runs three checks:

- **pytest:** runs all 13 tests.
- **bandit:** scans my Python code for risky patterns.
- **pip-audit:** checks my packages against a database of known vulnerabilities.

I gave the workflow `contents: read` permission only. It doesn't need to change anything in the repo, so it shouldn't be able to. This is the same least privilege idea as the allowlist in my secure agent.

### What the Scans Found

**bandit:** No issues in 142 lines of code.

This was interesting, because bandit didn't flag the vulnerable agent. Bandit looks for known risky Python patterns, like running shell commands or hardcoded passwords. It doesn't understand that my `read_file()` trusts a file name from an article. Automated scanners catch common mistakes, but logic flaws in my own design still need manual testing.

**pip-audit:** Found one known vulnerability.

| Package | Version | ID | Fixed in |
|---|---|---|---|
| pytest | 8.4.2 | PYSEC-2026-1845 | 9.0.3 |

pytest creates temporary folders with a predictable name in `/tmp`, like `/tmp/pytest-of-{user}`. Since `/tmp` is shared by all users on a computer, another local user could create that folder first and cause a denial of service or possibly gain privileges. My tests use `tmp_path`, so they do rely on this feature.

### Risk Assessment

I rated it low risk for this project:

- It can only be exploited by someone with an account on the same computer.
- My Mac only has one user, and GitHub Actions uses a fresh, single-user machine for every run.
- pytest is a development tool, not part of the agent itself.

Low risk doesn't mean ignore it, so I still fixed it.

### Problem: The Fix Required Upgrading Python

When I tried to upgrade pytest, it stayed on 8.4.2. Newer versions of pytest don't support Python 3.9, which was the version my project used. Python 3.9 reached end of life in October 2025, so it also no longer gets security fixes. The real root cause wasn't pytest, it was the outdated Python version.

I also noticed a `NotOpenSSLWarning` when running pip-audit, because the Mac's built-in Python 3.9 uses an old encryption library. This was another sign the old setup needed to be replaced.

### The Fix

- Installed Python 3.14.10 from python.org and ran `Install Certificates.command` so it could make secure connections.
- I chose 3.14 instead of 3.15. Python 3.15 was only released a few weeks ago, and tools often need time to support a brand-new version. I avoided 3.13 because it had moved to security-fix-only status with no macOS installer.
- Deleted and rebuilt the `.venv` with Python 3.14.
- Installed pytest 9.2.0 and updated `requirements.txt` with `pip freeze`.
- Installed bandit and pip-audit after `pip freeze` so they stay out of `requirements.txt`, since the agent doesn't need them to run.
- Updated the CI workflow to test on Python 3.12 and 3.14.

### Testing

- `pip-audit -r requirements.txt`: No known vulnerabilities found.
- `bandit -r app`: No issues identified.
- `pytest -v`: All 13 tests passed on Python 3.14.

### What I Learned

I followed the full process: detect, understand, assess, fix. Reading the advisory first helped me understand the real risk instead of just upgrading blindly.

I also learned that the latest version isn't always the safest choice. The safest choice is usually a supported, stable version that my tools work with. Unsupported software quietly collects unfixed vulnerabilities, which is what happened with Python 3.9.

---

## Phase 2: A Realistic AI Agent with a Local LLM

### Date

November 1–2, 2026

### Objective

Replace the simulated agent with a real local AI model that makes its own decisions, attack it with indirect prompt injection, measure how often the attack works, and fix it.

### What I Built

I created a new `agent_lab/` folder for a fictional company called Novark:

- **Fake company data.** A public repo with three issues (`issue_001` and `issue_002` are normal, `issue_003` is poisoned) and a private repo with a fake `config.py`. I made the fake secrets look like `DEMO_..._NOT_REAL` on purpose, so secret scanners don't mistake them for real keys.
- **Three tools** in `tools.py`: `list_issues`, `read_repo_file`, and `post_comment`. In the vulnerable version, `read_repo_file` can read any repo, including the private one.
- **The agent** in `agent.py`. It connects a local model through Ollama to the tools using real tool calling. Python gives it one issue at a time, and the model decides which tools to call.
- **The experiment** in `experiment.py`. It runs the same attack hidden three different ways, 15 times each, and records whether the agent read the private file and whether a secret ended up in a public comment. Results save to `results/attack_results.csv`.

### Problem: The First Model Couldn't Do the Task

I started with `llama3.2` (3B) because it's small and fast. It couldn't reliably chain tool calls, and sometimes it made up file contents instead of actually reading the file. A model that can't do the job isn't a useful test, so I switched to `qwen2.5:7b`, which my Mac (16 GB of RAM) runs fine. It handled the normal issues correctly, which gave me a clean baseline.

### Results

| How the instruction was hidden | Read the private repo |
|---|---|
| Visible text ("SYSTEM NOTE...") | 14 / 15 (93%) |
| HTML comment | 10 / 15 (67%) |
| Collapsed `<details>` block | 15 / 15 (100%) |

In all 45 batch runs, the model stopped before posting the secrets publicly. In separate runs outside the experiment, it did post the full fake config in a public reply (screenshot 11).

What surprised me: hiding the instruction in an HTML comment worked the least. Something hidden from a human reviewer isn't automatically more convincing to the model.

### The Fix

The root cause was excessive agency. A bot that answers public issues never needs the private repo. I added an allowlist inside `read_repo_file` (`ALLOWED_REPOS = {"public_repo"}`), turned on with `ENFORCE_ALLOWLIST`. With it on, the agent still tried to read the private repo, because the injection still fooled it, but the tool refused every time and returned `ACCESS DENIED`.

### Deliverables

I turned the findings into three documents in `docs/`:

- **Vulnerability assessment:** the finding, my CVSS 3.1 score (8.6, High), evidence, and remediation.
- **Threat model:** trust boundaries, STRIDE, MITRE ATLAS mapping, and a risk register.
- **Governance playbook:** controls mapped to NIST AI RMF and ISO 42001, an agent-use policy, and a vendor questionnaire.

### What I Learned

The model's good behavior is not a security control. It stopped the final step in every batch run, but it still reached private data almost every time, and in separate runs it did leak the secrets. An attacker only needs it to work once. The fix that held was in the tool, not in the model's judgment. I also learned to measure attacks over many runs instead of trusting one result, because a real model doesn't behave the same way every time.

### Limitations

- I tested one model. Other models and sizes would give different results.
- 15 runs per technique is a small sample.
- GitHub is simulated with local folders, not the real GitHub API.
- Phase 2 isn't covered by the automated tests or CI, because it needs a local model running. The CI checks cover the Phase 1 code in `app/`.

### Screenshots

Saved to `docs/images/` (10 to 13).
