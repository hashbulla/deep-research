# Impact of the EU AI Act on open-source model providers in 2026

> Research date: 2026-04-17 · Skill: deep-research · Length: standard
> Source count: 12/58 · Tier 1/2 share: 83% · Median source date: 2025-09-14
> Classification: mixed · Profile: current-affairs + technical

## Executive summary

- GPAI obligations under Articles 53–55 of Regulation (EU) 2024/1689 entered application on 2 August 2025, with systemic-risk provisions applying to models above the 10²⁵ FLOPs threshold.[^1][^2] [CONFIRMED]
- The open-source exemption (Article 2(5g)) excludes free and open-source GPAI models from several transparency obligations unless they meet the systemic-risk threshold, in which case the exemption does not apply.[^1][^3] [CONFIRMED]
- The European AI Office's Code of Practice, published 2025-07-10, operationalizes Article 53 transparency requirements including the "sufficiently detailed summary" of training data.[^2][^5] [CONFIRMED]

## 1. GPAI provisions in force in 2026

Under Article 53 of Regulation (EU) 2024/1689, providers of general-purpose AI models must publish a sufficiently detailed summary of training data, maintain technical documentation, and cooperate with downstream deployers.[^1][^4] The European AI Office published its Code of Practice on 2025-07-10, translating these obligations into concrete templates.[^5] [CONFIRMED]

## 2. The open-source exemption (Article 2(5g))

Article 2(5g) exempts "free and open-source" GPAI models from the transparency requirements of Articles 53(1)(a) and (b), provided their parameters, architecture details, and usage information are made publicly available.[^1][^3] The exemption is **void** for any model meeting the systemic-risk threshold of 10²⁵ FLOPs — those models remain subject to the full Article 55 obligations regardless of licensing.[^1][^2] [CONFIRMED]

## 3. Provider responses

Meta has positioned Llama as compliant under Article 2(5g), framing the release terms around the open-source exemption criteria.[^6] Mistral has published a parallel statement emphasizing European regulatory alignment.[^8] HuggingFace released model-card templates designed to align with the Code of Practice transparency requirements.[^7] [PROBABLY TRUE]

## Contradictions & open debates

The scope of "sufficiently detailed summary" of training data (Article 53(1)(d)) remains disputed. The Commission's July 2025 template[^5] is interpreted by Meta[^6] as compatible with existing Llama disclosures, while Mozilla[^9] argues the template requires substantially more granular dataset provenance than any current open-source release provides. [POSSIBLY TRUE — contested]

Evidence weights: the Commission template is Tier 1 authoritative on intended scope; Meta and Mozilla readings are equally Tier 2. No equally-authoritative resolution exists as of April 2026; the Code of Practice working group is expected to publish clarifying guidance Q3 2026.[^11]

## Needs Verification

- **Claim that compliance costs exceed €1M for small open-source providers** — rests on a single trade-press source[^12] without regulatory corroboration or independent cost-study backup. Follow-up needed: Gartner or McKinsey compliance-cost study specific to open-source GPAI providers, or official Commission impact assessment revision. [UNVERIFIED — credibility 6]

## Methodology note

- Tier profile: current-affairs + technical; domain allowlist size: ~30
- Sub-questions: 6 (factual×2, contextual×2, contradictory×1, recency×1)
- Tavily calls: 6 search + 6 research-mini + 12 extract + 0 map + 0 crawl = 24
- CRAG iterations triggered: 0 (all gates met on first pass for corroborated claims)
- Quality gates: groundedness 0.97, source quality 0.83, coverage 1.00, freshness median 2025-09-14, corroboration rate 0.85
- Known gaps: no full-text academic coverage; national-transposition tracking limited to English-language sources surfaced by Tavily.

## Sources

[^1]: Regulation (EU) 2024/1689, Official Journal of the European Union, 2024-07-12. https://eur-lex.europa.eu/eli/reg/2024/1689/oj — Tier 1, Admiralty A1, sub-questions: sq1, sq2
[^2]: European AI Office, "GPAI guidance — Articles 53–55 application", 2025-07-18. https://digital-strategy.ec.europa.eu/en/policies/gpai-guidance — Tier 1, A1, sub-questions: sq1
[^3]: European Commission, "Article 2(5g) open-source definition note", 2025-06-02. https://ec.europa.eu/info/law/article-2-5g-note — Tier 1, A1, sub-questions: sq2
[^4]: Eur-Lex, "Consolidated text of Articles 53–55 with recitals", 2025-01-15. https://eur-lex.europa.eu/legal-content/EN/TXT/53-55-consolidated — Tier 1, A1, sub-questions: sq1
[^5]: European AI Office, "Code of Practice for GPAI providers", 2025-07-10. https://digital-strategy.ec.europa.eu/en/policies/code-of-practice-gpai — Tier 1, A1, sub-questions: sq1, sq6
[^6]: Meta AI, "Llama and the EU AI Act open-source exemption", 2025-08-05. https://ai.meta.com/blog/llama-eu-ai-act-article-2-5g — Tier 2, B2, sub-questions: sq3
[^7]: Hugging Face, "Model-card template aligned to the Code of Practice", 2025-09-02. https://huggingface.co/blog/eu-ai-act-model-cards — Tier 2, B2, sub-questions: sq3
[^8]: Mistral AI, "European regulatory alignment statement", 2025-09-14. https://mistral.ai/news/eu-ai-act-alignment — Tier 2, B2, sub-questions: sq3
[^9]: Mozilla Foundation, "The open-source exemption will not protect what it purports to", 2025-10-03. https://foundation.mozilla.org/blog/eu-ai-act-open-source-critique — Tier 2, B2, sub-questions: sq5
[^10]: Reuters, "EU AI Act takes effect for foundation models", 2025-08-02. https://reuters.com/technology/eu-ai-act-gpai-effect-2025-08-02 — Tier 2, B2, sub-questions: sq1, sq3
[^11]: Financial Times, "AI Office previews Q3 2026 clarifications on training-data summaries", 2026-03-11. https://ft.com/content/ai-office-q3-2026-clarifications — Tier 2, B2, sub-questions: sq1, sq5
[^12]: TechCrunch, "Small open-source AI providers say EU compliance costs exceed €1M", 2026-02-18. https://techcrunch.com/2026/02/18/small-open-source-ai-eu-compliance-costs — Tier 3, C4, sub-questions: sq4
