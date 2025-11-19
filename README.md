# 🚧 **AI Code Review System** – *Learning Project Under Construction* 🚧
> ⚠️ **This is a learning project under active construction.**
> APIs, models, tools, and architecture may change frequently.
> Use at your own risk — and feel free to explore, modify, and break things! 😄

---

<div align="center">

## 🔍🤖 Automated AI Code Review for GitLab

### **FastAPI + Celery + PostgreSQL + Qdrant + crewAI + Local LLMs**  

Offline-first • Agent-driven • Extensible • Private-Cloud Friendly

---

### 🔰 Badges

![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL--3-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.112+-green)
![Celery](https://img.shields.io/badge/Celery-5.3+-yellowgreen)
![PostgreSQL](https://img.shields.io/badge/Postgres-14+-blue)
![Qdrant](https://img.shields.io/badge/Qdrant-VectorDB-orange)
![crewAI](https://img.shields.io/badge/crewAI-Agents-purple)
![Status](https://img.shields.io/badge/Status-Under_Active_Development-orange)

</div>

---

# 📘 About the Project

This project aims to build a **fully offline, private, agent-based AI system** that can automatically review code in:

- GitLab **Merge Requests**
- Individual **commits**
- (Future) Entire **codebases**, with architectural insights

The system uses:

- **crewAI** → for agent orchestration
- **Local LLMs** → for offline inference (OpenAI-compatible API)
- **FastAPI** → as API/Webhook receiver
- **Celery** → for background processing
- **PostgreSQL + Alembic** → persistent storage with migrations
- **Qdrant** → code RAG and vector search
- **Static analysis tools** → ruff, bandit, mypy, eslint, etc.

All meant to work **in an air-gapped environment**, with **1 worker** and minimal compute.

---

# ✨ Features (MVP)

### 🔔 GitLab Integration
- Receives **Merge Request webhooks**
- Dispatches review jobs to Celery worker

### 🧠 Offline LLM Agent Review
- crewAI agent reviews diffs and produces structured JSON
- Supports local LLMs via OpenAI-compatible API

### 🔍 Static Code Analysis
- Integrates linters and security tools
- Combines static findings with LLM output

### 💬 Automated Reporting
- Generates:
  - Inline comments
  - MR summary
  - Severity-ranked findings

### 📦 Storage & Persistence
- PostgreSQL: MRs, reviews, tasks, findings
- Alembic migrations
- (Future) Qdrant for code embeddings and RAG

---

# 🏗️ Project Structure

```
ai-code-review/
├── app/
│ ├── api/ # FastAPI endpoints
│ ├── crew/ # crewAI agents + tasks
│ ├── db/ # SQLAlchemy + sessions
│ ├── llm/ # Local LLM client
│ ├── models/ # ORM
│ ├── schemas/ # Pydantic models
│ ├── services/ # Business logic
│ ├── workers/ # Celery tasks
│ └── utils/ # Helpers
├── alembic/ # Migrations
├── pyproject.toml # uv + dependencies
└── README.md
```

---

# 🏁 Quick Start

## ▶️ Run API (development)
```bash
uv run uvicorn app.main:app --reload
```
## ▶️ Run Celery Worker
```bash
uv run celery -A app.workers.celery_app.celery_app worker --loglevel=INFO
```
▶️ Run with Docker (coming soon)

Dockerfile + docker-compose.yml will be added after core subsystems stabilize.

🔧 Requirements

Python 3.10+

PostgreSQL 14+

Redis (or RabbitMQ) for Celery broker

Local LLM server (vLLM, llama.cpp, or TGI recommended)

📌 Roadmap

 FastAPI Webhooks

 Celery worker with dummy review

 crewAI agent stub

 Pyproject for uv

 SQLAlchemy models

 GitLab API integration

 Real LLM review

 Static analysis integration

 Qdrant code embedding index

 Full MR inline comments

 Architecture-level RAG review

 Dockerfile & CI pipeline

📜 License

This project is licensed under the AGPL-3.0 license.
See LICENSE
 for details.

🙌 Contributing

Since this is a learning project, contributions, ideas, and PRs are welcome.
Open issues, propose architecture changes, or expand the agent/tool system.

💬 Questions / Ideas?

Open an issue, start a discussion, or just ask! 😊
