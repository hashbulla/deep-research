# State-of-the-Art Web Search Techniques for AI Agents
## Source Trustworthiness, Credibility Scoring & Deep Research Patterns

> **Target audience:** Staff AI/DevSecOps engineers building a Claude Code skill using Tavily, benchmarked against Perplexity Deep Research as gold standard.

---

## Executive Summary

The gap between "web search for chatbots" and "web search for academic-grade intelligence work" is a four-layer problem: **query architecture**, **source filtering**, **retrieval pipeline**, and **credibility scoring**. The state of the art in 2025–2026 combines iterative multi-pass query decomposition (as used by Perplexity Deep Research and Anthropic's internal research system) with domain-level allow-listing, relevance + authority reranking, and post-retrieval grading harnesses. This report maps every layer, catalogues the official Anthropic and Tavily mechanisms available to you, cross-references OSINT intelligence tradecraft, and proposes a composable architecture for your Claude Code skill.

---

## 1. The Gold Standard Explained: Perplexity Deep Research

Perplexity Deep Research is the current public benchmark for LLM-powered research quality. It completes in 2–4 minutes work that would take a human expert many hours, performing dozens of searches against hundreds of sources. Its internal process follows a strict five-stage **retrieval–reasoning–refinement** loop:

1. **Query Decomposition** — The original question is split into orthogonal sub-topics and dimensions (tokenised into atomic search intents).
2. **Parallel Retrieval** — Each sub-topic triggers a dedicated web or database search, using a tiered source preference (peer-reviewed > institutional > established press > general web).
3. **Structured Note Synthesis** — Partial answers are written into intermediate structured notes before final synthesis.
4. **Conflict Detection & Verification** — Conflicting claims are flagged and double-checked against independent sources before the synthesis step.
5. **Final Narrative with Reliability Notes** — A single grounded narrative is generated with inline citations and explicit uncertainty markers.

**Key differentiator from a naive agent loop:** Perplexity refines its *research plan* iteratively as it learns — it does not send all queries at once. Its source scoring strongly weights publisher authority, author credentials, institutional affiliation, peer-review status, and content freshness.

---

## 2. Anthropic's Official Techniques

### 2.1 Dynamic Filtering (`web_search_20260209`)

Anthropic's most recent tool version (February 2026) allows Claude to write Python code to **post-process and filter search results before they consume context window tokens**. This is the single highest-leverage quality mechanism currently available in the Claude API.

| Metric | Before | After Dynamic Filtering |
|--------|--------|------------------------|
| BrowseComp (Opus 4.6) | 45.3% | 61.6% (+16.3 pp) |
| DeepSearchQA F1 (Opus 4.6) | 69.8% | 77.3% (+7.5 pp) |
| Input token reduction | — | ~24% fewer tokens |
| Cost of code execution | — | **Free** when paired with web search |

**How to activate:**
- Use tool name `web_search_20260209`
- Include beta header: `code-execution-web-tools-2026-02-09`
- Enable the code execution tool in the same request

This allows Claude to write inline filters such as: score-threshold filtering, domain reputation checks, publication date filtering, and deduplication — all before results land in the prompt.

### 2.2 Domain Allow-Lists and Block-Lists

The Anthropic API web search tool exposes two parameters directly relevant to source quality:

- **`allowed_domains`**: An explicit allowlist — Claude **only** retrieves from these domains. Use this for academic-grade work (see Section 6 for a curated domain set).
- **`blocked_domains`**: Explicit denylist — useful for eliminating SEO farms, aggregator blogs, and low-trust commentary sites.

These can be configured at two levels:
- **Organization level** (Anthropic Console): Sets a baseline policy across all API calls in your account.
- **Request level**: Can only *further restrict* the org-level list, never expand it (security by default).

**Security caveat:** Unicode homograph attacks (e.g., `аrxiv.org` with a Cyrillic 'а') can bypass naive domain matching. Normalize and canonicalize all domain strings before comparison.

### 2.3 Anthropic's Internal Multi-Agent Research System

Anthropic published a case study on their own internal deep research agent. Several lessons are directly actionable:

- **Early agents consistently chose SEO-optimized content farms over academic PDFs**, even when authoritative sources were retrievable. The fix was explicit source quality heuristics in system prompts.
- **Orchestrator-worker pattern**: A lead orchestrator coordinates parallel subagents, each searching independently, then synthesizes. This prevents one low-quality source chain from contaminating the whole answer.
- **LLM-as-judge eval criteria** included a dedicated "source quality" dimension: *"Did the agent use primary sources over lower-quality secondary sources?"*
- **Start wide, then narrow**: Short, broad queries first to discover the landscape; progressively narrow follow-up queries to validate and deepen.

### 2.4 Skill Authoring Best Practices (Claude Code)

From the official Claude Code skill authoring docs:

- Describe **what sources constitute a good answer**, not just what information to retrieve. Give the agent a source preference hierarchy in the system prompt.
- Use **extended thinking** (if available) before the first tool call to decompose the query into a structured research plan.
- Use **interleaved thinking** after each retrieval tool result to evaluate source quality before proceeding.
- Apply context engineering: maintain lightweight URL/path identifiers in context, load full content on demand ("just in time") to avoid polluting the context window with low-quality content.

### 2.5 Agent Evaluation: Source Quality as a First-Class Metric

Anthropic's 2026 eval guide explicitly identifies three checks for research agents:

1. **Groundedness checks** — Every claim is supported by a retrieved source (no hallucination).
2. **Coverage checks** — Key facts a correct answer must include are present.
3. **Source quality checks** — Consulted sources are authoritative, not just the first retrieved. An LLM-as-judge grades whether the agent reached for primary sources.

For your Claude Code skill, source quality scoring should be an exit condition, not an afterthought.

---

## 3. Tavily API — Full Source Control Toolkit

### 3.1 Core Quality Parameters

| Parameter | Purpose | Recommended Value for Academic Work |
|-----------|---------|--------------------------------------|
| `search_depth` | `basic` / `advanced` / `ultra-fast` | `advanced` (reranked by relevance) |
| `include_domains` | Allowlist (up to 300 domains) | See Section 6 |
| `exclude_domains` | Denylist (up to 150 domains) | SEO farms, aggregators |
| `score` (metadata) | Relevance score 0–1 on each result | Filter `score > 0.7` |
| `auto_parameters` | Tavily auto-selects best params | `true` as default, override depth |
| `include_raw_content` | Return full page content | `true` for deep extraction |
| `max_results` | Number of results returned | 5–10 then rerank |

### 3.2 `advanced` vs `basic` Depth

`advanced` depth is fundamentally different from `basic`: results are returned as **semantic chunks** (not full pages), reranked by relevance to the query. This is the key setting for quality over speed. At roughly 2–5× the credit cost of `basic`, it is the correct default for a serious research skill.

### 3.3 Tavily Research API (vs Search Endpoint)

The **Research endpoint** (`/research`) is Tavily's answer to Perplexity Deep Research. It orchestrates a full multi-step loop autonomously:

```
Query → Search → Read → Identify gaps → Re-search → Synthesize
```

- Cost: 15–250 credits per call (vs 1 credit for `/search`)
- Returns a structured synthesis with citations, not just a list of results
- Tavily claims benchmark parity with or superiority to OpenAI and Perplexity on DeepResearch Bench

For your skill architecture, the Research endpoint handles the iteration loop internally. Use the Search endpoint when you need explicit control over the loop (for custom source grading).

### 3.4 Score-Based Post-Filtering Pattern

```
results = tavily.search(query, search_depth="advanced", max_results=10)
trusted = [r for r in results["results"] if r["score"] > 0.7
           and r["url"] not in blocked_urls
           and domain_tier(r["url"]) >= TIER_2]
```

Pair score filtering with a **domain tier function** (see Section 6) that classifies domains into tiers before any result enters the LLM context.

---

## 4. Intelligence & OSINT Tradecraft Applied to Source Grading

### 4.1 The NATO Admiralty Code (Source Grading System)

The intelligence community has used the **NATO Admiralty System** (also called the 2×6 grading matrix) since the Cold War. It evaluates on two independent axes:

**Source Reliability (A–F):**

| Grade | Meaning |
|-------|---------|
| A | Completely reliable (no doubt about authenticity/trustworthiness) |
| B | Usually reliable (minor doubts, mostly reliable history) |
| C | Fairly reliable (some doubts, significant reliable history) |
| D | Not usually reliable (significant doubt, occasional reliable output) |
| E | Unreliable (lacks authenticity, trustworthiness, competence) |
| F | Cannot be judged (insufficient basis to evaluate) |

**Information Credibility (1–6):**

| Grade | Meaning |
|-------|---------|
| 1 | Confirmed (independently confirmed by other sources) |
| 2 | Probably true (consistent with past intelligence) |
| 3 | Possibly true (reasonable but not confirmed) |
| 4 | Doubtful (not consistent with past intelligence) |
| 5 | Improbable (contradicted by other sources) |
| 6 | Cannot be judged (no basis for evaluation) |

**Actionability heuristic:** A1–B2 results are high-confidence actionable. F6 (most common in raw OSINT) requires corroboration before use. For an LLM research agent, map domain tiers to A–C reliability grades and cross-source confirmation to 1–3 credibility grades.

### 4.2 The CRAAP Test (Automated Source Evaluation)

The CRAAP test (originally academic, now widely adopted in OSINT) provides five automatable dimensions:

| Dimension | Signal | Automatable? |
|-----------|--------|-------------|
| **Currency** | Publication date, last updated timestamp | ✅ (metadata parse) |
| **Relevance** | Query-document semantic similarity | ✅ (embedding cosine / reranker score) |
| **Authority** | Author credentials, institutional domain, peer review | ✅ (domain tier + byline NER) |
| **Accuracy** | Evidence-backed, cross-checkable, no logical fallacies | ✅ (LLM-as-judge) |
| **Purpose** | No hidden agenda, not sensationalized | ⚠️ (LLM-as-judge, partial) |

For AI agents, Currency + Relevance + Authority can be fully automated in a pre-retrieval filter step. Accuracy and Purpose require an LLM grading pass post-retrieval.

### 4.3 Five-Step OSINT Validation Pipeline (for LLM Sources)

Adapted from intelligence analyst best practices for AI-tainted sources:

1. **Grade the source** — Assign an A–F reliability score based on domain tier, publication history, and editorial standards. Use a pre-built domain authority database.
2. **Validate against independent sources** — No single source should be the sole evidence for a claim. Require ≥2 independent corroborating sources for any factual assertion in the final synthesis.
3. **Interrogate model logic** — After retrieval, ask Claude to identify the primary source chain for each claim. If it cannot trace a claim to a URL, flag as unverified.
4. **Avoid the confidence trap** — LLM confidence scores and fluency do not correlate with accuracy. Treat all retrieved content as provisional until corroborated.
5. **Automate with curated domain lists** — Maintain a tiered domain registry (see Section 6). Integrate external media credibility databases (MBFC, NewsGuard, AllSides) for news sources.

---

## 5. Retrieval Pipeline Architecture: Two-Stage Retrieve + Rerank

The state-of-the-art pipeline for high-precision source selection follows a two-stage architecture:

```
┌─────────────────────────────────────────────────────────────────┐
│                    STAGE 1: BROAD RECALL                        │
│  Query Decomposer → Parallel Search (BM25 + semantic, 50-100   │
│  results) → Domain Tier Pre-filter → Score Threshold Filter     │
└──────────────────────────┬──────────────────────────────────────┘
                           │ ~20 candidates
┌──────────────────────────▼──────────────────────────────────────┐
│                    STAGE 2: PRECISION RERANK                    │
│  Cross-Encoder Reranker (query × document jointly scored) →     │
│  LLM-as-Judge Authority Check → Top 3–7 selected               │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Top 3–7 trusted results
┌──────────────────────────▼──────────────────────────────────────┐
│                    STAGE 3: SYNTHESIS                           │
│  LLM synthesis with grounding check + source quality eval →    │
│  Corrective loop if grounding fails (CRAG pattern)              │
└─────────────────────────────────────────────────────────────────┘
```

### 5.1 Query Decomposition Patterns

| Pattern | Description | Best For |
|---------|-------------|----------|
| **LevelRAG** | High-level decomposer → atomic sub-queries → low-level retrievers | Complex multi-faceted research |
| **ReDI** | Decompose → Interpret each sub-query → Fuse results | Ambiguous queries |
| **PRISM** | Question Analyzer + Selector Agent + Adder Agent (iterative loop) | Multi-hop fact-finding |
| **CoT Decomposition** | Chain-of-thought prompt to list sub-questions | General research tasks |

### 5.2 Cross-Encoder vs Bi-Encoder Reranking

| Method | How It Works | Accuracy | Speed | Cost |
|--------|-------------|----------|-------|------|
| **Bi-encoder** | Separate embeddings for query + doc | ⭐⭐⭐ | ⚡ Fast | Low |
| **Cross-encoder** | Joint encoding of query+doc pair | ⭐⭐⭐⭐⭐ | 🐢 Slow | High |
| **LLM reranker (pointwise)** | LLM scores each doc independently | ⭐⭐⭐⭐ | 🐢 Very slow | Very High |
| **LLM reranker (listwise)** | LLM ranks full candidate list at once | ⭐⭐⭐⭐⭐ | 🐢 Very slow | Very High |

**Recommendation for your skill:** Use a **cross-encoder** (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2` via HuggingFace or Cohere Rerank API) as Stage 2. Its joint query-document scoring catches relevance nuances that bi-encoders miss. Reserve LLM reranking for the final source quality judgement only (small candidate set, ≤10 docs).

### 5.3 Corrective RAG (CRAG) Loop

After initial synthesis, a CRAG loop grades each claim for grounding:

```
Generate → Grade claims → If groundedness < threshold:
  → Rewrite query (web search supplement)
  → Re-retrieve
  → Re-synthesize
```

This prevents hallucinations from propagating when the initial retrieval set has coverage gaps.

---

## 6. Curated Domain Tier Registry

A domain tier registry is the backbone of any source-quality-aware research agent. Assign domains to tiers before any source enters the LLM context.

### Tier 1 — Primary / Peer-Reviewed / Government
Highest trust. Use `include_domains` for pure academic work.

```
# Academic preprint & journals
arxiv.org, biorxiv.org, medrxiv.org, ssrn.com, semanticscholar.org
pubmed.ncbi.nlm.nih.gov, pmc.ncbi.nlm.nih.gov
nature.com, science.org, cell.com, thelancet.com
ieee.org, acm.org, springer.com, wiley.com, oup.com, sagepub.com
aclanthology.org, neurips.cc, icml.cc, iclr.cc

# Government & intergovernmental
*.gov, *.mil, *.gc.ca, *.gouv.fr, *.europa.eu
who.int, un.org, worldbank.org, imf.org, oecd.org, nato.int

# Statistics & official data
census.gov, bls.gov, eurostat.ec.europa.eu, data.gov
```

### Tier 2 — Institutional / Industry Research / Established Press
High trust for current affairs and technical topics.

```
# AI/tech primary research labs
anthropic.com, openai.com, deepmind.google, research.google
ai.meta.com, microsoft.com/en-us/research, labs.perplexity.ai

# Established tech documentation
docs.python.org, docs.rust-lang.org, kubernetes.io, cncf.io
github.com (official org repos only), stackoverflow.com (accepted answers)

# Established press (international)
reuters.com, apnews.com, bbc.co.uk, ft.com, economist.com
nytimes.com, washingtonpost.com, theguardian.com, lemonde.fr

# Industry analysis
gartner.com, mckinsey.com, hbr.org, mitsloan.mit.edu
```

### Tier 3 — Trade Press / Technical Blogs with Editorial Standards
Acceptable with corroboration.

```
techcrunch.com, wired.com, arstechnica.com, theregister.com
towardsdatascience.com (peer-reviewed), thenewstack.io
substack.com (institution-affiliated authors only)
```

### Tier 4 — General Web / Social / Forums
Require corroboration from Tier 1–2 before use. Never cite as primary.

```
reddit.com, twitter.com, linkedin.com, medium.com
# Only valid as social signal evidence, not factual claims
```

### Automatic Blocklist (SEO Spam / Content Farms)
```
# Add dynamically based on score < 0.3 from Tavily
# Supplement with: NewsGuard ratings, MBFC fact-check database
```

---

## 7. Specialized Search APIs for Academic & Trustworthy Sources

| API | Index Type | Academic Specialization | Source Control | Best For |
|-----|-----------|------------------------|----------------|----------|
| **Tavily** | Proprietary + web | `include_domains` + score filter | Domain allow/block lists, 300 domains | General research with domain control |
| **Exa AI** | Neural (link-prediction) | `findSimilar` from trusted seed URL | Category & domain filters | Semantic similarity from anchor paper |
| **Valyu** | Academic databases | arXiv, PubMed, bioRxiv, medRxiv | `included_sources` per database | Pure academic search |
| **Perplexity Sonar** | Proprietary LLM search | Source citation built-in | Limited | Fast quality answers, not raw sources |
| **Linkup** | Agent-optimized | Source-aware retrieval | Domain filtering | Agent-native structured retrieval |
| **Firecrawl** | Web + crawl | Full-page markdown extraction | URL-level control | Deep extraction after source selection |

### Exa AI — `findSimilar` Pattern for Academic Research

Exa's `findSimilar` endpoint is highly effective for building a trusted source graph: given one known-good URL (e.g., a specific arXiv paper), it finds semantically similar pages from its neural index. This is the equivalent of citation chaining in academic research — start from one authoritative anchor and expand.

```
Step 1: findSimilar(anchor_url="https://arxiv.org/abs/2502.18139",
                    num_results=10, type="research_paper")
Step 2: Grade results with domain tier check
Step 3: Use trusted URLs as new anchors for next iteration
```

Exa's neural index is trained on link prediction (how researchers actually cite each other), which produces fundamentally different — and often higher quality — results than keyword-based search for technical topics.

---

## 8. Prompt Engineering for Source Quality

System prompt heuristics that Anthropic's internal research system found effective:

### 8.1 Source Preference Hierarchy Prompt

```markdown
## Source Quality Requirements

You are a research assistant performing intelligence-grade information gathering.
Apply the following source preference hierarchy strictly:

TIER 1 (Preferred): Peer-reviewed papers (arXiv, PubMed, ACL Anthology),
  official government publications (*.gov, *.eu), primary technical documentation.

TIER 2 (Acceptable): Official company engineering blogs (anthropic.com/engineering,
  openai.com/research), established press (Reuters, AP, FT), official SDK docs.

TIER 3 (Require corroboration): Trade press, technical blogs, third-party tutorials.
  Never use as sole evidence for a claim.

TIER 4 (Do not use as sources): Reddit, LinkedIn posts, Medium articles, social media.
  Only use as social signal pointers to Tier 1–2 sources.

Before finalizing any claim, verify it is supported by at least one Tier 1 or Tier 2
source. If you cannot find a Tier 1/2 source, explicitly flag the claim as unverified.
```

### 8.2 Query Decomposition Prompt Pattern

```markdown
Before issuing any search queries, decompose the research question into:
1. Core factual sub-questions (what, when, who)
2. Contextual sub-questions (why, how, what are the implications)
3. Contradictory/alternative perspectives sub-questions
4. Recency sub-questions (what has changed in the last 12 months)

Issue parallel searches for each category. Synthesize only after all categories
have ≥2 independent Tier 1–2 sources.
```

### 8.3 Source Credibility Check Prompt (Post-Retrieval)

```markdown
For each source in your retrieved results, evaluate:
- Is the author or publisher identified and credible?
- Is the content dated and is the date relevant to the claim?
- Is this a primary source (original research/data) or secondary (summary/commentary)?
- Can the core claim be independently verified from another source?

Discard results that fail two or more criteria. Do not synthesize claims that rest
on a single unverifiable source.
```

---

## 9. Recommended Skill Architecture for Claude Code

### Architecture Overview

```
┌───────────────────────────────────────────────────────────────────┐
│ USER QUERY                                                        │
└──────────────────────────┬────────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 0: QUERY ARCHITECT (Extended Thinking)                     │
│  - Decompose into sub-questions (CoT)                            │
│  - Classify: academic / technical / current affairs / mixed      │
│  - Select domain tier profile for this query type                │
└──────────────────────────┬───────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 1: BROAD RETRIEVAL (Parallel)                              │
│  - Tavily `advanced` depth + `include_domains` (Tier 1+2)        │
│  - Exa `findSimilar` from any anchor academic URL identified     │
│  - Valyu for pure academic sub-questions                         │
│  - Score filter: keep only score > 0.7                           │
│  - Domain tier gate: reject Tier 4, flag Tier 3                  │
└──────────────────────────┬───────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 2: SOURCE GRADING (Dynamic Filtering Code Execution)       │
│  - Admiralty A–F source reliability score per domain             │
│  - CRAAP Currency + Authority automated check                    │
│  - Deduplicate by canonical URL                                  │
│  - Select top 10 candidates for reranking                        │
└──────────────────────────┬───────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 3: CROSS-ENCODER RERANK                                    │
│  - Cohere Rerank API or local cross-encoder                      │
│  - Final top 5–7 sources selected                                │
└──────────────────────────┬───────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 4: SYNTHESIS + GROUNDING VALIDATION                        │
│  - LLM synthesizes with inline citations                         │
│  - LLM-as-judge: groundedness + coverage + source quality check  │
│  - CRAG loop: if groundedness < threshold → re-query             │
└──────────────────────────┬───────────────────────────────────────┘
                           ▼
┌──────────────────────────────────────────────────────────────────┐
│ PHASE 5: CONFIDENCE ANNOTATION                                   │
│  - Each claim tagged: [CONFIRMED / PROBABLY TRUE / UNVERIFIED]  │
│  - Based on Admiralty credibility score (1–6) of supporting src  │
│  - Unverified claims isolated in a separate "Needs Verification" │
│    section of the output                                         │
└──────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Primary search | Tavily `advanced` + `include_domains` | Best domain control for quality |
| Academic fallback | Valyu / Exa `findSimilar` | Reach papers not indexed by Tavily |
| Source pre-filter | Dynamic Filtering (code execution) | ~24% token reduction, free with web search |
| Reranker | Cohere Rerank v3 or `ms-marco-MiniLM` | Cross-encoder accuracy without LLM cost |
| Synthesis grading | LLM-as-judge (Claude) | Matches Anthropic's internal eval criteria |
| Confidence output | Admiralty 1–6 per claim | Intelligence-grade provenance, usable by humans |

---

## 10. Evaluation Harness: Benchmarking Against Perplexity Deep Research

To validate your skill against the Perplexity gold standard, implement a three-dimension eval:

| Dimension | Metric | Method |
|-----------|--------|--------|
| **Groundedness** | % claims supported by a retrieved URL | LLM-as-judge: flag unsupported claims |
| **Source Quality** | % Tier 1/2 sources in final answer | Domain tier classification of all cited URLs |
| **Coverage** | Key fact recall vs gold answer | LLM-as-judge with reference answer |
| **Freshness** | Median publication date of sources | Metadata parse of retrieved URLs |
| **Corroboration Rate** | % claims with ≥2 independent sources | Citation graph analysis |

Run this harness on a fixed test set (e.g., 20–30 complex multi-hop research questions across domains) comparing your skill output vs Perplexity Deep Research output. Source quality and corroboration rate are the most discriminating metrics — they directly reflect the trustworthiness gap between agents.

---

## 11. Known Gaps and Open Problems

- **Paywalled academic content**: Tavily and Exa surface abstracts, not full papers, for major journals. Valyu partially solves this for PubMed/arXiv but not commercial journals (Elsevier, Springer). Open access repositories (PubMed Central, Unpaywall API) help but are incomplete.
- **Temporal bias in domain trust**: A domain rated A-reliable historically may publish lower-quality content on specific topics. Domain-level trust should be supplemented by article-level author credential checks when possible.
- **LLM-as-judge circularity**: Using Claude to grade Claude-generated synthesis introduces bias. For production systems, use a separate model (e.g., GPT-4 or Gemini) as the external judge.
- **Dynamic website content**: Many authoritative government and institutional sites render content client-side. Tavily and Firecrawl handle JS rendering; basic HTTP fetchers will silently fail, returning empty pages.
- **Unicode homograph domain spoofing**: Domain allowlists can be defeated by visually identical Unicode characters. Normalize all domain strings to ASCII (punycode) before comparison.

---

*Report generated: April 2026. Sources: Anthropic engineering blog, Tavily official documentation, Perplexity official blog, NATO Admiralty intelligence tradecraft, arXiv research papers on agentic RAG and retrieval systems.*
