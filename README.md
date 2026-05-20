# AI-PR-Review-Assistant

An AI-powered GitHub review assistant that improves code quality, reduces review latency, and standardizes engineering feedback across teams.


## MVP goal
Build an AI PR Review Assistant that:
Receives a GitHub pull request event, analyzes the changed code with AI, and posts a structured review comment back to the PR.


## MVP flow

```text
GitHub Webhook
      ↓
FastAPI Endpoint
      ↓
GitHub API Client
      ↓
PR Diff Fetcher
      ↓
Context Builder
      ↓
OpenAI Review Engine
      ↓
Structured Review
      ↓
GitHub Comment Publisher
```


## 🚀 Features (MVP)

Version 1 should include:
- GitHub App webhook receiver
- Pull request diff fetcher
- AI review prompt
- Review result formatter
- GitHub PR comment publisher
- Basic config via environment variables

## 🏗 Initial repo structure

```text
ai-pr-review-assistant/
├─ app/
│  ├─ main.py
│  ├─ github/
│  │  ├─ client.py
│  │  ├─ webhooks.py
│  │  └─ auth.py
│  ├─ review/
│  │  ├─ orchestrator.py
│  │  ├─ diff_parser.py
│  │  └─ formatter.py
│  ├─ ai/
│  │  ├─ client.py
│  │  └─ prompts.py
│  └─ config.py
├─ tests/
├─ docs/
├─ .env.example
├─ Dockerfile
├─ docker-compose.yml
├─ pyproject.toml
└─ README.md
```

## ⚙️ Tech Stack

- Python
- FastAPI
- GitHub App API
- OpenAI API
- Docker
- pytest

## 📊 Status

Create a local FastAPI service with one endpoint:

POST /webhooks/github
