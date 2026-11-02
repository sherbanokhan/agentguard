# AgentGuard

**Securing AI agents against prompt injection and tool misuse.**

![Security CI](https://github.com/sherbanokhan/agentguard/actions/workflows/security-ci.yml/badge.svg)

AgentGuard is a hands-on security project about a modern problem: AI agents that don't just answer questions but take actions — reading files, calling tools, posting content. When an agent can't tell the difference between data it reads and instructions from its owner, anyone who can get text in front of it can control what it does.

I built vulnerable agents, attacked them, measured how often the attacks worked, built defenses, and proved the defenses hold. Then I turned the findings into the reports, threat models, and governance documents a security or GRC team would actually use.

All work runs locally with fabricated data. No real systems, credentials, or networks are involved.

---

## The deliverables

These are the write-ups that turn the lab into decision-ready security work:

| Document | What it is |
|---|---|
| [Vulnerability Assessment Report](docs/VULNERABILITY_ASSESSMENT.md) | Formal finding with CVSS score, evidence, and remediation |
| [Threat Model](docs/THREAT_MODEL.md) | Data-flow diagram, trust boundaries, STRIDE, MITRE ATLAS, risk register |
| [Governance Playbook](docs/GOVERNANCE_PLAYBOOK.md) | NIST AI RMF / ISO 42001 control mapping, agent-use policy, vendor questionnaire |

---

## Phase 1 — Foundations (deterministic simulation)

A simplified, fully predictable agent that demonstrates the core problem without the noise of a real model. A hidden instruction in a support article makes the agent leak a fake API key and escape its allowed folder (path traversal). I fixed it with three layers of defense and proved each with automated tests.

- **Attacks:** indirect prompt injection (OWASP LLM01), excessive agency (LLM06), path traversal (CWE-22)
- **Defenses:** content treated as data only, tools that validate their own inputs, security logging
- **Result:** 13 automated tests, security scanning (bandit, pip-audit) in CI, all passing on Python 3.12 and 3.14

Full write-up in [LEARNING_LOG.md](LEARNING_LOG.md).

---

## Phase 2 — A realistic AI agent (local LLM)

A triage agent for a fictional company (Novark), powered by a real local model (`qwen2.5:7b` via Ollama). It reads public issues and replies to them, and it holds tools to read repository files and post comments. An attacker who can file a public issue hides an instruction that tells the agent to read the **private** repo and leak its secrets.

### The attack worked

I tested the same injection hidden three ways, 15 trials each, and measured how often the agent reached into the private repo:

| Hiding technique | Private access rate |
|---|---|
| Visible text | 93% (14/15) |
| HTML comment | 67% (10/15) |
| Collapsed `<details>` block | 100% (15/15) |

In separate runs the agent pasted full (fake) production secrets into a public reply.

![Attack succeeds](docs/images/11-attack-succeeds-secret-leaked.png)

### The defense works — and doesn't depend on the model

The root cause is excessive agency: the agent could read any repo. I scoped its file tool with a **least-privilege allowlist**, and the attack was blocked **100% of the time**, deterministically, because the control lives in the tool, not in the model's judgment.

![Defense blocks access](docs/images/13-defense-blocks-access.png)

**The lesson:** prompt injection can't be fully prevented, so the architecture's job is to make a successful injection boring — to ensure that even when the agent is fooled, it can't reach anything that matters.

---

## Run it yourself

Requires Python 3.12+.

```bash
git clone https://github.com/sherbanokhan/agentguard.git
cd agentguard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Phase 1:**
```bash
python3 -m app.vulnerable_agent    # attacks succeed
python3 -m app.secure_agent        # attacks blocked
pytest -v                          # all tests
```

**Phase 2** (needs [Ollama](https://ollama.com) + a local model):
```bash
pip install ollama
ollama pull qwen2.5:7b
python3 -m agent_lab.agent         # triage agent + attack
python3 -m agent_lab.experiment    # success-rate experiment
```

---

## Repository structure

```
agentguard/
├── app/                       # Phase 1: simulated vulnerable + secure agents
├── agent_lab/                 # Phase 2: realistic LLM agent and lab
│   ├── agent.py               #   the triage agent (LLM + tools)
│   ├── tools.py               #   agent tools (with the least-privilege fix)
│   ├── experiment.py          #   success-rate experiment
│   └── company_data/          #   fabricated public/private repos (fake data)
├── tests/                     # automated security tests
├── docs/                      # the three deliverables + images
├── .github/workflows/         # CI: tests + security scans
└── LEARNING_LOG.md            # full build log, decisions, and lessons
```

---

## Limitations

- Phase 1 is a simulation; a real model reads data and instructions in the same text, which is harder to separate.
- Phase 2 uses one local model; results would differ across models and sizes. I observed that a weaker model (llama3.2 3B) couldn't reliably perform the task at all.
- Whether the agent completed public disclosure was probabilistic — which is exactly why the defense is least privilege, not reliance on model behavior.

---

## About

Built by Sherbano Khan as a hands-on study of AI agent security, from offensive testing through defense to governance. Inspired by real-world indirect-prompt-injection incidents against AI coding and workplace agents.