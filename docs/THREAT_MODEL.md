# Threat Model — AI Issue-Triage Agent

**Author:** Sherbano Khan
**Project:** AgentGuard — Securing AI Agents and MCP Tools
**Date:** November 2026
**Classification:** TLP:CLEAR — may be shared freely (all data in this lab is fabricated)
**Frameworks used:** STRIDE, MITRE ATLAS, trust-boundary analysis

---

## 1. What I Modeled

I threat-modeled the AI issue-triage agent I built for a fictional company (Novark). The agent reads incoming public issues and replies to them, and it holds tools that let it read repository files and post comments. My goal was to find where the AI introduces new risk that a traditional app wouldn't have, and to decide where the security boundaries actually need to sit.

I treat the agent as an autonomous actor with its own permissions, because that is the mindset these systems require: the question isn't only "can a user do X," it's "can content the agent *reads* make the agent do X on an attacker's behalf."

---

## 2. Architecture and Trust Boundaries

![Threat model data flow](docs/images/threat_model.png)

The diagram shows four zones and the attack path (in red) I confirmed in testing:

| Zone | Contains | Trust |
|---|---|---|
| Untrusted (Internet) | Any public user, including the attacker | None |
| Public boundary | Public repo issues, public replies | Low — anyone can write here |
| Agent trust zone | The AI triage agent and its tools | The agent is trusted with tools, but acts on untrusted input |
| Private boundary | Private repo with secrets/config | High — should never be reachable from a public workflow |

**The core design flaw:** there is a path from the untrusted zone all the way into the private boundary, and it runs *through the agent*. The agent is the bridge. Untrusted issue text (step 2) can steer the agent across the private boundary (step 3) and back out to a public reply (step 5). That crossing is what the whole model is about.

### Data flows
1. Attacker files a poisoned issue into the public repo.
2. Agent reads issue text via `list_issues` (untrusted data enters the agent).
3. Agent is steered to call `read_repo_file` on the private repo (boundary crossing).
4. Secrets are returned into the agent's context.
5. Agent publishes a reply via `post_comment` (data leaves to the public boundary).
6. Attacker reads the public reply and obtains the secrets.

---

## 3. STRIDE Analysis

I applied STRIDE, adapted for an AI agent:

| Category | Threat in this system | Severity |
|---|---|---|
| **S**poofing | An attacker poses as an ordinary issue reporter; there's no barrier to submitting content the agent will read. | Medium |
| **T**ampering | Injected instructions in issue text tamper with the agent's intended behavior — it acts on attacker goals instead of the operator's. | High |
| **R**epudiation | The malicious action looks like a normal issue. Without tool-call logging, attributing the abuse after the fact is hard. | Medium |
| **I**nformation Disclosure | The headline risk: private secrets disclosed through the agent's public reply. | **High** |
| **D**enial of Service | The agent can be driven to loop, waste tool calls, or post spam replies. | Low–Medium |
| **E**levation of Privilege | Classic confused-deputy: an unprivileged attacker uses the agent's private-repo access to reach data they could never reach directly. | **High** |

The two that matter most here are **Information Disclosure** and **Elevation of Privilege**, and they're really the same story: the agent lends its privileges to whoever can get text in front of it.

---

## 4. MITRE ATLAS Mapping

I mapped the attack to ATLAS, the AI-specific companion to MITRE ATT&CK:

| ATLAS tactic | Technique in this attack |
|---|---|
| Initial Access | **LLM Prompt Injection (AML.T0051)** — indirect injection via planted issue content |
| Execution | The agent executes the injected instruction using its own tools |
| Exfiltration | Sensitive data is exfiltrated through the agent's own output channel (the public reply) |
| Impact | Disclosure of credentials enabling downstream database, payment, and internal-API abuse |

---

## 5. Risk Register

This is the register I'd hand to a security or GRC team. Likelihood and impact are my assessments from the lab results.

| ID | Risk | Likelihood | Impact | Severity | Owner | Mitigation | Status |
|---|---|---|---|---|---|---|---|
| R1 | Indirect prompt injection via public issue leads to unauthorized private-repo access | High | High | **High** | AI platform / AppSec | Least-privilege tool scoping (repo allowlist) | **Mitigated** (verified) |
| R2 | Public exfiltration of secrets through the agent's reply | Medium | High | **High** | AppSec | Output scanning for secrets + human approval before sensitive replies | Open |
| R3 | Over-privileged agent identity (excessive agency) | High | High | **High** | Platform / IAM | Scoped, short-lived credentials per agent role | Partially mitigated |
| R4 | Insufficient logging and attribution of agent tool calls | Medium | Medium | Medium | SecOps | Audit-log every tool call, especially blocked ones | Open |
| R5 | Hidden-content injection bypasses human review (HTML comments, collapsed blocks) | Medium | Medium | Medium | AppSec | Strip hidden content from untrusted text before the model sees it | Open |

---

## 6. My Key Architectural Recommendation

The most durable fix is not a better prompt or a smarter model — it's **moving the security boundary into the tools and the agent's identity**, so a hijacked agent simply cannot reach what it shouldn't.

Concretely, in priority order:
1. **Least privilege at the tool layer** (R1, R3) — the control I implemented and verified. A triage agent is scoped to the public repo only.
2. **Treat agent output as untrusted** (R2) — filter replies and require human approval for anything containing file contents.
3. **Scoped identity** (R3) — the agent's credentials should carry only what its role needs, nothing more.
4. **Audit and input hygiene** (R4, R5) — log every tool call and strip hidden content before it reaches the model.

The principle I keep coming back to: **prompt injection can't be fully prevented, so the architecture's job is to make a successful injection boring** — to ensure that even when the agent is fooled, it can't do anything that matters.
