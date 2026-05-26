# Privacy Boundary

Alcove Dux is local-first. Private documents, extracted text, generated reports, vector indexes, and model caches stay on the user's device unless the user deliberately exports them.

For schools and universities, that means student work can stay under institutional control instead of being uploaded to a third-party similarity service.

## Student work and FERPA

Alcove Dux processes student submissions locally. During a scan, student work does not need to be transmitted to Anthropic, GitHub, or another third party.

For US institutions, this supports FERPA-aligned deployment because student records remain under institutional control rather than entering a vendor-managed comparison database.

## GDPR and local processing

For EU and UK institutions, local-first processing means student data does not need to cross jurisdictional boundaries or enter third-party infrastructure during routine scanning. The institution controls the data at rest and in transit.

## For IT administrators

- No external API calls are required during scans.
- No student data is intentionally sent to telemetry services during scans.
- Scan state is stored locally by the deployment.
- Report export is opt-in.
- Unlike cloud-based similarity services, Alcove Dux does not retain copies of submitted documents, does not build a comparison database from student submissions, and does not share data with external services by default.

## Recommended Public Report Contents

When a report needs to travel outside a trusted review context, keep it focused on stable evidence artifacts rather than raw source material.

- stable document IDs
- document hashes
- chunk IDs
- offsets
- scores
- match kinds
- model and dataset IDs
- reviewer-facing explanations

## Private Data To Omit

These details are the easiest way to accidentally leak context that a public report does not need.

- raw private document text
- private filesystem paths
- credentials or tokens
- device names
- private infrastructure names
- personally identifying information
- student, author, submission, or case labels that are not meant to be public

## Document IDs

Document IDs should help a reviewer stay oriented without revealing provenance that should remain private.

User-provided document IDs are handled as public labels. IDs that look like emails, paths, filenames, titles, student/submission labels, mixed-case names, or other private provenance are replaced with digest-based IDs before reports are written.

## Local Outputs

These locations are where local-only artifacts should accumulate during normal use.

These paths are intended for local material:

- `data/`
- `reports/`
- `models/`
- `vectorstores/`
- SQLite database files

The `examples/reports/` folder is intended for deliberately public examples.

## Hosted Mode

Hosted mode changes the trust boundary, so it needs explicit operational safeguards rather than assuming local defaults still hold.

Hosted mode depends on authentication, tenant isolation, retention controls, deletion flows, and audit logging. See [Hosted Hardening](hosted-hardening.md).
