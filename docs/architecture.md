# AI PR Review Assistant Architecture

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
   |-- PR Size Guardrails
   |-- Diff Chunking
   |-- Language Detection
   |-- Multi-Agent Reviewers
   |-- Repository Context Retrieval
   |-- Semantic Context Retrieval
   |-- Structured JSON Parsing
   `-- Confidence + Valid-Line Filtering
        |
GitHub Review Publisher
        |
Metrics + Telemetry
```

## Main Components

- **FastAPI webhook API** receives GitHub pull request events and validates GitHub webhook signatures.
- **Celery worker** moves expensive review work out of the request path.
- **Redis** acts as the Celery broker, idempotency store, and metrics store.
- **GitHub client** fetches pull request files, repository context files, and publishes review comments.
- **Review pipeline** chunks diffs, detects language, runs focused reviewer profiles, filters findings, and handles malformed AI output safely.
- **Retrieval layer** builds a local FAISS index and injects semantically related repository context into review prompts.
- **Metrics layer** records review counts, findings, duration, repositories, publish modes, and language distribution.

## Review Flow

1. GitHub sends a signed pull request webhook.
2. FastAPI verifies the event header and webhook signature.
3. The webhook handler queues a Celery job and returns immediately.
4. The worker fetches PR files and repo-level configuration.
5. Guardrails skip oversized PRs with a clear GitHub comment.
6. The pipeline builds diff context, retrieves repository context, and runs multi-agent reviewers.
7. Findings are filtered by confidence and valid changed lines.
8. The assistant publishes inline PR comments or falls back to a summary comment.
9. Metrics and telemetry capture review duration, findings, and publish mode.

## Stabilization Guardrails

- Duplicate webhook events are skipped with Redis idempotency keys.
- Oversized PRs are skipped before AI execution.
- Invalid AI JSON is converted into an empty structured review result.
- Inline review API failures fall back to a normal PR summary comment.
- Admin endpoints require `x-admin-token`.
