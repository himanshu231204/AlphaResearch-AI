# Architecture Documentation

AlphaResearch AI is a multi-agent system built on LangGraph that orchestrates specialized AI agents to perform autonomous equity research.

---

## High-Level Architecture

```mermaid
flowchart TD
    U["<b>User</b>"] -->|"Query"| API["<b>FastAPI Backend</b>"]
    API -->|"graph.invoke()"| LG["<b>LangGraph Server</b>"]
    LG --> SUP["<b>Supervisor Agent</b><br/>Gemini 2.5 Flash"]

    SUP --> RA["<b>Research Analysis</b><br/>Subgraph"]
    SUP --> TA["<b>Technical Analysis</b><br/>Subgraph"]

    RA --> R["Research Agent<br/>Groq Llama 3.3 70B"]
    R --> F["Financial Agent<br/>OpenRouter Nex N2 Pro"]
    TA --> T["Technical Agent<br/>Groq Llama 3.3 70B"]

    F --> AGG["<b>Aggregate</b>"]
    T --> AGG

    AGG --> CMP{"Query Type?"}
    CMP -->|"comparison"| COMP["Comparison Agent"]
    CMP -->|"single_stock"| REF["Reflection Loop"]
    COMP --> REF

    REF -->|"Issues found"| SUP
    REF -->|"Approved"| WR["Writer Agent<br/><i>HITL ✓</i>"]
    WR --> REP["<b>Research Report</b>"]

    style U fill:#1a1a2e,stroke:#e94560,color:#fff
    style SUP fill:#16213e,stroke:#0f3460,color:#fff
    style AGG fill:#1a1a2e,stroke:#e94560,color:#fff
    style REF fill:#533483,stroke:#e94560,color:#fff
    style WR fill:#16213e,stroke:#0f3460,color:#fff
    style REP fill:#0f3460,stroke:#e94560,color:#fff
```

---

## Agent Architecture

The system follows a **Supervisor Pattern** — only the supervisor communicates with users, all other agents are specialist workers.

### Agent Hierarchy

```mermaid
flowchart LR
    subgraph "Supervisor Layer"
        S["Supervisor Agent"]
    end

    subgraph "Research Branch"
        R["Research Agent"]
        F["Financial Agent"]
    end

    subgraph "Technical Branch"
        T["Technical Agent"]
    end

    subgraph "Comparison"
        C["Comparison Agent"]
    end

    subgraph "Output"
        W["Writer Agent"]
        RFL["Reflection Agent"]
    end

    S --> R
    S --> T
    R --> F
    S --> C
    S --> RFL
    RFL --> W

    style S fill:#16213e,stroke:#0f3460,color:#fff
    style R fill:#0d1b2a,stroke:#1b263b,color:#fff
    style F fill:#0d1b2a,stroke:#1b263b,color:#fff
    style T fill:#0d1b2a,stroke:#1b263b,color:#fff
    style C fill:#0d1b2a,stroke:#1b263b,color:#fff
    style W fill:#16213e,stroke:#0f3460,color:#fff
    style RFL fill:#533483,stroke:#e94560,color:#fff
```

### Agent Responsibilities

| Agent | Model | Role | Tools |
|:--|:--|:--|:--|
| **Supervisor** | Gemini 2.5 Flash | Query parsing, orchestration | None (LLM only) |
| **Research** | Groq Llama 3.3 70B | Web intelligence gathering | All search tools |
| **Financial** | OpenRouter Nex N2 Pro | Fundamental analysis | Yahoo Finance, Finnhub, Alpha Vantage |
| **Technical** | Groq Llama 3.3 70B | Technical indicators | RSI, MACD, Bollinger, support/resistance |
| **Comparison** | Gemini 2.5 Flash | Head-to-head analysis | All comparison tools |
| **Reflection** | Gemini 2.5 Flash | Quality review | None (LLM only) |
| **Writer** | Gemini 2.5 Flash | Report generation | None (LLM only) |

---

## LangGraph Graph Structure

### Node Definitions

```mermaid
flowchart TD
    subgraph "Main Graph: ResearchState"
        START((START))
        SUP["supervisor_node"]
        RA["research_analysis<br/><i>subgraph</i>"]
        TA["technical_analysis<br/><i>subgraph</i>"]
        AGG["aggregate_node"]
        CMP["comparison_node"]
        REF["reflection_node"]
        WR["writer_node"]
        END((END))

        START --> SUP
        SUP --> RA
        SUP --> TA
        RA --> AGG
        TA --> AGG
        AGG --> CMP
        AGG --> REF
        CMP --> REF
        REF --> WR
        REF -->|"loop"| SUP
        WR --> END
    end

    subgraph "Research Analysis Subgraph: ResearchAnalysisState"
        R_START((START))
        RES["research_node"]
        FIN["financial_node"]
        R_END((END))

        R_START --> RES
        RES --> FIN
        FIN --> R_END
    end

    subgraph "Technical Analysis Subgraph: TechnicalAnalysisState"
        T_START((START))
        TECH["technical_node"]
        T_END((END))

        T_START --> TECH
        TECH --> T_END
    end
```

### Conditional Edges

```mermaid
flowchart LR
    subgraph "route_after_supervisor"
        S1["supervisor"] -->|"Returns list"| PAR["research_analysis +<br/>technical_analysis"]
    end

    subgraph "route_after_aggregation"
        A1["aggregate"] -->|"missing data"| END["__end__"]
        A1 -->|"query_type == comparison"| CMP["comparison"]
        A1 -->|"query_type == single_stock"| REF["reflection"]
    end

    subgraph "route_after_reflection"
        R1["reflection"] -->|"feedback == RESEARCH_COMPLETE"| WR["writer"]
        R1 -->|"feedback != RESEARCH_COMPLETE"| SUP["supervisor"]
    end
```

---

## State Schema

### ResearchState (Main Graph)

```mermaid
flowchart LR
    subgraph "ResearchState"
        direction TB
        M["messages: Annotated[list, add_messages]"]
        UQ["user_query: str"]
        C["company: Annotated[str, str_replace]"]
        T["ticker: Annotated[str, str_replace]"]
        QT["query_type: Annotated[str, str_replace]"]
        RF["research_findings: Annotated[str, str_replace]"]
        FM["financial_metrics: Annotated[dict, dict_merge]"]
        TA["technical_analysis: Annotated[dict, dict_merge]"]
        CR["comparison_results: Annotated[dict, dict_merge]"]
        VR["valuation_results: Annotated[dict, dict_merge]"]
        RR["risk_results: Annotated[dict, dict_merge]"]
        S["sources: Annotated[list[str], operator.add]"]
        FR["final_report: Annotated[str, str_replace]"]
        RFB["reflection_feedback: Annotated[str, str_replace]"]
        CC["cycle_count: Annotated[int, str_replace]"]
        TC["target_companies: Annotated[list[dict], str_replace]"]
    end
```

### Subgraph State Mapping

| Subgraph | Shared Keys (auto-mapped) | Private Keys |
|:--|:--|:--|
| `research_analysis` | `company`, `ticker`, `research_findings`, `financial_metrics`, `sources` | None |
| `technical_analysis` | `company`, `ticker`, `technical_analysis` | None |

When a subgraph is added via `add_node()`, LangGraph automatically maps shared keys between the subgraph state and the parent graph state.

---

## Data Flow

```mermaid
flowchart TD
    Q["User Query"] --> SUP["Supervisor<br/>Parse query → company, ticker, query_type"]
    
    SUP --> RA["Research Analysis Subgraph"]
    SUP --> TA["Technical Analysis Subgraph"]

    RA --> R["Research Agent<br/>Web search → research_findings, sources"]
    R --> F["Financial Agent<br/>yfinance/finnhub → financial_metrics"]
    
    TA --> T["Technical Agent<br/>RSI/MACD/Bollinger → technical_analysis"]

    F --> AGG["Aggregate<br/>Sync point — both branches complete"]
    T --> AGG

    AGG --> CMP{"Comparison?"}
    CMP -->|"Yes"| COMP["Comparison Agent<br/>compare_financials, compare_technicals"]
    CMP -->|"No"| REF["Reflection"]

    COMP --> REF["Reflection<br/>Quality review → RESEARCH_COMPLETE or issues"]
    REF -->|"Issues"| SUP
    REF -->|"Complete"| WR["Writer<br/>Generate Markdown report"]
    WR --> END["Report"]
```

---

## Fault Tolerance

### Retry Policy

All agent nodes use `RetryPolicy` from LangGraph:

```mermaid
flowchart LR
    A["Agent Node"] -->|"Exception"| R["RetryPolicy"]
    R -->|"Attempt 1"| A
    R -->|"Attempt 2<br/>(after 1s)"| A
    R -->|"Attempt 3<br/>(after 2s)"| A
    R -->|"All failed"| ERR["Error message<br/>in state"]
```

| Parameter | Value |
|:--|:--|
| `max_attempts` | 3 |
| `initial_interval` | 1.0s |
| `backoff_factor` | 2.0 |
| `retry_on` | `Exception` (all) |

### Timeout Policy

All agent nodes use `TimeoutPolicy` from LangGraph:

| Parameter | Value | Purpose |
|:--|:--|:--|
| `run_timeout` | 600s (10 min) | Hard wall-clock limit per attempt |
| `idle_timeout` | 120s (2 min) | Reset on progress; fire if stuck |

### CancelledError Handling

In Python 3.11+, `asyncio.CancelledError` derives from `BaseException`, not `Exception`. This means:
- The retry policy's default `retry_on` does **not** catch it
- `except Exception` blocks do **not** catch it

The system handles this at three levels:

1. **Agent nodes** — explicitly re-raise `CancelledError` so LangGraph's runner handles it
2. **API endpoints** — catch `CancelledError` and return HTTP 499 (client closed request)
3. **Lifespan handler** — 5-second drain window on shutdown to let in-flight requests finish

### Aggregate Fail-Fast

The aggregate node verifies data completeness before routing forward. If any critical branch failed (research findings missing, financial or technical analysis contains errors), it writes a clear error report and routes directly to `__end__`, skipping the reflection and writer nodes entirely.

### Graceful Degradation

When an agent fails after all retries:

1. **Research agent** → Returns `"Research failed: <error>"` + empty sources
2. **Financial agent** → Returns `{"error": "<message>"}` in `financial_metrics`
3. **Technical agent** → Returns `{"error": "<message>"}` in `technical_analysis`
4. **Supervisor** → Falls back to default query parsing (no LLM)
5. **Reflection** → Uses basic completeness checks instead of LLM review
6. **Writer** → Returns `"Report generation failed: <error>"`
7. **Aggregate node** → If any branch failed, writes error report and routes to `__end__`, skipping reflection and writer entirely

---

## Persistence & Memory

### Per-Thread Checkpointing (MemorySaver)

```mermaid
flowchart LR
    T1["Thread 1<br/>Analyze AAPL"] --> CP1["Checkpoint 1"]
    T2["Thread 2<br/>Compare MSFT/GOOG"] --> CP2["Checkpoint 2"]
    
    CP1 -->|"Resume"| T1R["Continue AAPL"]
    CP2 -->|"Resume"| T2R["Continue MSFT/GOOG"]
```

Each research session gets a unique `thread_id`. `MemorySaver` checkpoints state at every superstep, enabling:

- Session resume after interruptions
- Human-in-the-loop approval flow
- Debug state at any point

### Cross-Thread Memory (InMemoryStore)

```mermaid
flowchart LR
    subgraph "InMemoryStore"
        UP["namespace: user/preferences<br/>User research preferences"]
        UQ["namespace: user/queries<br/>Query history"]
    end

    Q1["Query 1"] --> UQ
    Q2["Query 2"] --> UQ
    SUP["Supervisor"] -->|"Read"| UP
```

| Namespace | Purpose | Access |
|:--|:--|:--|
| `("user", "preferences")` | User research preferences | Read at supervisor startup |
| `("user", "queries")` | Query history | Write on every query |

---

## Human-in-the-Loop

```mermaid
flowchart TD
    A["Writer Node Reached"] --> B["interrupt() fired"]
    B --> C["State saved via checkpointer"]
    C --> D["Agent Chat UI shows approval prompt"]
    D --> E{"User Decision"}
    E -->|"Approve"| F["Generate report"]
    E -->|"Reject"| G["Return cancellation"]
    F --> H["Report delivered"]
    G --> I["Session ended"]
```

The `interrupt()` function pauses graph execution and surfaces to the frontend. The user can approve or reject report generation.

---

## Technology Stack

| Layer | Technology | Purpose |
|:--|:--|:--|
| **Agent Framework** | LangGraph | Graph orchestration, state management |
| **Agent Library** | DeepAgents | Autonomous research agents |
| **Model Routing** | LiteLLM | Unified LLM access across providers |
| **Backend** | FastAPI | REST API |
| **Frontend** | Agent Chat UI | Real-time streaming interface |
| **Vector DB** | ChromaDB | RAG pipeline (Phase 4) |
| **Observability** | LangSmith | Tracing, monitoring |
