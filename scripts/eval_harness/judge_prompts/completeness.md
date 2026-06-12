# Layer-4 judge prompt — completeness & citation-recall (versioned: v1, 2026-06-12)

> Receives the approved research-plan.md sub-question list, the report's section headings + claims, and the sources list. Never the scratch context.

You audit coverage, not correctness. Answer two questions:

1. **Sub-question coverage:** for each sub-question in the plan, is it answered in the report with at least one supported claim, explicitly marked unanswered in the Methodology note, or silently dropped?
2. **Citation recall:** are there sources in research-sources.json that materially bear on a sub-question but are cited nowhere? (Material = a Tier 1/2 source retrieved for that sub-question.)

Output exactly one JSON object:
{"subquestions": [{"id": "<sq id>", "status": "answered" | "documented_gap" | "silently_dropped"}], "uncited_material_sources": ["<source id>", ...], "citation_recall": <cited material sources / total material sources, 4 decimals>}
