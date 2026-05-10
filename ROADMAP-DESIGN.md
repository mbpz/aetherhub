# AetherHub Competitive Analysis & Roadmap

**Document Version**: 1.0
**Date**: 2026-05-10
**Author**: Senior Software Architect
**Status**: Strategic Reference for 2026-2027

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Competitive Analysis Matrix](#2-competitive-analysis-matrix)
3. [AetherHub's Unique Differentiation Strategy](#3-etherhubs-unique-differentiation-strategy)
4. [Strengths to Preserve](#4-strengths-to-preserve)
5. [Critical Gaps and Enhancement Plans](#5-critical-gaps-and-enhancement-plans)
6. [Implementation Roadmap](#6-implementation-roadmap)
7. [Product Direction](#7-product-direction)
8. [Technical Architecture Evolution](#8-technical-architecture-evolution)
9. [Risk Assessment](#9-risk-assessment)

---

## 1. Executive Summary

### 1.1 Market Position

AetherHub occupies a **unique position** at the intersection of three converging trends:

1. **Skill Marketplace Boom**: The rise of AI agent platforms (Claude Code, Gemini CLI) has created demand for curated, verified skill repositories. SkillX.sh, echoskill, and ai-plugins represent the current state of this emerging market.

2. **Formal Verification Renaissance**: Z3 theorem proving, previously confined to academic and safety-critical systems, is now being explored for AI safety guarantees. No competitor currently applies this to skill/code verification at runtime.

3. **Dynamic Code Generation**: SWE-agent and mini-swe-agent have demonstrated that LLMs can generate and execute code. However, they lack the marketplace layer and verification that AetherHub proposes.

### 1.2 Unique Differentiators

| Differentiator | Description | Competitor Gap |
|----------------|-------------|----------------|
| **Z3 Formal Verification** | Mathematical proof of code safety before execution | No competitor does this |
| **Dynamic Skill Generation** | Generate skills on-demand from natural language | All competitors use static skills |
| **Wasm Execution Sandbox** | Lightweight, verifiable code execution | SWE-agent uses Docker; most use nothing |
| **ISMP Protocol** | Intent-to-skill mapping with constraint injection | No equivalent protocol |
| **Proof-Carrying Artifacts** | Every skill includes its Z3 verification proof | Not implemented anywhere |

### 1.3 Target Users

| Persona | Description | Primary Need |
|---------|-------------|---------------|
| **AI Agent Developers** | Developers building agents on Claude Code/Gemini CLI | Verified, secure skills |
| **Enterprise Security Teams** | Organizations requiring provably safe AI code execution | Formal verification guarantees |
| **Skill Creators** | Developers who want to publish and monetize skills | Marketplace with verification baked-in |
| **Researchers** | Academic/industry researchers on AI safety | Experimental verification pipeline |

### 1.4 Strategic Summary

**AetherHub's thesis**: The skill marketplace of 2027 will require what GitHub repos require today -- not just code, but proof of correctness. The combination of Z3 verification + dynamic generation + Wasm sandbox is **not being pursued by any known competitor**.

---

## 2. Competitive Analysis Matrix

### 2.1 Competitor Overview

| Project | Stars | License | Language | Primary Focus |
|---------|-------|---------|----------|---------------|
| SWE-agent | 19,178 | Apache 2.0 | Python | Autonomous bug fixing |
| OpenAI Swarm | 21,465 | MIT | Python | Multi-agent orchestration |
| mini-swe-agent | 4,275 | Apache 2.0 | Python | Minimal SWE-bench solver |
| SkillX.sh | 126 | Proprietary | TypeScript | Skill marketplace |
| echoskill | -- | MIT | Python | File-based skills |
| ai-plugins | -- | MIT | Python | Claude Code plugins |
| AgenticX-AgentSkills | 11 | MIT | Python | Skill marketplace (early) |
| squidbay | 3 | -- | HTML | A2A marketplace |

### 2.2 Technical Architecture Comparison

| Dimension | AetherHub | SkillX.sh | echoskill | ai-plugins | SWE-agent | mini-swe-agent | OpenAI Swarm | AgenticX | squidbay |
|-----------|-----------|-----------|-----------|------------|-----------|----------------|--------------|----------|----------|
| **Code Execution Sandbox** | Wasmtime (mock) | None | None | None | Docker/Podman | subprocess | None | Celery workers | None |
| **Formal Verification** | Z3 (partial) | None | None | None | None | None | None | None | None |
| **Dynamic Skill Generation** | Codex (mock) | No | No | No | N/A | N/A | No | No | No |
| **Tree-sitter AST** | Referenced, not integrated | No | No | No | No | No | No | No | No |
| **Skill Marketplace** | FastAPI (functional) | React Router v7 | File-based | File-based | No | No | No | Milvus | A2A protocol |
| **Search Engine** | Basic ILIKE | FTS5 + Vectorize | File search | None | N/A | N/A | N/A | Milvus | None |
| **Hybrid Search** | No | Yes (RRF fusion) | No | No | N/A | N/A | N/A | Yes | No |
| **Web Framework** | FastAPI + React | Cloudflare Workers | N/A | N/A | N/A | N/A | Python | FastAPI | HTML only |
| **Vector Database** | None | Cloudflare Vectorize | None | None | N/A | N/A | N/A | Milvus | None |
| **Database** | SQLite | D1 (Cloudflare) | Filesystem | Filesystem | N/A | N/A | In-memory | PostgreSQL | None |

### 2.3 Feature Comparison Matrix

| Feature | AetherHub | SkillX.sh | echoskill | ai-plugins | SWE-agent | mini-swe-agent | Swarm | AgenticX | squidbay |
|---------|-----------|-----------|-----------|------------|-----------|----------------|-------|----------|----------|
| **Skill CRUD** | Yes | Yes | Yes (files) | Yes (files) | N/A | N/A | No | Partial | No |
| **Search/Filter** | Basic | Advanced | File search | No | N/A | N/A | No | Yes | No |
| **Pagination** | 7 pages | Yes | N/A | N/A | N/A | N/A | No | Yes | No |
| **Star/Favorite** | Yes | Yes | No | No | N/A | N/A | No | No | No |
| **Leaderboard** | No | Yes | No | No | N/A | N/A | No | No | No |
| **Ratings/Reviews** | No | Yes | No | No | N/A | N/A | No | No | No |
| **GitHub OAuth** | Yes (mock) | Yes | No | No | N/A | N/A | No | No | No |
| **JWT Auth** | Yes (mock) | Yes | No | No | N/A | N/A | No | No | No |
| **File Upload** | Yes | No | Yes | Yes | N/A | N/A | No | No | No |
| **Categories** | 11 | Yes | No | No | N/A | N/A | No | No | No |
| **Tags** | Yes (10 max) | Yes | No | No | N/A | N/A | No | No | No |
| **Skill Versioning** | No | Yes | No | No | N/A | N/A | No | No | No |
| **Download Count** | Yes | Yes | No | No | N/A | N/A | No | No | No |
| **A2A Protocol** | No | No | No | No | N/A | N/A | No | No | Yes |
| **Micropayments** | No | No | No | No | N/A | N/A | No | No | Bitcoin Lightning |
| **Usage Analytics** | No | Yes | No | No | N/A | N/A | No | No | No |

### 2.4 Security & Verification Comparison

| Dimension | AetherHub | SkillX.sh | echoskill | ai-plugins | SWE-agent | mini-swe-agent | OpenAI Swarm | AgenticX | squidbay |
|-----------|-----------|-----------|-----------|------------|-----------|----------------|-------|----------|----------|
| **Formal Methods** | Z3 (partial) | None | None | None | None | None | None | None | None |
| **Code Verification** | Path-based | No | No | No | No | No | No | No | No |
| **Sandbox Execution** | Wasmtime (mock) | No | No | No | Docker | Bubblewrap | No | No | No |
| **Resource Limits** | Memory/time (mock) | N/A | N/A | N/A | Yes (Docker) | Yes | N/A | Celery limits | N/A |
| **Safe AST Parsing** | Tree-sitter (not integrated) | No | No | No | No | No | No | No | No |
| **Constraint Injection** | ISMP (functional) | No | No | No | No | No | No | No | No |

### 2.5 Integration Comparison

| Integration | AetherHub | SkillX.sh | echoskill | ai-plugins | SWE-agent | mini-swe-agent | OpenAI Swarm | AgenticX | squidbay |
|-------------|-----------|-----------|-----------|------------|-----------|----------------|-------|----------|----------|
| **Claude Code** | No | Yes (plugin marketplace) | Yes | Yes | No | No | No | No | No |
| **Gemini CLI** | No | No | Yes | No | No | No | No | No | No |
| **GitHub OAuth** | Yes (mock) | Yes | No | No | N/A | N/A | No | No | No |
| **CLI Tool** | No | Yes | Yes | No | bash only | bash only | No | No | No |
| **MCP Support** | No | No | No | Yes (OAuth retry) | No | No | No | No | No |
| **OpenAI API** | Codex (mock) | No | No | No | litellm | litellm | No | No | No |
| **Anthropic API** | No | No | No | No | litellm | litellm | No | No | No |

### 2.6 Business Model & License

| Dimension | AetherHub | SkillX.sh | echoskill | ai-plugins | SWE-agent | mini-swe-agent | OpenAI Swarm | AgenticX | squidbay |
|-----------|-----------|-----------|-----------|------------|-----------|----------------|-------|----------|----------|
| **License** | MIT | Proprietary | MIT | MIT | Apache 2.0 | Apache 2.0 | MIT | MIT | -- |
| **Open Source** | Yes | No | Yes | Yes | Yes | Yes | Yes | Yes | -- |
| **Monetization** | TBD | Pro tier | TBD | TBD | N/A | N/A | N/A | N/A | Micropayments |
| **Enterprise Support** | TBD | Yes | TBD | TBD | Meta/NVIDIA/IBM use | No | No | No | No |

---

## 3. AetherHub's Unique Differentiation Strategy

### 3.1 The Verification Gap

**No competitor combines all four of these:**

1. Skill marketplace with discovery/browse
2. Formal Z3 verification of generated code
3. Dynamic skill generation (not just static repos)
4. Wasm execution sandbox

### 3.2 The "Proof-Carrying Skills" Concept

Every skill in AetherHub should carry a Z3 proof that demonstrates:

- The skill's code does not access forbidden resources
- The skill terminates within time/memory bounds
- The skill's logic is consistent with its specification

**This is analogous to:**
- Git signed commits (provenance)
- Reproducible builds (verifiable artifacts)
- Type signatures (interface contracts)

### 3.3 ISMP as a Protocol Layer

The Intent-Skill Mapping Protocol (ISMP) provides:

```
User Intent → Semantic Vector → Capability Space → Atomic Skills → Generated Code → Z3 Proof → Wasm Execution
```

**Competitors skip steps 1-5 and just host static files.**

### 3.4 Strategic Position

```
                    Static Skills
                         |
           +-------------+-------------+
           |                           |
     SkillX.sh                   echoskill/ai-plugins
           |                           |
           +---- Skill Marketplace ----+
                         |
                    AetherHub
                    (with Z3 + Wasm + Dynamic Generation)
                         |
                    Future Position
```

**AetherHub is not competing with SkillX.sh -- it is building toward a different future.**

---

## 4. Strengths to Preserve

### 4.1 Architecture Strengths

| Strength | Evidence | Why It Matters |
|----------|----------|----------------|
| **ISMP Protocol Design** | `ismp/protocol.py` is well-structured with semantic vectorization, capability mapping, and constraint injection | Provides the foundation for dynamic skill generation |
| **Multi-layer Defense** | Blueprint shows 4-layer security (ISMP → Codex → Z3 → Wasm) | Correct architecture for a verification-first system |
| **Separation of Concerns** | Skills engine vs web platform are cleanly separated | Allows independent evolution |
| **SQLAlchemy ORM** | `web/backend/models.py` uses proper relationships and migrations | Enterprise-ready data model |
| **RESTful API Design** | Skills routes follow proper REST conventions | Standard, interoperable interface |
| **Tag Validation** | TC-05-18 ensures max 10 tags | Prevents spam, maintains quality |
| **File Type Allowlist** | Only `.py`, `.md`, `.txt`, `.json`, `.yaml`, `.yml`, `.toml` allowed | Security boundary |

### 4.2 Process Strengths

| Strength | Evidence | Why It Matters |
|----------|----------|----------------|
| **Comprehensive Test Suite** | 87 test cases, 30/31 passing | Regression prevention, confidence |
| **Chinese Documentation** | ISMP protocol spec, blueprint fully documented | Project clarity |
| **Seed Data Strategy** | 5 demo skills auto-seeded | Instant demo capability |
| **GitHub OAuth Integration** | Auth flow implemented (mock mode) | Future-ready for real OAuth |
| **Category System** | 11 categories defined | Discoverability |

### 4.3 Code Quality Observations

| Area | Assessment | Notes |
|------|------------|-------|
| **Error Handling** | Good | `err_response()` helper, proper HTTP codes |
| **Input Validation** | Good | Regex for skill name, version format, tag limits |
| **Path Safety** | Good | `safe_filename()` prevents traversal |
| **Type Safety** | Moderate | Some `Any` types, could use more generics |
| **Documentation** | Good | Chinese docs comprehensive |

---

## 5. Critical Gaps and Enhancement Plans

### 5.1 Gap 1: No Real Code Execution (Wasm Mock)

**Current State**: `execution/wasmtime.py` returns mock results. No actual Wasm compilation.

**Required Actions**:

| Priority | Action | Technical Approach |
|----------|--------|-------------------|
| Critical | Integrate wasmtime Python binding | `pip install wasmtime`, use `wasmtime.Engine()`, `wasmtime.Module()`, `wasmtime.Linker()` |
| Critical | Implement Python-to-Wasm compilation | Use `py2wasm` or transpile Python AST to Wasm |
| Important | Add resource limit enforcement | Memory tracking via `wasmtime.Store()` limits |
| Important | Implement execution timeout | Use `wasmtime.Store().set_deadline()` |

**Verification**: Execute `python main.py` and confirm Wasm execution completes.

### 5.2 Gap 2: No Real Code Generation (Codex Mock)

**Current State**: `codex/engine.py` returns hardcoded placeholder code.

**Required Actions**:

| Priority | Action | Technical Approach |
|----------|--------|-------------------|
| Critical | Enable OpenAI API client | Uncomment `openai` client in `codex/engine.py` |
| Critical | Implement skill template prompts | Create prompt library for atomic skills (read_file, write_file, filter_data, etc.) |
| Important | Implement iterative refinement | On Z3 failure, feed counterexample back to Codex for regeneration |
| Important | Add code quality scoring | LLM-based assessment before Z3 verification |

**Verification**: Pass a real intent like "filter CSV where age > 18" and receive valid Python code.

### 5.3 Gap 3: No Tree-sitter AST Extraction

**Current State**: `tree_sitter` is passed as `None` in `main.py`. Z3 verification uses simplified path analysis.

**Required Actions**:

| Priority | Action | Technical Approach |
|----------|--------|-------------------|
| Critical | Install tree-sitter Python binding | `pip install tree-sitter` |
| Critical | Add language parsers | Install `tree-sitter-python`, `tree-sitter-javascript`, etc. |
| Critical | Implement AST-to-formula conversion | Extract path constraints, loop bounds, function calls from AST |
| Important | Add Z3 formula generation from AST | Convert Python AST to Z3 Bool/Int/Real expressions |

**Verification**: Parse a Python function and extract its symbolic execution path as Z3 constraints.

### 5.4 Gap 4: No Hybrid Semantic Search

**Current State**: `web/backend/routes/skills.py` uses basic `ILIKE` + `contains()` for search.

**Required Actions**:

| Priority | Action | Technical Approach |
|----------|--------|-------------------|
| Important | Add vector embeddings | Use `sentence-transformers` to embed skill descriptions |
| Important | Integrate vector database | Options: Qdrant (self-hosted), Pinecone (managed), or simple FAISS |
| Important | Implement RRF fusion ranking | Combine keyword (BM25) + vector (cosine) with Reciprocal Rank Fusion |
| Nice-to-have | Add skill similarity search | "Skills similar to X" feature |

**Reference**: SkillX.sh achieves <800ms p95 with Cloudflare Vectorize + FTS5 + RRF.

**Verification**: Search "data processing" returns skills with vector similarity + keyword match ranked by RRF.

### 5.5 Gap 5: No Claude Code / Gemini CLI Plugin

**Current State**: No agent integration exists.

**Required Actions**:

| Priority | Action | Technical Approach |
|----------|--------|-------------------|
| Important | Implement Claude Code plugin format | Create `.claude` directory with `commands/` and `skills/` |
| Important | Design skill installation API | `claude skill install aetherhub/my-skill` |
| Important | Build skill sync daemon | Keep local skills in sync with AetherHub marketplace |
| Nice-to-have | Gemini CLI plugin | Follow similar approach with Gemini's plugin system |

**Reference**: SkillX.sh and ai-plugins have already done Claude Code integration.

### 5.6 Gap 6: No A2A / Agent-to-Agent Protocol

**Current State**: No A2A support.

**Required Actions**:

| Priority | Action | Technical Approach |
|----------|--------|-------------------|
| Nice-to-have | Study squidbay A2A model | Agent-to-agent skill discovery + Bitcoin Lightning |
| Nice-to-have | Implement A2A client | Allow agents to request skills from AetherHub at runtime |
| Nice-to-have | Add skill negotiation | Agents can request custom skill generation |

**Note**: This is a future direction; not critical for Phase 1-2.

### 5.7 Gap 7: No Skill Version Management

**Current State**: Skills have a `version` field but no version history.

**Required Actions**:

| Priority | Action | Technical Approach |
|----------|--------|-------------------|
| Important | Add version history table | `skill_versions` table with full snapshot |
| Important | Implement version diff | Show what changed between versions |
| Important | Add deprecation workflow | Mark old versions as deprecated |

### 5.8 Gap 8: No Usage Analytics / Leaderboard

**Current State**: `download_count` and `star_count` exist but no analytics dashboard.

**Required Actions**:

| Priority | Action | Technical Approach |
|----------|--------|-------------------|
| Nice-to-have | Add usage tracking | Log every skill execution with timestamp, user, intent |
| Nice-to-have | Build analytics dashboard | React dashboard with charts (downloads, stars, recency) |
| Nice-to-have | Implement leaderboard | Top skills by weekly downloads/stars |

### 5.9 Gap 9: No Real-Time Skill Validation Pipeline

**Current State**: Skills are uploaded and stored; no validation on upload.

**Required Actions**:

| Priority | Action | Technical Approach |
|----------|--------|-------------------|
| Important | Add skill schema validation | Validate SKILL.md structure (like echoskill's format) |
| Important | Implement security scanning | Check for dangerous patterns in uploaded Python |
| Important | Add Z3 pre-verification | Verify skill constraints before publishing |

### 5.10 Gap 10: Pagination Limited to 7 Pages

**Current State**: `size=20` with basic pagination formula.

**Required Actions**:

| Priority | Action | Technical Approach |
|----------|--------|-------------------|
| Low | Fix pagination calculation | Current code appears correct; investigate if "7 pages" is a display issue |
| Low | Add cursor-based pagination | For high-volume APIs, cursor pagination is more efficient |

---

## 6. Implementation Roadmap

### 6.1 Phase 1: Foundation (2026 Q2)

**Goal**: Make the core engine functional -- real Z3, real Wasm, real Codex.

#### Phase 1A: Fix Critical Mocks (Weeks 1-4)

| Week | Task | Deliverable |
|------|------|-------------|
| 1 | Integrate OpenAI Codex API | `codex/engine.py` generates real code |
| 2 | Integrate tree-sitter Python | `verification/tree_sitter.py` parses Python AST |
| 3 | Implement AST-to-Z3 conversion | `verification/z3_verifier.py` uses real AST formulas |
| 4 | Integrate wasmtime | `execution/wasmtime.py` compiles and runs Wasm |

#### Phase 1B: Verification Pipeline (Weeks 5-8)

| Week | Task | Deliverable |
|------|------|-------------|
| 5 | Implement path constraint extraction | Extract file path constraints from AST |
| 6 | Implement loop bound verification | Verify loops won't exceed time limits |
| 7 | Implement iterative refinement loop | Codex regenerates on Z3 failure |
| 8 | End-to-end test | Full "intent → code → Z3 → Wasm" pipeline |

#### Phase 1C: Web Platform Hardening (Weeks 9-12)

| Week | Task | Deliverable |
|------|------|-------------|
| 9 | Replace mock OAuth with real GitHub OAuth | `web/backend/routes/auth.py` full OAuth flow |
| 10 | Add JWT refresh tokens | Token expiry handling |
| 11 | Implement skill version history | `skill_versions` table |
| 12 | Add skill validation on upload | SKILL.md schema validation |

**Phase 1 Success Metrics**:
- [ ] 31/31 tests passing
- [ ] `python main.py` produces verified, executed code (not mocks)
- [ ] GitHub OAuth works in production mode
- [ ] Skills can be uploaded with real Z3 proof attached

### 6.2 Phase 2: Execution (2026 Q3)

**Goal**: Build the marketplace layer and agent integrations.

#### Phase 2A: Skill Marketplace (Weeks 13-18)

| Week | Task | Deliverable |
|------|------|-------------|
| 13-14 | Implement hybrid search | Vector embeddings + FTS5 + RRF fusion |
| 15 | Add skill categories with counts | `/skills/categories` endpoint |
| 16 | Build skill detail page | Full SKILL.md rendering, file browser |
| 17 | Implement skill ratings | Star system with review text |
| 18 | Add skill versioning UI | Version diff viewer |

#### Phase 2B: Claude Code Integration (Weeks 19-22)

| Week | Task | Deliverable |
|------|------|-------------|
| 19 | Design Claude Code plugin structure | `.claude/commands/` + `skills/` |
| 20 | Implement skill install command | `claude skill install <name>` |
| 21 | Build skill sync mechanism | Webhook + polling for updates |
| 22 | Test end-to-end | Install and execute a skill from Claude Code |

#### Phase 2C: Advanced Features (Weeks 23-26)

| Week | Task | Deliverable |
|------|------|-------------|
| 23-24 | Usage analytics dashboard | Download trends, star history |
| 25 | Leaderboard | Top skills by week/month |
| 26 | A2A protocol exploration | Design draft for agent-to-agent skill request |

**Phase 2 Success Metrics**:
- [ ] Hybrid search responds < 800ms p95
- [ ] Claude Code plugin installs and executes skills
- [ ] Leaderboard displays top skills
- [ ] Usage analytics visible per skill

### 6.3 Phase 3: Scale (2026 Q4)

**Goal**: Enterprise features, performance optimization, community building.

#### Phase 3A: Performance (Weeks 27-30)

| Week | Task | Deliverable |
|------|------|-------------|
| 27 | Cursor-based pagination | Handle 10,000+ skills efficiently |
| 28 | Query result caching | Redis caching for popular searches |
| 29 | Parallel Z3 verification | Multi-core solver utilization |
| 30 | Load testing | Identify bottlenecks under 1000 concurrent users |

#### Phase 3B: Enterprise (Weeks 31-34)

| Week | Task | Deliverable |
|------|------|-------------|
| 31 | Private skill visibility | Organization-scoped skills |
| 32 | Skill approval workflow | Moderation queue |
| 33 | API rate limiting | Per-user limits |
| 34 | Audit logging | Full action history |

#### Phase 3C: Community (Weeks 35-39)

| Week | Task | Deliverable |
|------|------|-------------|
| 35 | Contributor guide | How to add atomic skills |
| 36 | Skill template marketplace | Pre-built skill templates |
| 37 | Community leaderboard | Contributor rankings |
| 38 | Integration with GitHub Actions | CI/CD skill verification |
| 39 | Public beta launch | Open registration |

**Phase 3 Success Metrics**:
- [ ] < 200ms average API response
- [ ] 1000+ registered users
- [ ] 100+ public skills
- [ ] 50+ Claude Code installations

### 6.4 Roadmap Summary Table

| Phase | Timeframe | Focus | Key Milestones |
|-------|-----------|-------|----------------|
| Phase 1 | 2026 Q2 | Foundation | Real Z3, Wasm, Codex; OAuth; Version history |
| Phase 2 | 2026 Q3 | Execution | Hybrid search; Claude Code plugin; Analytics |
| Phase 3 | 2026 Q4 | Scale | Performance; Enterprise; Community |

---

## 7. Product Direction

### 7.1 Target User Personas

| Persona | Description | Goals | Pain Points |
|---------|-------------|-------|-------------|
| **Alice (AI Agent Developer)** | Builds agents on Claude Code | Integrate verified skills | "I need skills I can trust not to execute malicious code" |
| **Bob (Security Engineer)** | Enterprise security team | Prove AI code is safe | "Our compliance team needs formal verification, not trust" |
| **Carol (Skill Creator)** | Publishes Python skills | Earn recognition for skills | "GitHub stars don't tell me if my skill is actually correct" |
| **David (AI Researcher)** | Studies AI safety | Experiment with verification | "No good testbed for Z3 + skill generation" |

### 7.2 Primary Use Cases

| Use Case | User | Flow | Success Metric |
|----------|------|------|----------------|
| **Skill Discovery** | Alice | Browse marketplace → search → filter → star | Finds useful skill in < 5 min |
| **Skill Execution** | Alice | Install skill → invoke → get result | Skill executes correctly in Claude Code |
| **Skill Upload** | Carol | Upload SKILL.md → validation → publish | Skill published with Z3 proof |
| **Verification Request** | Bob | Submit code → Z3 verify → receive proof | Proof delivered in < 10s |
| **Dynamic Generation** | David | Send intent → ISMP → Codex → Z3 → Wasm | Functional skill generated |

### 7.3 Success Metrics

| Metric | Phase 1 Target | Phase 2 Target | Phase 3 Target |
|--------|----------------|----------------|----------------|
| **Test Pass Rate** | 31/31 (100%) | 45/45 | 60/60 |
| **Z3 Verification Time** | < 1s | < 500ms | < 200ms |
| **Wasm Execution Time** | < 500ms | < 200ms | < 100ms |
| **Search Latency (p95)** | N/A | < 800ms | < 200ms |
| **API Availability** | 99% | 99.5% | 99.9% |
| **Registered Users** | -- | 100 | 1000 |
| **Public Skills** | -- | 50 | 500 |
| **Claude Code Installs** | -- | 10 | 100 |

### 7.4 Pricing Model (Future)

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0 | 10 skills, 100 verifications/month, public marketplace |
| **Pro** | $9/mo | Unlimited skills, 1000 verifications/month, private skills |
| **Enterprise** | Custom | Unlimited, SSO, SLA, on-premise deployment |

---

## 8. Technical Architecture Evolution

### 8.1 Current Architecture

```
                    ┌─────────────────┐
                    │  User Intent    │
                    └────────┬────────┘
                             │
                             ▼
┌──────────────────────────────────────────────┐
│           ISMP Protocol (Python)              │
│  ┌─────────────┬─────────────┬────────────┐ │
│  │ Semantic    │ Capability  │ Constraint │ │
│  │ Vectorizat. │ Mapping     │ Injection  │ │
│  └─────────────┴─────────────┴────────────┘ │
└──────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────┐
│           Codex Engine (Mock)                 │
│  Returns hardcoded placeholder code          │
└──────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────┐
│           Z3 Verifier (Partial)               │
│  Simplified path analysis, not full AST      │
└──────────────────────────────────────────────┘
                             │
                             ▼
┌──────────────────────────────────────────────┐
│         Wasmtime Sandbox (Mock)               │
│  Returns mock execution results              │
└──────────────────────────────────────────────┘
```

### 8.2 Target Architecture (Phase 2)

```
┌──────────────────────────────────────────────────────────────────┐
│                          User Intent                             │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FastAPI Web Platform                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │
│  │ Auth     │  │ Skills   │  │ Search   │  │ Claude Code      │ │
│  │ (OAuth)  │  │ CRUD     │  │ (Hybrid) │  │ Plugin Server    │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │
└───────────────────────────────┬──────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                 Skills Engine (Python)                           │
│  ┌─────────────┬─────────────┬────────────┬─────────────────┐  │
│  │ ISMP        │ Codex       │ Tree-sitter│ Z3 Verifier     │  │
│  │ Protocol    │ (Real API)  │ AST Parse  │ (Full logic)    │  │
│  └─────────────┴─────────────┴────────────┴─────────────────┘  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Wasmtime Sandbox (Real execution)                          │ │
│  └─────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                   Data Layer                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
│  │ SQLite   │  │ Qdrant   │  │ Redis    │  │ File Storage   │  │
│  │ (Skills) │  │ (Embed-  │  │ (Cache)  │  │ (uploads/)     │  │
│  │          │  │ dings)    │  │          │  │                │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

### 8.3 Component Evolution Plan

| Component | Current State | Phase 1 Target | Phase 2 Target |
|-----------|---------------|----------------|----------------|
| **Codex Engine** | Mock returns placeholder | Real OpenAI API calls | Iterative refinement loop |
| **Tree-sitter** | None | Python AST parsing | Multi-language (JS, Go, Rust) |
| **Z3 Verifier** | Path-based only | Full AST formula extraction | Parallel solving, incremental |
| **Wasmtime** | Mock results | Real Wasm execution | Python→Wasm transpilation |
| **Search** | Basic ILIKE | -- | Hybrid (Vector + FTS5 + RRF) |
| **Database** | SQLite | SQLite | PostgreSQL (for scale) |
| **Cache** | None | None | Redis |
| **Vector DB** | None | None | Qdrant (self-hosted) |

### 8.4 Data Model Evolution

**Current**: Single `Skill` table with JSON tags

**Phase 2**:
```
users ───1:N─── skills
                  │
                  ├──── 1:N ─── skill_versions
                  ├──── 1:N ─── skill_files
                  ├──── 1:N ─── skill_stars
                  └──── 1:N ─── skill_ratings
```

**Phase 3**:
```
users ───1:N─── skills ───1:N─── skill_metrics
      │                           │
      └── organizations ───1:N─── │ (org-scoped skills)
```

---

## 9. Risk Assessment

### 9.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Z3 solver performance** | High | Medium | Parallel solving, rule optimization, incremental SAT |
| **Wasm compilation overhead** | Medium | High | Pre-compile common patterns, use cached modules |
| **Tree-sitter parser bugs** | Medium | Low | Comprehensive test suite, upstream contributions |
| **OpenAI API rate limits** | High | Medium | Caching, batch verification, fallback to local models |
| **Python-to-Wasm transpilation gaps** | High | High | Use Pyodide for full Python, or limit to subset |

### 9.2 Product Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Market timing** | High | Medium | The verification gap is real but market may not mature |
| **Competition** | Medium | High | SkillX.sh could add verification; differentiate early |
| **User adoption** | High | High | Focus on Claude Code integration as adoption vector |
| **Community building** | Medium | High | Seed with high-quality skills, contributor incentives |

### 9.3 Security Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Z3 bypass** | Critical | Low | Defense in depth (ISMP → Codex → Z3 → Wasm) |
| **Malicious skill upload** | High | Medium | Sandboxing, scanning, reputation system |
| **OAuth token theft** | High | Low | HTTPS only, secure cookie flags, short expiry |
| **Wasm escape** | High | Low | Resource limits, seccomp, landlock |

### 9.4 Operational Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Infrastructure cost** | Medium | High | Start with SQLite + local vector, scale as needed |
| **Team bandwidth** | High | High | Phase 1 focus on core engine, defer web improvements |
| **Technical debt** | Medium | High | Refactor mocks immediately when replacing with real code |

### 9.5 Risk Priority Matrix

| | Low Probability | High Probability |
|---|---|---|
| **High Impact** | Z3 solver perf, Wasm escape, Market timing | User adoption, Team bandwidth, Infrastructure cost |
| **Low Impact** | Tree-sitter bugs, OAuth token theft | Community building, Competition |

**Primary Focus Areas** (High Impact + High Probability):
1. User adoption via Claude Code integration
2. Team bandwidth management (realistic scope)
3. Infrastructure cost control
4. Competition monitoring (SkillX.sh)

---

## Appendix A: Competitive Reference Summary

| Project | URL | Key Innovation | Relevance |
|---------|-----|----------------|-----------|
| SWE-agent | github.com/princeton-nlp/SWE-agent | Minimalist agent, SoTA on SWE-bench | Demonstrates power of simplicity |
| mini-swe-agent | github.com/SWE-agent/mini-swe-agent | 100-line agent, 74%+ accuracy | Minimalism wins |
| OpenAI Swarm | github.com/openai/swarm | Multi-agent handoffs | Educational reference |
| SkillX.sh | nextlevelbuilder/skillx | Hybrid search, professional UI | Closest marketplace competitor |
| echoskill | echo-skill/echoskill | SKILL.md format, cross-agent | Skill convention standard |
| ai-plugins | lakamsani/ai-plugins | Claude Code integration | Agent integration reference |
| AgenticX | DemonDamon/AgenticX-AgentSkills | Milvus + Celery architecture | Infrastructure reference |
| squidbay | squidbay/ | A2A + micropayments | Future direction signal |

---

## Appendix B: Technology Stack Recommendations

| Layer | Current | Phase 1 | Phase 2 | Phase 3 |
|-------|---------|---------|---------|---------|
| **Web Framework** | FastAPI | FastAPI | FastAPI + GraphQL | FastAPI + GraphQL |
| **Database** | SQLite | SQLite | PostgreSQL | PostgreSQL |
| **Cache** | None | None | Redis | Redis Cluster |
| **Vector DB** | None | None | Qdrant | Qdrant |
| **Code Generation** | Mock | OpenAI | OpenAI + Anthropic | Multi-model |
| **Verification** | Z3 (partial) | Z3 (full) | Z3 + Verifier | Z3 + Verifier |
| **Sandbox** | Mock | Wasmtime | Wasmtime + Pyodide | Wasmtime + Pyodide |
| **Search** | ILIKE | ILIKE | Hybrid (this, vector) | Hybrid + Analytics |
| **AST Parsing** | None | tree-sitter | tree-sitter | tree-sitter |

---

## Appendix C: Key Files Reference

| File | Purpose | Priority |
|------|---------|----------|
| `/Users/doug/ai/system/aetherhub/main.py` | Skills engine entry point | Phase 1 |
| `/Users/doug/ai/system/aetherhub/codex/engine.py` | Code generation (currently mock) | Phase 1 |
| `/Users/doug/ai/system/aetherhub/verification/z3_verifier.py` | Z3 verification (partial) | Phase 1 |
| `/Users/doug/ai/system/aetherhub/execution/wasmtime.py` | Wasm sandbox (mock) | Phase 1 |
| `/Users/doug/ai/system/aetherhub/ismp/protocol.py` | ISMP protocol | Preserve |
| `/Users/doug/ai/system/aetherhub/web/backend/main.py` | FastAPI app | Phase 2 |
| `/Users/doug/ai/system/aetherhub/web/backend/routes/skills.py` | Skill CRUD + search | Phase 2 |
| `/Users/doug/ai/system/aetherhub/web/backend/models.py` | Database models | Preserve |

---

**Document End**

*This document should be reviewed quarterly and updated to reflect market changes and project progress.*