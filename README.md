# 🤖 Agentic-ETL-Orchestrator
> **Autonomous Data Engineering Agent powered by LangGraph & MCP**

[![GCP](https://img.shields.io/badge/Provider-Google_Cloud-blue?logo=google-cloud)](https://cloud.google.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-yellow?logo=python)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-LangGraph-orange)](https://github.com/langchain-ai/langgraph)

---

## 🏗️ System Architecture
This project implements a **Self-Healing Multi-Agent System** that transforms unstructured business requirements (Jira/UI) into production-ready, audited ETL pipelines.

![Architecture Diagram](./assets/architecture.png)

### 🧩 The 4-Stage Autonomous Flow
1. **Intake & Analysis:** Extracts intent from Jira and uses **Model Context Protocol (MCP)** to verify schemas in BigQuery.
2. **Planning & Logic:** Orchestrates task breakdown via **LangGraph** with a Senior DE "Critique" loop.
3. **Production Studio:** Generates modular **PySpark** code and performs **Static Code Analysis (SCA)** to prune dead code.
4. **DevOps & Deployment:** Raises a GitHub PR with automated execution reports and performance scores.

---

## 🛠️ Tech Stack
| Component | Technology |
| :--- | :--- |
| **LLM** | Gemini 1.5 Flash (Vertex AI) |
| **Orchestration** | LangGraph & Pydantic |
| **Data Grounding** | Model Context Protocol (MCP) |
| **Processing** | Apache Spark (PySpark) & BigQuery |
| **Infrastructure** | GCP (Dataproc Serverless, Secret Manager) |

---

## 🚀 Key Features
* **Zero-Hallucination:** MCP ensures the agent only writes code for columns that actually exist.
* **Shift-Left Quality:** Automated linting removes unused variables and flags BigQuery anti-patterns.
* **Self-Correction:** Agents automatically refactor logic if unit tests or audit checks fail.

---

## 📂 Project Structure
```bash
├── agents/            # Specialized Agent Nodes (Parser, Auditor, Coder)
├── config/            # standards.yaml & Framework Constraints
├── inputs/            # User Stories & Jira Mocks
├── notebooks/         # Prototyping & Connectivity Tests
├── ui/                # Intake UI prototype (HTML)
├── docs/              # Use cases and UI design docs
└── README.md

## 🖥️ Launch the Intake UI Prototype
The Week 1 intake UI is a static HTML page at:

- `ui/request_intake_form.html`

You can launch it locally with a lightweight Python HTTP server:

```bash
cd /workspace/Agentic-ETL-Orchestrator
python3 -m http.server 8000
```

Then open:

- `http://localhost:8000/ui/request_intake_form.html`

### Alternative (open file directly)
You can also open `ui/request_intake_form.html` directly in a browser, but running an HTTP server is recommended for consistent behavior.
