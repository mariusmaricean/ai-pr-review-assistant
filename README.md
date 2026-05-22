# AI PR Review Assistant

AI PR Review Assistant is a GitHub-integrated backend platform that reviews pull requests with AI, posts structured feedback back to GitHub, and exposes operational metrics for the review pipeline.

## Problem

Code reviews are often slow, inconsistent, and heavily dependent on reviewer availability. Large pull requests make this worse: important bugs, missing tests, security risks, and architectural concerns can be missed when feedback is manual and context is scattered across the repository.

## Solution

AI PR Review Assistant provides a repository-aware review pipeline that reacts to GitHub pull request events, retrieves diff and repository context, runs focused AI reviewers asynchronously, and posts structured feedback back to the PR. The system is designed as backend platform infrastructure: webhooks are verified, work runs through Celery, Redis tracks idempotency and metrics, and guardrails keep workloads bounded.

## Features

- GitHub pull request webhook ingestion with signature verification.
- GitHub App installation token support with personal access token fallback for local testing.
- Celery background jobs backed by Redis.
- Multi-agent AI review profiles for security, performance, maintainability, tests, and architecture.
- Diff chunking for larger pull requests.
- Language-aware review prompts.
- Structured JSON review output with safe parsing fallback.
- Inline GitHub PR review comments with summary-comment fallback.
- Valid changed-line filtering to reduce GitHub `422` review errors.
- Confidence filtering and configurable max comments.
- Repository-aware context from README, CONTRIBUTING, and architecture docs.
- Semantic context retrieval using Sentence Transformers and FAISS.
- Redis-backed review metrics APIs.
- OpenTelemetry tracing foundation and structured logs.
- Redis idempotency to avoid duplicate review posts.
- PR size guardrails for changed files and patch size.
- Admin-protected maintenance endpoints.

## ⚙️ Tech Stack

- Python 3.12
- FastAPI
- Celery
- Redis
- OpenAI API
- GitHub App API
- Pydantic Settings
- HTTPX
- Sentence Transformers
- FAISS
- OpenTelemetry
- Docker Compose
- Ruff
- Pytest

## Engineering Impact

This project demonstrates:

- Platform engineering with GitHub App integration
- Asynchronous distributed processing with Celery and Redis
- Multi-agent LLM orchestration for specialized code review
- Repository-aware semantic retrieval for contextual AI feedback
- Secure webhook validation and idempotent job processing
- Observability, metrics, and production-oriented deployment patterns

## Architecture

```txt
GitHub Pull Request Event
        |
Webhook API (FastAPI)
        |
Signature Verification
        |
Celery Queue
        |
Redis Broker
        |
Background Worker
        |
Review Pipeline
   |-- Chunking
   |-- Language Detection
   |-- Multi-Agent Reviewers
   |-- Semantic Context Retrieval
   `-- Confidence Filtering
        |
GitHub Review Publisher
        |
Metrics + Telemetry
```

See [docs/architecture.md](docs/architecture.md) for the detailed architecture notes.

## Local Development

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

Copy `.env.example` to `.env`, then fill in local values:

```txt
OPENAI_API_KEY=your_openai_key
GITHUB_TOKEN=your_local_github_token
GITHUB_APP_ID=your_github_app_id
GITHUB_PRIVATE_KEY_PATH=./github-app-private-key.pem
GITHUB_WEBHOOK_SECRET=your_webhook_secret
ADMIN_API_TOKEN=your_local_admin_token
REDIS_URL=redis://localhost:6379/0
REVIEW_IDEMPOTENCY_TTL_SECONDS=3600
MAX_CHANGED_FILES=50
MAX_PATCH_CHARS=60000
```

Start Redis:

```bash
docker compose up -d redis
```

Run the API:

```bash
python3 -m uvicorn app.main:app --reload
```

Run the worker in a second terminal:

```bash
source .venv/bin/activate
celery -A app.worker.celery_app worker --loglevel=info
```

Open Swagger:

```txt
http://localhost:8000/docs
```

## Running with Docker

The current `docker-compose.yml` starts Redis for local development:

```bash
docker compose up -d redis
```

The API and worker currently run from the local Python environment. A future Dockerization pass should add API and worker services plus a Dockerfile for fully containerized development.

When running inside Docker Compose, set Redis to the Compose service hostname:

```txt
REDIS_URL=redis://redis:6379/0
```

When running locally with Uvicorn, use localhost:

```txt
REDIS_URL=redis://localhost:6379/0
```

## GitHub App Setup

Create a GitHub App with these local development settings:

- Webhook URL: your ngrok URL plus `/webhooks/github`
- Webhook secret: same value as `GITHUB_WEBHOOK_SECRET`
- Subscribe to pull request events
- Install the app on the repository you want to review

Repository permissions should allow reading pull requests and contents, and writing pull request reviews or issue comments.

For local testing, a `GITHUB_TOKEN` can still be used as a fallback, but GitHub App installation tokens are the preferred path.

## Demo Workflow

1. A pull request is opened or updated.
2. GitHub sends a signed webhook to `/webhooks/github`.
3. FastAPI verifies the event and signature.
4. A Celery job is queued and the webhook returns quickly.
5. The worker fetches changed files, repository config, and repository context.
6. Guardrails skip oversized PRs before AI execution.
7. The AI review pipeline runs chunked, language-aware, multi-agent reviews.
8. Findings are filtered by confidence and valid changed lines.
9. GitHub receives inline review comments, or a fallback summary comment if inline publishing fails.
10. Redis metrics and telemetry are updated.

## Semantic Retrieval

Build the local repository context index:

```bash
python3 scripts/build_context_index.py
```

This creates local FAISS artifacts:

```txt
repo_context.index
repo_context_files.txt
```

These files are ignored by Git. The review pipeline uses the index to retrieve semantically related local files and injects that context into the AI reviewer prompt.

You can rebuild the index through the API:

```txt
POST /retrieval/reindex
x-admin-token: your ADMIN_API_TOKEN value
```

## Metrics APIs

Review metrics are stored in Redis and exposed through an admin-protected endpoint:

```txt
GET /metrics/reviews
x-admin-token: your ADMIN_API_TOKEN value
```

Example response:

```json
{
  "total_reviews": 0,
  "total_findings": 0,
  "avg_review_duration_seconds": 0,
  "avg_findings_per_review": 0,
  "repositories": {},
  "languages": {},
  "publish_modes": {}
}
```

## Example Screenshots

Demo screenshots should be added under [docs/screenshots](docs/screenshots):

- Swagger API with webhook, retrieval, and metrics endpoints.
- Successful metrics endpoint response.
- Inline GitHub PR comments.
- Celery worker logs processing a review.

## Future Roadmap

- Fully containerize API and worker services.
- Add automated tests for webhook validation, review service paths, and retrieval APIs.
- Add CI coverage for linting and test execution.
- Export OpenTelemetry traces to a collector.
- Add SaaS multi-tenancy for multiple GitHub installations.
- Move semantic retrieval to a managed vector database.
- Add historical PR learning from previous findings and fixes.
- Add human feedback loops for accepted, dismissed, and corrected AI findings.
- Add persistent review history storage and a metrics dashboard.
- Add deployment guides for Render, Railway, Fly.io, or AWS.
- Add screenshot and GIF demo assets for portfolio presentation.
