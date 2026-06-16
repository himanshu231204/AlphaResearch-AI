# AlphaResearch AI — Implementation Plan

---

## Phase 1 — ✅ DONE

**Date**: 2025-06-15

Autonomous AI Equity Research Platform — Phase 1.
Single stock analysis with LangGraph supervisor + DeepAgents + LiteLLM model routing.

### Architecture (Phase 1)

```
User Query → FastAPI → LangGraph Supervisor → DeepAgents (Research + Financial) → Writer → Report
                                          ↕
                                    Reflection Loop (max 3)
                                          ↕
                                    LiteLLM Model Router (ChatLiteLLM)
```

### Files Created (Phase 1)

| File | Description |
|------|-------------|
| `pyproject.toml` | Project metadata, all dependencies |
| `env.example` | API key template |
| `app/config.py` | pydantic-settings config class |
| `models/state.py` | `ResearchState` TypedDict — LangGraph state schema |
| `models/routing.py` | Centralized ChatLiteLLM model routing |
| `tools/financial_tools.py` | 5 LangChain `@tool` functions |
| `tools/search_tools.py` | 2 LangChain `@tool` functions |
| `agents/research_deep_agent.py` | Research DeepAgent with web-researcher subagent |
| `agents/financial_deep_agent.py` | Financial DeepAgent |
| `agents/writer.py` | LangChain chain for report generation |
| `agents/supervisor.py` | LangGraph StateGraph supervisor |
| `prompts/workflow.py` | System prompts |
| `app/main.py` | FastAPI app |
| `app/api/research.py` | `POST /api/research` endpoint |
| `rag/chroma_store.py` | ChromaDB vector store (stub) |
| `tests/test_agents.py` | 5 tests |
| `tests/test_api.py` | 2 tests |
| `tests/test_tools.py` | 4 tests |

---

## Phase 2 — ✅ DONE

**Date**: 2025-06-15

Added Technical Analysis agent, LLM-driven Reflection loops, and Company Comparison capability.

### Architecture (Phase 2)

```
User Query → FastAPI → LangGraph Supervisor
                              │
                 ┌────────────┴────────────┐
                 │ Parallel Fan-Out         │
                 ▼                          ▼
     ┌──────────────────┐      ┌──────────────────┐
     │ Research Branch   │      │ Technical Branch  │
     │ (Research Agent   │      │ (Technical Agent   │
     │  + Financial Agent│      │  + Web Research)   │
     │  + Web Research)  │      │                    │
     └────────┬─────────┘      └────────┬──────────┘
              │                          │
              └────────────┬─────────────┘
                           ▼
                      Aggregate
                           │
                 ┌─────────┴─────────┐
                 │ Single or Compare? │
                 └─────────┬─────────┘
                           ▼
                    ┌──────────────┐
                    │ Reflection   │ (LLM-driven, max 3 cycles)
                    └──────┬───────┘
                           ▼
                      Writer → Report
```

### What Changed in Phase 2

| Component | Before | After |
|-----------|--------|-------|
| Supervisor | Heuristic-only (keyword matching) | LLM-powered with structured output (`QueryType`) |
| Graph topology | Sequential (research → financial) | Parallel fan-out (research+financial ‖ technical) |
| Technical analysis | Tool function only | Dedicated DeepAgent (Grok + web research) |
| Reflection | Heuristic string checks | LLM-driven quality review |
| Company comparison | Did not exist | New agent + `/api/compare` endpoint |

### New Files (Phase 2)

| File | Description |
|------|-------------|
| `tools/technical_tools.py` | 4 tools: `calculate_technical_indicators`, `get_support_resistance`, `get_volume_analysis`, `get_trend_analysis` |
| `tools/comparison_tools.py` | 3 tools: `compare_financials`, `compare_technicals`, `compare_valuation` |
| `agents/technical_agent.py` | Technical analysis DeepAgent (Grok + technical tools + web research) |
| `agents/comparison_agent.py` | Company comparison DeepAgent (Gemini 2.5 Pro + comparison tools + web research) |
| `tests/test_technical.py` | 6 tests for technical tools |
| `tests/test_comparison.py` | 3 tests for comparison tools |

### Modified Files (Phase 2)

| File | Changes |
|------|---------|
| `models/state.py` | Added `query_type`, `technical_analysis`, `comparison_results`, `target_companies` |
| `agents/supervisor.py` | Complete rewrite — LLM supervisor, parallel graph, aggregate node, comparison node, LLM reflection |
| `prompts/workflow.py` | Added `TECHNICAL_AGENT_PROMPT`, `COMPARISON_AGENT_PROMPT`, `COMPETITOR_RESEARCH_PROMPT`; updated supervisor, reflection, writer prompts |
| `agents/writer.py` | Extended prompt template with `technical_analysis` and `comparison_results` |
| `app/api/research.py` | Updated response model, added `POST /api/compare` endpoint |
| `tools/financial_tools.py` | Removed `calculate_technical_indicators` (moved to `technical_tools.py`) |
| `tests/test_agents.py` | Updated for new state schema, routing, graph |
| `tests/test_tools.py` | Updated imports for moved tools |

### Tests (Phase 2)

```
24 passed in 67.98s

tests/test_agents.py      — 8 passed
tests/test_api.py         — 2 passed
tests/test_comparison.py  — 3 passed
tests/test_technical.py   — 6 passed
tests/test_tools.py       — 5 passed
```

### Model Routing (unchanged from Phase 1)

| Task | Model | Provider |
|------|-------|----------|
| Planning/Supervisor | `gemini/gemini-2.5-pro` | Google |
| Research | `xai/grok-3` | xAI |
| Financial Analysis | `gemini/gemini-2.5-pro` | Google |
| Technical Analysis | `xai/grok-3` | xAI |
| Reflection | `gemini/gemini-2.5-pro` | Google |
| Report Writing | `gemini/gemini-2.5-pro` | Google |
| Quick Summaries | `gemini/gemini-2.0-flash` | Google |

---

## Next Phases

| Phase | Features |
|-------|----------|
| Phase 3A | ✅ DONE — Streaming, Stores, Persistence, Fault Tolerance |
| Phase 3B | ✅ DONE — Subgraphs, Interrupts, Memory |
| Phase 4 | Annual report RAG, earnings call analysis (ChromaDB already stubbed) |
| Phase 5 | Portfolio analysis, sector analysis |
| Phase 6 | Autonomous daily research reports |
| Phase 7 | Institutional-grade market intelligence platform |

---

## Phase 3A — ✅ DONE

**Date**: 2025-06-16

Added critical LangGraph production capabilities: Streaming, Stores, Persistence, and Fault Tolerance.

### What Was Added (Phase 3A)

| Capability | Implementation | Details |
|------------|---------------|---------|
| **Streaming** | Agent Server auto-handles | `stream_mode` via LangGraph Agent Server — no code changes needed |
| **Stores** | `InMemoryStore` in graph compilation | Cross-thread long-term memory for user preferences and research history |
| **Persistence** | `MemorySaver` checkpointer | Per-thread checkpointing — Agent Server auto-persists via its backend |
| **Fault Tolerance** | `RetryPolicy` on all agent nodes | `max_attempts=3`, `backoff_factor=2.0` exponential backoff on transient API failures |

### Modified Files (Phase 3A)

| File | Changes |
|------|---------|
| `pyproject.toml` | Added `langgraph-cli[inmem]` dependency |
| `graph.py` | **NEW** — LangGraph Server entry point, re-exports `graph` from `agents.supervisor` |
| `langgraph.json` | **NEW** — LangGraph Server config pointing to `graph.py:graph` |
| `agents/supervisor.py` | Added `InMemoryStore`, `MemorySaver`, `RetryPolicy` on all agent nodes |
| `agents/supervisor.py` | Added message extraction from `messages` list for Agent Chat UI compatibility |

### Frontend Setup (Phase 3A)

| Component | Status | Details |
|-----------|--------|---------|
| LangGraph Agent Server | Running | `langgraph dev` serves at `http://localhost:2024` |
| Agent Chat UI | Cloned | Next.js frontend in `frontend/` directory |
| Connection | Configured | `frontend/.env` points to `localhost:2024` |

---

## Phase 3B — ✅ DONE

**Date**: 2025-06-16

Added proper LangGraph subgraphs, human-in-the-loop interrupts, and store-based memory.

### What Was Added (Phase 3B)

| Capability | Implementation | Details |
|------------|---------------|---------|
| **Subgraphs** | `build_research_analysis_subgraph()` | Research+financial branch as proper LangGraph subgraph with shared state mapping |
| **Subgraphs** | `build_technical_analysis_subgraph()` | Technical analysis as proper LangGraph subgraph with shared state mapping |
| **Subgraphs** | `add_node("research_analysis", subgraph)` | Subgraphs added via `add_node()` — automatic state key mapping |
| **Interrupts** | `interrupt()` in `writer_node` | Human-in-the-loop approval before report generation — pauses graph, surfaces to Agent Chat UI |
| **Memory** | `_load_user_preferences()` | Loads user preferences from store at supervisor startup |
| **Memory** | `_save_query_to_store()` | Saves every query to store for history tracking |

### Architecture (Phase 3B)

```
START
  │
supervisor  (loads user preferences from store, saves query)
  │
[research_analysis, technical_analysis]  (parallel subgraphs)
  │                    │
(subgraph:            (subgraph:
 research →            technical)
 financial)            │
  │                    │
  └─────────┬──────────┘
            │
       aggregate  (sync point)
            │
   [comparison | reflection]  (conditional)
            │            │
        reflection    [loop]
            │
        writer  (interrupts for human approval)
            │
           END
```

### Subgraph State Mapping

| Subgraph | Shared Keys (auto-mapped) | Private Keys |
|----------|--------------------------|--------------|
| `research_analysis` | `company`, `ticker`, `research_findings`, `financial_metrics`, `sources` | None |
| `technical_analysis` | `company`, `ticker`, `technical_analysis` | None |

### Interrupt Flow (Writer Node)

1. Graph reaches `writer` node
2. `interrupt()` fires — pauses execution, saves state via checkpointer
3. Agent Chat UI displays approval prompt with company/ticker details
4. User approves or rejects
5. If approved → report generated. If rejected → early return with cancellation message.

### Store Namespace Design

| Namespace | Purpose | Access Pattern |
|-----------|---------|----------------|
| `("user", "preferences")` | User research preferences | Read at supervisor startup |
| `("user", "queries")` | Query history | Write on every query |

### Modified Files (Phase 3B)

| File | Changes |
|------|---------|
| `agents/supervisor.py` | Added `ResearchAnalysisState`, `TechnicalAnalysisState` subgraph state types |
| `agents/supervisor.py` | Added `build_research_analysis_subgraph()`, `build_technical_analysis_subgraph()` |
| `agents/supervisor.py` | Updated `build_graph()` to use subgraphs via `add_node()` |
| `agents/supervisor.py` | Added `interrupt()` to `writer_node` for human-in-the-loop approval |
| `agents/supervisor.py` | Added `RunnableConfig` parameter to `supervisor_node` for store access |
| `agents/supervisor.py` | Added `_load_user_preferences()`, `_save_query_to_store()` helper functions |
| `agents/supervisor.py` | Updated `route_after_supervisor()` to return subgraph node names |
| `tests/test_agents.py` | Updated `test_route_after_supervisor_returns_parallel_nodes` for new node names |

### Tests (Phase 3B)

```
24 passed in 49.54s

tests/test_agents.py      — 8 passed
tests/test_api.py         — 2 passed
tests/test_comparison.py  — 3 passed
tests/test_technical.py   — 6 passed
tests/test_tools.py       — 5 passed
```
