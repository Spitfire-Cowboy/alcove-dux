# Alcove Plugin Plan

Alcove Dux integrates with Alcove as a local-first review plugin, not as a cloud service.

## Integration Goals

- Reuse Alcove's local corpus ingestion and search posture.
- Let users run Alcove Dux scans against an Alcove-managed corpus.
- Convert Alcove Dux JSON reports into searchable Alcove documents.
- Keep raw private document text local unless the user explicitly exports it.
- Preserve evidence-first language: `exact overlap`, `near duplicate`, `possible paraphrase`, `needs review`.

## Plugin Shape

Alcove Dux's core package remains independent:

- `alcove_dux.documents` for normalization, hashing, and chunking.
- `alcove_dux.matching` for exact/fuzzy evidence.
- `alcove_dux.semantic` and `alcove_dux.vector_store` for semantic retrieval.
- `alcove_dux.evaluation` for benchmark loaders and metric summaries.
- `alcove_dux.integrations.alcove` for Alcove-specific report extraction.

The integration path starts by making Alcove Dux reports searchable in Alcove. Additional milestones can add direct scan commands from Alcove collections.

## Boundaries

- Offline by default.
- No outbound corpus uploads.
- No private paths or device names in exported reports.
- No accusation labels.
- Store document hashes and local IDs by default; make source text export explicit.

## Proposed User Flow

1. User indexes a local corpus in Alcove.
2. User submits a document to Alcove Dux.
3. Alcove Dux scans against selected Alcove collection chunks.
4. Alcove Dux writes a `.alcove-dux` JSON report.
5. Alcove indexes the report summary so it can be searched later.

## Entry Point

Alcove Dux exposes a `.alcove-dux` report extractor through Alcove's plugin entry point group:

```toml
[project.entry-points."alcove.extractors"]
alcove_dux = "alcove_dux.integrations.alcove:extract_alcove_dux_report"
```

The `.alcove-dux` extension avoids overriding Alcove's built-in JSON extractor while still allowing Alcove Dux reports to use JSON internally.
