# Alcove Dux Roadmap

Alcove Dux is an open-source, local-first toolkit for reviewing plagiarism and text-reuse evidence. It is built for educators, editors, researchers, and small institutions that need transparent similarity review without sending private documents to a closed service.

## Product Goal

Alcove Dux aims to make similarity review understandable and auditable. A reviewer can ingest documents, compare submitted work against known sources or a local corpus, and inspect evidence with clear offsets, scores, source passages, hashes, model information, and privacy-aware exports.

Alcove Dux is not an automated misconduct decision system. It helps people review evidence; it does not decide intent, policy, or discipline.

## Principles

- Local-first by default: documents and embeddings stay on the user's device unless they choose a hosted deployment.
- Evidence over decisions: show the matched passages, scores, methods, and uncertainty instead of making accusations.
- Open and auditable: prefer permissive licenses, documented models, reproducible thresholds, and inspectable reports.
- Configurable by design: models, datasets, thresholds, and vector stores are selected through configuration.
- Public-safe by default: public examples and docs omit private paths, private infrastructure names, credentials, and personally identifying information.
- Accessible review: dashboards and reports are designed to work well with keyboard navigation and screen readers.

## Detection Approach

Alcove Dux combines several evidence types:

- Exact passage matches for copied text.
- Lexical and fuzzy similarity for lightly edited text.
- Semantic similarity for paraphrase and meaning-preserving reuse.
- Optional reranking for higher-confidence candidate review.
- Corpus search when a reviewer has a submitted document and a local source collection.
- Pairwise comparison when a reviewer already knows the two documents to inspect.

Reports are designed to record enough context for another reviewer to understand how the evidence was produced.

## Current Capabilities

### Document Ingest

- [x] Normalize plain text and preserve Unicode.
- [x] Compute SHA-256 text hashes.
- [x] Chunk documents by paragraph and character window.
- [x] Load plain text, Markdown, PDF, and DOCX files.
- [x] Upload plain text, Markdown, PDF, DOCX, and pasted text through the local app.
- [x] Store local document metadata, hashes, text length, chunks, offsets, and source IDs.
- [x] Sanitize private-looking document IDs before report export.
- [x] Scan one submitted text file against a local text or Markdown corpus.

### Similarity Detection

- [x] Detect exact substring overlap.
- [x] Detect exact token-sequence spans.
- [x] Score token Jaccard and containment similarity.
- [x] Detect exact n-gram matches.
- [x] Retrieve candidates with SimHash.
- [x] Configure lexical similarity thresholds per scan.
- [x] Generate embeddings for chunks with a configured local model.
- [x] Store vectors in a local vector index.
- [x] Retrieve semantically similar source chunks.
- [x] Score semantic candidates with cosine similarity.
- [x] Apply saved calibration profiles during scans.
- [x] Add an optional reranker pass for top candidates.

### Reports And Review UI

- [x] Produce structured `.alcove-dux` JSON reports.
- [x] Export public HTML summaries without raw matched text.
- [x] Export local review HTML with highlighted matched snippets.
- [x] Show local dashboard views for document upload, scan creation, scan status, and side-by-side review.
- [x] Use evidence-first labels such as exact overlap, near duplicate, possible paraphrase, and needs review.
- [x] Use evidence language instead of verdict language such as `plagiarized` in UI labels.
- [x] Add screen-reader landmarks, labels, captions, skip links, focus styles, and named review regions.
- [x] Include small public-safe example reports.

### Evaluation

- [x] Load PAN-PC-11.
- [x] Load PAN Text Alignment.
- [x] Load PlagBench.
- [x] Load PAWS.
- [x] Load STS Benchmark.
- [x] Load MRPC.
- [x] Track precision, recall, F1, and PlagDet-style metrics where available.
- [x] Save benchmark and calibration reports with model, threshold, and dataset metadata.
- [x] Add regression tests for high-overlap cases that are not classified as paraphrase reuse.

### Configuration

- [x] Publish a model and dataset catalog in [`config/catalog.yaml`](config/catalog.yaml).
- [x] Load catalog entries through the package API.
- [x] Support a default embedding model, optional long-context model, optional reranker, and multilingual candidates.
- [x] Enable or disable dataset loaders independently.
- [x] Store model IDs, licenses, source URLs, intended use, sequence-length notes, and threshold notes.
- [x] Store dataset IDs, licenses, source URLs, intended use, acquisition notes, and evaluation metrics.
- [x] Save resolved runtime configuration with each scan report.

### Integrations And Deployment

- [x] Package Alcove Dux as a Python library, CLI, and local FastAPI app.
- [x] Add an Alcove report extractor for `.alcove-dux` files.
- [x] Keep the Alcove integration offline by default and focused on retrieval and review.
- [x] Add Docker Compose for the local API app and SQLite state volume.
- [x] Add optional ChromaDB support and track zvec as experimental.
- [x] Document hosted deployment considerations for teams that choose to run Alcove Dux on a server.

### Multilingual Support

- [x] Preserve multilingual text through normalization and report generation.
- [x] Store language hints in runtime scan configuration.
- [x] Add language-aware tokenization for CJK, Thai, and other non-whitespace scripts.
- [x] Add multilingual embedding model candidates.
- [x] Add multilingual and cross-lingual benchmark datasets after license review.
- [x] Support threshold calibration by language and task type.
- [x] Include a public-safe demo corpus for local testing.

## Current Milestones

### Milestone 1: Security baseline on `develop`

- [ ] Merge the dependency and workflow hardening PRs into `develop`.
- [ ] Close the remaining Dependabot alerts on the default branch.
- [x] Keep code scanning at zero open alerts after workflow cleanup.

### Milestone 2: Release candidate to `main`

- [ ] Open a `develop` → `main` release PR.
- [ ] Summarize the release candidate scope in `CHANGELOG.md`.
- [ ] Confirm version metadata and release workflow readiness for the next cut.

### Milestone 3: Cut the next release

- [ ] Merge the release PR into `main`.
- [ ] Create the GitHub release from `main`.
- [ ] Verify the build and optional PyPI publish jobs complete successfully.

## Near-Term Priorities

- [ ] Improve benchmark documentation with clearer caveats, dataset licenses, and sample size notes.
- [ ] Add a guided demo flow that can be run from the CLI and the local dashboard.
- [ ] Expand accessibility testing for dashboard and HTML reports.
- [ ] Add more public-safe examples that show exact match, near duplicate, paraphrase, and no-match cases.
- [ ] Document threshold profiles by task, language, and review context.
- [ ] Prepare the `develop` → `main` release PR once security changes land on `develop`.

## Future Work

- Hosted mode with authentication, authorization, retention controls, deletion controls, tenant isolation, and audit logs.
- Larger benchmark runs on dedicated storage, including peS2o sampling and additional PAN evaluations.
- Better boilerplate, quotation, citation, and bibliography filtering.
- More multilingual and cross-lingual evaluation.
- Optional source retrieval from larger local academic collections.
- Code-reuse detection as a separate research track.
- Alcove workflows for launching scans from local collections.

## Architecture

- Core: Python package with library API and CLI.
- Review app: local FastAPI dashboard for uploads, scans, and evidence review.
- Storage: SQLite by default, with Postgres as a hosted deployment option.
- Vector stores: local in-process vectors by default, with optional ChromaDB and experimental zvec paths.
- Models: local Sentence Transformers by default, with optional adapters for compatible embedding backends.
- Jobs: background scan work for longer semantic comparisons.

## Open Questions

- Which audience is the primary public focus: educators, editors, or researchers?
- Is code-reuse detection part of the main product, or a separate research track?
- Which multilingual benchmarks are appropriate to include by default after license review?
- What public expansion, if any, works well for `dux`?
