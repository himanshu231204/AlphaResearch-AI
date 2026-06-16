# AGENTS.md

# Autonomous Market Research AI agent

Version: 1.0

---

# PROJECT VISION

Build a production-grade AI Market Research agent capable of performing institutional-quality equity research using autonomous AI agents.

The platform should function as:

* Perplexity for Stocks
* AI Equity Research Analyst
* AI Financial Copilot
* Autonomous Market Intelligence Platform

The system must autonomously:

* Research companies
* Analyze financial statements
* Analyze technical indicators
* Analyze earnings reports
* Analyze annual reports
* Analyze investor presentations
* Analyze earnings call transcripts
* Compare competitors
* Identify risks
* Calculate valuation
* Generate investment theses
* Generate professional research reports

The final output should be comparable to professional equity research reports.

---

# CORE PHILOSOPHY

The system must be:

* Source Grounded
* Agent Driven
* Research First
* Reflection Based
* Production Ready
* Explainable
* Auditable
* Extensible

Every major conclusion must have supporting evidence.

Never fabricate financial data.

Never fabricate sources.

---

# DOCUMENTATION-FIRST DEVELOPMENT POLICY

This project follows a Documentation-First Engineering approach.

The coding agent MUST use the provided official documentation MCP servers before implementing any feature.

Never rely on:

* Memory
* Assumptions
* Old blog posts
* Outdated examples
* Deprecated APIs

Always verify implementation details through official documentation.

---

# SOURCE OF TRUTH

Primary source of truth:

1. Official LangGraph Documentation MCP
2. Official LangChain Documentation MCP
3. Official DeepAgents Documentation MCP
4. Official LiteLLM Documentation MCP
5. Official Chroma Documentation MCP
6. Official Firecrawl Documentation MCP

If AGENTS.md conflicts with official documentation:

Follow official documentation.

Then update implementation accordingly.

---

# TECHNOLOGY STACK

## Agent Framework

* LangGraph
* DeepAgents
* LangChain

## Model Routing

* LiteLLM

## Models

Primary Reasoning:

* Gemini 2.5 Pro

Fast Research:

* Grok

Fast Summaries:

* Gemini Flash

## Search Layer

Using LangChain MCP Adapter:

* Google Search MCP
* Brave Search MCP
* Firecrawl MCP

## Financial Data

* Yahoo Finance
* Finnhub
* Alpha Vantage

## Vector Database

* ChromaDB

## Embeddings

Primary:

* BAAI/bge-large-en-v1.5

Alternative:

* nomic-embed-text

## Backend

* FastAPI

## Frontend

* Next.js

## Observability

* LangSmith

---

# HIGH LEVEL ARCHITECTURE

User
↓
LangGraph Supervisor
↓
Deep Research Agent Layer
↓
Research Agents
↓
Reflection Layer
↓
Investment Thesis Generator
↓
Research Report Generator

---

# AGENT ARCHITECTURE

The system follows a Supervisor Pattern.

Only the Supervisor communicates with users.

All other agents act as specialist workers.

---

# SUPERVISOR AGENT

Responsibilities:

* Understand user intent
* Create research plans
* Delegate tasks
* Track execution
* Coordinate reflection cycles
* Aggregate findings
* Generate final response

Example:

User Query:

Analyze Reliance Industries and compare with TCS.

Supervisor creates:

* Company Research Task
* Financial Analysis Task
* Technical Analysis Task
* News Analysis Task
* Valuation Task
* Risk Analysis Task

---

# RESEARCH AGENT

Responsibilities:

* Company research
* Sector research
* Competitor research
* Macro-economic research
* News collection

Tools:

* Google Search MCP
* Brave Search MCP
* Firecrawl MCP

Outputs:

* Research findings
* Sources
* Citations

---

# FINANCIAL ANALYSIS AGENT

Responsibilities:

Analyze:

* Revenue Growth
* Net Income
* EPS
* PE Ratio
* PB Ratio
* ROE
* ROCE
* Debt to Equity
* Cash Flow
* Profit Margins

Output:

Structured financial analysis.

---

# TECHNICAL ANALYSIS AGENT

Responsibilities:

Calculate:

* RSI
* MACD
* EMA
* SMA
* Bollinger Bands
* Support Levels
* Resistance Levels
* Trend Direction

Libraries:

* pandas
* numpy
* ta

Output:

Technical trading summary.

---

# ANNUAL REPORT AGENT

Responsibilities:

Analyze:

* Annual Reports
* Investor Presentations
* Earnings Reports
* Earnings Call Transcripts

Identify:

* Growth Drivers
* Risks
* Management Guidance
* Expansion Plans
* CapEx Plans
* Future Outlook

Uses RAG.

---

# VALUATION AGENT

Responsibilities:

Perform:

* Discounted Cash Flow
* Relative Valuation
* Industry Comparison
* PE Comparison
* PB Comparison

Generate:

* Intrinsic Value
* Margin of Safety
* Valuation Score

---

# RISK ANALYSIS AGENT

Responsibilities:

Identify:

* Business Risks
* Financial Risks
* Industry Risks
* Regulatory Risks
* Competitive Risks
* Management Risks

Generate:

Risk Score

Scale:

1 to 10

---

# REFLECTION AGENT

Responsibilities:

Review all findings.

Check:

* Missing evidence
* Missing sources
* Weak conclusions
* Contradictions
* Incomplete research

If issues exist:

Return control to Supervisor.

Maximum reflection cycles:

3

The system must never enter infinite loops.

---

# WRITER AGENT

Responsibilities:

Generate:

* Executive Summary
* Investment Thesis
* Financial Summary
* Valuation Summary
* Risk Assessment
* Buy/Hold/Sell Recommendation

Output:

Professional research report.

---

# DEEP AGENT STRATEGY

DeepAgents are autonomous researchers.

Use DeepAgents for:

* Planning
* Investigation
* Research
* Information gathering
* Multi-step reasoning

Do not manually recreate DeepAgent functionality.

Leverage official DeepAgents capabilities whenever possible.

---

# MCP-FIRST PRINCIPLE

If an official MCP integration exists:

Prefer MCP.

Avoid:

* Custom search clients
* Manual scraping
* Direct HTTP implementations

Preferred order:

1. Google Search MCP
2. Brave Search MCP
3. Firecrawl MCP

Create wrappers around MCP clients.

Never call MCP servers directly from business logic.

---

# LANGGRAPH-FIRST PRINCIPLE

Workflow orchestration must use LangGraph.

Prefer:

* StateGraph
* Conditional Edges
* Checkpointers
* Interrupts
* Streaming

Avoid custom orchestration frameworks.

---

# RAG ARCHITECTURE

Supported Documents:

* Annual Reports
* Earnings Reports
* Earnings Call Transcripts
* Investor Presentations
* SEC Filings
* NSE Filings
* BSE Filings

Pipeline:

Document
↓
Loader
↓
Chunking
↓
Embedding
↓
ChromaDB
↓
Retriever
↓
LLM Analysis

---

# MEMORY ARCHITECTURE

## Short-Term Memory

Stored in LangGraph state.

Used during active execution.

---

## Long-Term Memory

Stored in ChromaDB.

Contains:

* Previous reports
* Research findings
* Historical analyses
* User preferences

---

# LANGGRAPH STATE

Core state should include:

user_query

company

research_findings

news_findings

financial_metrics

technical_metrics

valuation_results

risk_results

reflection_feedback

sources

final_report

---

# MODEL ROUTING POLICY

All model access must go through LiteLLM.

Never instantiate providers directly inside agents.

Use centralized routing.

Routing:

Planning:
Gemini 2.5 Pro

Research:
Grok

Financial Analysis:
Gemini 2.5 Pro

Technical Analysis:
Grok

Reflection:
Gemini 2.5 Pro

Report Writing:
Gemini 2.5 Pro

Quick Summaries:
Gemini Flash

---

# FOLDER STRUCTURE

market-research-ai/

app/

agents/

graphs/

models/

mcp/

tools/

rag/

memory/

prompts/

reports/

tests/

docs/

---

# CODING STANDARDS

Required:

* Type hints
* Pydantic models
* Async support
* Structured logging
* Dependency injection

Avoid:

* Global variables
* Hardcoded prompts
* Direct model instantiation
* Duplicate business logic

---

# ERROR HANDLING

Every tool must:

* Retry
* Log failures
* Return structured errors

The system must remain operational even when external tools fail.

Implement graceful degradation.

---

# OBSERVABILITY

Track:

* Agent execution
* Tool usage
* Latency
* Token usage
* Failure rates
* Reflection cycles

Use LangSmith tracing.

---

# SECURITY

Never:

* Execute arbitrary code
* Expose secrets
* Trust scraped content blindly

Always:

* Validate external content
* Sanitize inputs
* Protect API keys

---

# DEVELOPMENT ROADMAP

Phase 1

* Single stock analysis
* Financial analysis
* News research
* Basic reports

Phase 2

* Technical analysis
* Reflection loops
* Company comparison

Phase 3

* Annual report RAG
* Earnings call analysis

Phase 4

* Portfolio analysis
* Sector analysis

Phase 5

* Autonomous daily research reports

Phase 6

* Institutional-grade market intelligence platform

---

# SUCCESS CRITERIA

The final system should produce research reports comparable to:

* Morningstar
* Seeking Alpha
* Perplexity Deep Research

while remaining:

* Source-backed
* Explainable
* Auditable
* Agent-driven
* Production-ready

---

# FINAL IMPLEMENTATION RULE

Before writing code:

1. Read official documentation MCP.
2. Create implementation plan.
3. Explain architecture.
4. Implement feature.
5. Add tests.
6. Validate against documentation.

Documentation is the source of truth.
