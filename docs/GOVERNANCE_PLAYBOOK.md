# AI Agent Governance Playbook

**Author:** Sherbano Khan
**Project:** AgentGuard — Securing AI Agents and Their Tools
**Date:** November 2026
**Classification:** TLP:CLEAR — may be shared freely (all data in this lab is fabricated)
**Frameworks referenced:** NIST AI RMF, ISO/IEC 42001, OWASP Top 10 for LLM & Agentic Apps

---

## 1. Why I Wrote This

I built an AI agent, attacked it, and watched a single public bug report make it leak private secrets. This playbook is my answer to the next question an organization has to ask: *how do we govern these agents so this doesn't happen across the whole company, not just in one lab?*

Most AI-security write-ups stop at the attack. I wrote this part because the harder, and more valuable, problem is turning one finding into repeatable controls: a policy for who can deploy agents, a way to vet third-party AI tools, and a mapping to the frameworks auditors and regulators expect. This is written so a GRC or security team could adopt it as a starting template.

**Scope:** autonomous or semi-autonomous AI agents that hold tools or permissions (read data, call APIs, post content), including agents built on third-party models and MCP servers.

---

## 2. Control Mapping

Here I map the risks I found to the two frameworks most relevant to AI governance — the **NIST AI Risk Management Framework** (functions: Govern, Map, Measure, Manage) and **ISO/IEC 42001** (the AI management-system standard) — plus the OWASP agentic risks.

| Control | What it does | Risk addressed | NIST AI RMF | ISO/IEC 42001 theme | OWASP |
|---|---|---|---|---|---|
| **Least-privilege tool scoping** | An agent's tools can only reach resources its role requires | Unauthorized private access (R1, R3) | MANAGE | Operational controls / access | LLM06 Excessive Agency |
| **Scoped, short-lived agent identity** | Each agent has its own minimal, time-boxed credentials | Over-privilege, lateral movement (R3) | MANAGE | Resource & access management | LLM06 |
| **Output handling as untrusted** | Agent output is filtered for secrets before it leaves | Data exfiltration (R2) | MEASURE / MANAGE | Operational controls | LLM02 Sensitive Info Disclosure |
| **Human-in-the-loop for sensitive actions** | A person approves high-impact agent actions | Autonomous harm (R2) | GOVERN / MANAGE | Human oversight | LLM06 |
| **Input hygiene** | Hidden content is stripped from untrusted text | Concealed injection (R5) | MANAGE | Data governance | LLM01 Prompt Injection |
| **Tool-call audit logging** | Every tool call, especially blocked ones, is logged | Weak attribution (R4) | MEASURE | Monitoring & review | — |
| **Agent inventory** | A maintained register of all agents, tools, and MCP servers in use | Shadow agents | MAP | Context & asset management | — |
| **Pre-deployment AI risk assessment** | Each agent is risk-assessed before go-live | All | MAP / MEASURE | AI risk assessment | — |

**How to read this:** the NIST function tells you *which part of the lifecycle* the control lives in (Govern = policy, Map = understand context, Measure = assess, Manage = act), and the ISO/IEC 42001 theme is where it would sit in a formal AI management system. Together they let an auditor trace each technical control back to a recognized requirement.

---

## 3. AI Agent Use & Approval Policy

A short policy a company could adopt. I kept it to the essentials.

### 3.1 Principles
1. **Least privilege.** An agent receives only the tools and access its specific job requires. Broad or convenient access is not justification.
2. **Untrusted content.** Any content an agent reads from outside its trust boundary (issues, emails, web pages, documents) is untrusted and must never be treated as instructions.
3. **Untrusted output.** An agent's output is untrusted until checked. Output that can reach people or systems is filtered and, where sensitive, human-approved.
4. **Human oversight.** High-impact actions (sending data externally, financial actions, changes to production) require human approval.
5. **Accountability.** Every agent has a named owner and every tool call is logged.

### 3.2 Approval process (before an agent goes live)
- Register the agent in the AI inventory (owner, purpose, tools, data it touches).
- Complete a pre-deployment risk assessment (threat model + risk register).
- Confirm least-privilege scoping and scoped credentials.
- Confirm logging and, where required, human-in-the-loop controls.
- Sign-off by a security/GRC reviewer.

### 3.3 Prohibited without additional review
- Giving an agent access to both untrusted content **and** sensitive data **and** an external communication channel (the "lethal trifecta") without compensating controls.
- Using a third-party model or MCP server that has not passed vendor review (Section 4).

---

## 4. Third-Party AI / MCP Vendor Security Questionnaire

The questions a company should ask before approving an external AI model, tool, or MCP server. This applies the supply-chain trust thinking I used in my earlier project (Arguss) to the AI agent ecosystem.

**Identity & permissions**
1. What permissions does this tool/server request, and can they be scoped down?
2. Does it support per-tenant or per-agent credentials rather than a single shared key?
3. Are credentials short-lived and revocable?

**Data handling**
4. What data leaves our environment, and where does it go?
5. Is our data used for model training? Can we opt out?
6. How is data retained and deleted?

**Tool & supply-chain integrity**
7. Are tool descriptions and server code auditable? (Hidden instructions in tool descriptions are a known attack.)
8. Are dependencies pinned and verified? How are updates reviewed?
9. What is the vendor's process if a published version is found to be compromised?

**Monitoring & incident response**
10. Can we log all calls to and from this tool?
11. Does the vendor provide security advisories and a disclosed vulnerability history?
12. What is the vendor's incident notification SLA?

A tool that can't answer 1–3 and 7 should not be approved for use with sensitive data.

---

## 5. Continuous Compliance Monitoring

Governance isn't one-time. My recommended ongoing cadence:

| Activity | Frequency | Function |
|---|---|---|
| Review agent inventory for new/shadow agents | Monthly | MAP |
| Re-run attack/red-team tests against deployed agents | Quarterly, and on major change | MEASURE |
| Review tool-call logs for blocked/anomalous actions | Continuous / weekly review | MEASURE |
| Re-assess vendor questionnaires for third-party tools | Annually, or on vendor change | MANAGE |
| Review and update this policy | Annually | GOVERN |

---

## 6. Roles

| Role | Responsibility |
|---|---|
| Agent owner | Accountable for one agent's purpose, scoping, and risk assessment |
| Security / AppSec | Defines controls, runs red-team tests, reviews output filtering |
| GRC / Compliance | Owns this policy, control mapping, vendor review, and audit evidence |
| Platform / IAM | Issues scoped agent identities and enforces least privilege |

---

## 7. My Takeaway

The technical fix for my lab was one control (least privilege). But a company doesn't have one agent — it has dozens, built by different teams on different models and tools. Governance is what makes the fix hold at that scale: a policy that every agent is scoped and reviewed, a questionnaire that keeps untrusted third-party tools out, and a monitoring cadence that catches the next problem before it's an incident. That's the difference between fixing a bug and managing a risk.
