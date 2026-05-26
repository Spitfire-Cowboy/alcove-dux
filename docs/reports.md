# Reports

Alcove Dux reports are evidence artifacts. They help a reviewer inspect similarity without assigning a misconduct decision.

## Report Types

### JSON

`.alcove-dux` files contain structured evidence:

- scan ID and generation timestamp
- suspicious and source document IDs
- document hashes when available
- runtime configuration
- selected model and dataset IDs
- match kind, score, offsets, chunk IDs, and explanation

The public schema lives at [`schemas/alcove-dux-report.schema.json`](../schemas/alcove-dux-report.schema.json).

Minimal example:

> **Note**: This example is illustrative and intentionally omits required
> fields. A complete payload also includes top-level fields such as
> `schema_version`, `generated_at`, and `source_documents`, plus per-match
> fields such as `suspicious_start`, `suspicious_end`, `source_start`,
> `source_end`, chunk IDs, and `explanation`. See
> [`schemas/alcove-dux-report.schema.json`](../schemas/alcove-dux-report.schema.json)
> for the full required structure.

```json
{
  "scan_id": "scan-123",
  "suspicious_document_id": "submitted",
  "source_document_id": "source-a",
  "matches": [
    {
      "kind": "exact_overlap",
      "score": 0.93
    }
  ]
}
```

### Public HTML

The `--html` export is meant for sharing a summary. It avoids raw private matched text and focuses on hashes, IDs, offsets, scores, and evidence metadata.

### Local Review HTML

The `--review-html` export is meant for local review. It includes matched text snippets and highlighted spans.

See the public-safe examples in [`examples/reports/example-scan.html`](../examples/reports/example-scan.html) and [`examples/reports/example-review.html`](../examples/reports/example-review.html).

## Evidence Labels

Reports use evidence-first wording:

- `exact_token_sequence`
- `exact_overlap`
- `near_duplicate`
- `possible_paraphrase`
- `needs_review`

Report output is review evidence, not a standalone decision. Human policy and context still matter.

## Privacy Rules

- Keep generated reports under `reports/`.
- Keep local reports out of public commits except public-safe examples under `examples/reports/`.
- Prefer document IDs without private paths, student identifiers, credentials, or device names.
- Prefer the public HTML export when raw text is not meant to be shared.
- Prefer local review HTML in trusted review contexts.
