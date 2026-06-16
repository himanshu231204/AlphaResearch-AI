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
        A1["aggregate"] -->|"query_type == comparison"| CMP["comparison"]
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
        C["company: str"]
        T["ticker: str"]
        QT["query_type: str"]
        RF["research_findings: str"]
        FM["financial_metrics: dict"]
        TA["technical_analysis: dict"]
        CR["comparison_results: dict"]
        VR["valuation_results: dict"]
        RR["risk_results: dict"]
        S["sources: list[str]"]
        FR["final_report: str"]
        RFB["reflection_feedback: str"]
        CC["cycle_count: int"]
        TC["target_companies: list[dict]"]
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
    R -->|"Attempt 2<br/>(after 2s)"| A
    R -->|"Attempt 3<br/>(after 4s)"| A
    R -->|"All failed"| ERR["Error message<br/>in state"]
```

| Parameter | Value |
|:--|:--|
| `max_attempts` | 3 |
| `initial_interval` | 1.0s |
| `backoff_factor` | 2.0 |
| `retry_on` | `Exception` (all) |

### Graceful Degradation

When an agent fails after all retries:

1. **Research agent** → Returns `"Research failed: <error>"` + empty sources
2. **Financial agent** → Returns `{"error": "<message>"}` in `financial_metrics`
3. **Technical agent** → Returns `{"error": "<message>"}` in `technical_analysis`
4. **Supervisor** → Falls back to default query parsing (no LLM)
5. **Reflection** → Uses basic completeness checks instead of LLM review
6. **Writer** → Returns `"Report generation failed: <error>"`

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
