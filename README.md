<h1 align="center">Alcove Dux</h1>

<p align="center">
  <strong>Local-first plagiarism and text-reuse evidence for reviewers.</strong>
</p>

<p align="center">
  <a href="https://github.com/Spitfire-Cowboy/alcove-dux/actions/workflows/ci.yml"><img src="https://github.com/Spitfire-Cowboy/alcove-dux/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <img src="https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg" alt="Python 3.11 and 3.12" />
  <a href="https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License" /></a>
</p>

Alcove Dux is an open-source, local-first toolkit for reviewing plagiarism and text-reuse evidence.

Alcove Dux is a review aid, not an automated misconduct decision system. It helps humans inspect similarity evidence without making unsupported accusations.

For the full local dashboard and PDF/DOCX upload path, install the `api` and `documents`
extras together.

## ⚡ Start Here

- [Live Demo](https://spitfire-cowboy.github.io/alcove-dux/): try a browser-only sample scan.
- [Quick Start](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/quickstart.md): install locally and run a sample scan.
- [Demo Walkthrough](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/demo.md): run the sample demo and inspect the generated report.
- [CLI Usage](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/cli.md): command reference for pairwise scans, corpus scans, semantic matching, and calibration.
- [Reports](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/reports.md): JSON, public HTML, local review HTML, and report privacy behavior.
- [Privacy Boundary](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/privacy.md): what Alcove Dux does and does not expose.

## 🔎 What It Does

- Text, Markdown, PDF, and DOCX ingestion.
- Exact, fuzzy, semantic, and reranked similarity evidence.
- Pairwise scans and local-corpus scans from the CLI.
- Local FastAPI dashboard for document upload, scan creation, and side-by-side review.
- Screen-reader-friendly dashboard and HTML reports with privacy-preserving exports.

PDF/DOCX ingestion requires the optional `documents` extra in CLI or API installs.

## 📚 Documentation

- [Research Notes](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/research.md) and [Benchmarks](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/benchmarks.md)
- [AI-use stigma note](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/research-ai-use-stigma.md): why self-reported AI use is biased in education and what that changes for Alcove Dux.
- [Configuration](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/configuration.md), [Datasets](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/datasets.md), and [Multilingual Detection](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/multilingual.md)
- [Vector Stores](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/vector-stores.md) and [Alcove Plugin Plan](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/alcove-plugin.md)
- [Deployment Notes](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/deployment.md), [Hosted Hardening](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/hosted-hardening.md), and [Repository Setup](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/repository-setup.md)
- [Roadmap](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/roadmap.md) and [Demo Video Script](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/docs/demo-video.md)

## 📦 Package

The package name is `alcove-dux`, the import path is `alcove_dux`, and the CLI command is `alcove-dux`. The core engine can be used as a CLI, Python library, local FastAPI app, or Alcove plugin.

## 🤝 Contributing

Alcove Dux is maintained as a public open-source project. Contributions are encouraged to keep the local-first privacy boundary intact, include tests for behavioral changes, and keep private corpora, generated reports, model caches, and vector indexes out of public commits.

See [CONTRIBUTING.md](https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/CONTRIBUTING.md) for setup, checks, and privacy rules.
