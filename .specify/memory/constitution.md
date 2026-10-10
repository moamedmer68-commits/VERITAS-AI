<!--
Sync Impact Report:
- Version change: 1.0.0 (Initial)
- Principles added: 5 principles (Agentic AI First, Robust RAG & Evidence Engine, Human-in-the-Loop, Tenant Isolation, Verifiability & Observability)
- Sections added: Architecture Constraints, Quality & Release Gates
- Governance rules defined.
-->
# VERITAS AI Constitution

## Core Principles

### I. Agentic AI First
All workflows should be designed with autonomous, agent-driven execution in mind. We leverage LangGraph and DeepSeek tool calling to build reliable, multi-step reasoning capabilities. Agents must have bounded scopes and clear termination conditions.

### II. Robust RAG & Evidence Engine
Knowledge retrieval is the foundation of our AI's accuracy. We mandate rigorous retrieval strategies using pgvector and Redis. All LLM responses must be backed by traceable evidence to minimize hallucination.

### III. Human-in-the-Loop Workflow
Critical decisions and irreversible actions MUST require human validation. We use LangGraph `interrupt()` mechanisms for human-in-the-loop approvals. The system should pause, await user confirmation, and seamlessly resume execution via the `Command(resume=...)` API.

### IV. Tenant Isolation & Security
As a SaaS foundation, data isolation is non-negotiable. Every database query, vector search, and LLM context window must enforce strict tenant boundaries. JWT-based Role-Based Access Control (RBAC) and row-level security (RLS) are mandatory.

### V. Verifiability & Observability
All AI reasoning and actions must be fully logged, explainable, and debuggable. Server-Sent Events (SSE) must stream agent states to the frontend in real-time. Structured logging is required for all backend components to facilitate tracing.

## Architecture Constraints

- **Backend:** FastAPI for REST/SSE endpoints. SQLAlchemy 2 + pgvector for data and vector storage.
- **Frontend:** Next.js (App Router), React, TypeScript.
- **AI/Agents:** LangGraph for orchestration, DeepSeek APIs for LLM inference.
- **State & Caching:** Redis for rate limiting and ephemeral state.
- **Infrastructure:** Dockerized deployments, managed via Docker Compose.

## Quality & Release Gates

- **Test-First (TDD):** Automated tests (Pytest for backend, TypeScript checks for frontend) are mandatory. 
- **Integration Testing:** All tool calling functions and LangGraph state transitions must have integration coverage.
- **Code Reviews:** All PRs require passing CI (GitHub Actions) and explicit review for tenant isolation and prompt security.

## Governance

This Constitution supersedes all other practices and documentation. 
Amendments to this document require a formal PR, justification, and approval from the architecture team. 
All pull requests must be validated against these Core Principles. Any complexity introduced must be justified by user value or security necessity.

**Version**: 1.0.0 | **Ratified**: 2026-10-09 | **Last Amended**: 2026-10-09
