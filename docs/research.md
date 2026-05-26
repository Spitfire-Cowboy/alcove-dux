# Research Notes

This is the public research basis for Alcove Dux.
The academic literature often uses the term `plagiarism detection`; Alcove Dux uses that literature to build similarity evidence for human review rather than an automated verdict.

## Bottom Line

Alcove Dux is scoped as a text-focused, evidence-first similarity review tool:

- local corpus ingestion
- lexical matching for copy and light edits
- embedding retrieval for paraphrase and summarization
- span alignment
- reviewer UI that says `similarity evidence`, not `plagiarism decision`

The literature repeatedly warns that software supports review but cannot determine misconduct on its own.

## Key Technical Direction

Use a two-stage pipeline:

1. Candidate retrieval with paragraph/window embeddings plus lexical shingling, MinHash, or SimHash.
2. Evidence alignment with lexical overlap, containment, semantic cosine, and optional reranking.

Combine lexical and semantic signals:

- Lexical methods catch verbatim, reordered, lightly edited, and boilerplate reuse.
- BERT/SBERT/Longformer-style embeddings catch paraphrase and summary-like reuse.
- Explainable semantic Jaccard/edit-distance ideas can be used as features even if they are not the core model.

LLM paraphrase is in scope, but `LLM detector` branding is intentionally avoided. The product claim is source alignment: Alcove Dux finds passages that appear to derive from or closely resemble known sources.

## Datasets And Benchmarks

- [PAN 2025 plagiarism task](https://arxiv.org/abs/2510.06805): LLM-generated scientific plagiarism using open and proprietary generators; simple embeddings can reach high recall but weaker precision and poor generalization.
- [PlagBench](https://arxiv.org/abs/2406.16288): synthetic pairs covering verbatim copying, paraphrasing, and summarization.
- [Identifying Machine-Paraphrased Plagiarism](https://arxiv.org/abs/2103.11909): arXiv preprints, theses, and Wikipedia paraphrased with machine tools; Longformer-style models are relevant.
- [How Large Language Models are Transforming Machine-Paraphrased Plagiarism](https://arxiv.org/abs/2210.03568): LLM paraphrases are hard for humans and traditional tools.
- [Semantically-informed distance and similarity measures for paraphrase identification](https://arxiv.org/abs/1805.11611): paraphrase-plagiarism corpora with subtype labels for semantic matching evaluation.
- [Plagiarism Detection in arXiv](https://arxiv.org/abs/cs/0702012) and [Patterns of Text Reuse in a Scientific Corpus](https://arxiv.org/abs/1412.2716): scholarly text reuse baselines.
- [Wikipedia Text Reuse: Within and Without](https://arxiv.org/abs/1812.09221): large-scale retrieval pipeline and reuse corpus.

## Implement in v1

- PDF/text upload and clean extraction.
- Source-library indexing from user-provided corpora.
- Chunking by paragraph plus overlapping sentence windows.
- Vector retrieval with an open embedding model.
- Lexical shingling and containment score for exact and near-exact reuse.
- Exact token-sequence spans for high-confidence copied text.
- Span-level alignment and side-by-side highlighting.
- Filters for references, quotations, bibliography, formulas, boilerplate, and very short spans.
- Conservative labels: `high similarity`, `possible paraphrase`, `exact overlap`, `needs review`.
- Evaluation harness using PAN, PlagBench, and paraphrase pair data.

## Defer

- Production-grade cross-language plagiarism decisions beyond calibrated similarity evidence.
- Source-code plagiarism.
- Whole-web crawling.
- Intrinsic stylometry/authorship anomaly detection.
- Citation, image, math, and formula reuse.
- LLM-as-judge detection as the default path.

## Sources of misleading similarity

- Shared templates, assignment prompts, abstracts, methods boilerplate, legal wording, and standard wording.
- Reference lists, citations, quoted text, theorem statements, captions, and common definitions.
- Domain terminology causing high semantic similarity without copying.
- Summaries of the same source or common knowledge.
- Short chunks with unstable similarity.
- Self-reuse, which may be acceptable or unacceptable depending on policy.
- Synthetic benchmark overfitting.

## Paper Leads

- [Plagiarism: Taxonomy, Tools and Detection Techniques](https://arxiv.org/abs/1801.06323)
- [Methods for Detecting Paraphrase Plagiarism](https://arxiv.org/abs/1712.10309)
- [How Large Language Models are Transforming Machine-Paraphrased Plagiarism](https://arxiv.org/abs/2210.03568)
- [Identifying Machine-Paraphrased Plagiarism](https://arxiv.org/abs/2103.11909)
- [PlagBench: Exploring the Duality of Large Language Models in Plagiarism](https://arxiv.org/abs/2406.16288)
- [LLMs Plagiarize: Ensuring Responsible Sourcing of Large Language Model Outputs](https://arxiv.org/abs/2407.02659)
- [BERT-Enhanced Retrieval Tool for Homework Plagiarism Detection System](https://arxiv.org/abs/2404.01582)
- [A Novel Plagiarism Detection Approach Combining BERT-based Word Embeddings](https://arxiv.org/abs/2305.02374)
- [The Struggle with Academic Plagiarism: Approaches based on Semantic Similarity](https://arxiv.org/abs/2106.04404)
- [A Comparison of Document Similarity Algorithms](https://arxiv.org/abs/2304.01330)
- [TEIMMA: The First Content Reuse Annotator for Text, Images, and Math](https://arxiv.org/abs/2305.13193)
- [Testing of Support Tools for Plagiarism Detection](https://arxiv.org/abs/2002.04279)
- [Analyzing Non-Textual Content Elements to Detect Academic Plagiarism](https://arxiv.org/abs/2106.05764)
