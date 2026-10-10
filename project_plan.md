# VERITAS AI - Project Plan & Product Vision

## 1. Product Vision
**VERITAS AI** is an intelligent, agent-driven platform built on the ResolveFlow architecture. It empowers organizations to make data-backed, high-stakes decisions through autonomous reasoning, semantic search, and human-in-the-loop workflows. By merging deep knowledge retrieval with safe, verifiable agent execution, VERITAS AI acts as a trusted operational brain for customer, market, and idea intelligence.

## 2. Scope & MVP Definition
The Minimum Viable Product (MVP) focuses on a secure, multi-tenant SaaS foundation that supports core agentic workflows. 
- **In Scope:** Tenant isolation, document ingestion (RAG), basic case intelligence, market trend summarization, idea tracking, interruptible LangGraph workflows, Next.js frontend, and evaluation pipelines.
- **Out of Scope:** Complex multi-agent negotiation, external third-party actions without human approval, billing integrations, and advanced predictive analytics.

## 3. Functional Requirements
- **FR1:** The system MUST isolate all data (documents, embeddings, chat history) by tenant.
- **FR2:** The system MUST support ingesting and embedding text documents into pgvector.
- **FR3:** The LangGraph agent MUST synthesize answers using only retrieved context.
- **FR4:** The system MUST pause execution (interrupt) and wait for human approval before committing high-risk actions.
- **FR5:** The system MUST stream reasoning steps and tool calls in real-time to the frontend via SSE.

## 4. Non-Functional Requirements
- **Security:** JWT-based RBAC, Row-Level Security (RLS) in PostgreSQL.
- **Performance:** SSE streaming must have a time-to-first-token (TTFT) of < 2 seconds. Vector search must return top-k results in < 200ms.
- **Observability:** All tool calls and state transitions must be logged with trace IDs.
- **Reliability:** The system must gracefully handle DeepSeek API rate limits using Redis.

## 5. Target Architecture & ADRs
- **ADR-001: LangGraph for Orchestration:** Chosen over raw LLM chains for cyclic reasoning and native human-in-the-loop (interrupt) support.
- **ADR-002: PostgreSQL + pgvector:** Chosen over dedicated vector DBs to simplify infrastructure and natively support tenant RLS alongside relational data.
- **ADR-003: DeepSeek Tool Calling:** Chosen for high reasoning capability and strict JSON tool-calling compliance.
- **ADR-004: Next.js App Router + SSE:** Chosen for server-side rendering and seamless real-time event streaming from FastAPI.

## 6. Unified Milestone Roadmap
- **M1: Foundation (Weeks 1-2):** Auth, Tenant Isolation, Next.js scaffolding, FastAPI base.
- **M2: Knowledge Engine (Weeks 3-4):** Document parsing, chunking, embedding, pgvector setup.
- **M3: Intelligence Features (Weeks 5-7):** Customer Case, Market, and Idea Intelligence agents.
- **M4: Safety & Workflow (Weeks 8-9):** LangGraph human-in-the-loop, SSE streaming UI.
- **M5: Eval & Launch (Week 10):** Security audits, evaluation pipelines, MVP release.

## 7. Prioritized Backlog
1. Setup PostgreSQL with RLS and pgvector.
2. Implement JWT Auth and tenant middleware in FastAPI.
3. Scaffold Next.js dashboard.
4. Build Document Ingestion Pipeline.
5. Implement LangGraph base agent with interrupt capabilities.
6. Build specific agent prompts (Customer, Market, Idea).
7. Develop SSE frontend consumption components.
8. Set up evaluation framework for RAG accuracy.

## 8. Risk Register
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM Hallucination | High | Medium | Strict RAG grounding prompts, human-in-the-loop for actions. |
| Tenant Data Leak | Critical | Low | PostgreSQL RLS, mandatory tenant_id on all queries, integration tests. |
| API Rate Limiting | Medium | High | Redis-based exponential backoff, request queuing. |

## 9. Definition of Done (DoD)
- Code is peer-reviewed and merged.
- Unit and integration tests pass (coverage > 80%).
- Type checking passes (TypeScript/Pyright).
- Feature is deployed to staging and manually verified.
- Architecture matches the Spec Kit plans.
- Tenant isolation is explicitly tested and verified.
