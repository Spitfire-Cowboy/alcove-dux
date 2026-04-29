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

## ⚡ Start Here

- [Live Demo](https://spitfire-cowboy.github.io/alcove-dux/): try a browser-only sample scan.
- [Quick Start](docs/quickstart.md): install locally and run a sample scan.
- [Demo Walkthrough](docs/demo.md): run the sample demo and inspect the generated report.
- [CLI Usage](docs/cli.md): command reference for pairwise scans, corpus scans, semantic matching, and calibration.
- [Reports](docs/reports.md): JSON, public HTML, local review HTML, and report privacy behavior.
- [Privacy Boundary](docs/privacy.md): what Alcove Dux does and does not expose.

## 🔎 What It Does

- Text, Markdown, PDF, and DOCX ingestion.
- Exact, fuzzy, semantic, and reranked similarity evidence.
- Pairwise scans and local-corpus scans from the CLI.
- Local FastAPI dashboard for document upload, scan creation, and side-by-side review.
- Screen-reader-friendly dashboard and HTML reports with privacy-preserving exports.

## 📚 Documentation

- [Research Notes](docs/research.md) and [Benchmarks](docs/benchmarks.md)
- [Configuration](docs/configuration.md), [Datasets](docs/datasets.md), and [Multilingual Detection](docs/multilingual.md)
- [Vector Stores](docs/vector-stores.md) and [Alcove Plugin Plan](docs/alcove-plugin.md)
- [Deployment Notes](docs/deployment.md), [Hosted Hardening](docs/hosted-hardening.md), and [Repository Setup](docs/repository-setup.md)
- [Roadmap](roadmap.md) and [Demo Video Script](docs/demo-video.md)

## 📦 Package

The package name is `alcove-dux`, the import path is `alcove_dux`, and the CLI command is `alcove-dux`. The core engine can be used as a CLI, Python library, local FastAPI app, or Alcove plugin.

## 🤝 Contributing

Alcove Dux is maintained as a public open-source project. Contributions are encouraged to keep the local-first privacy boundary intact, include tests for behavioral changes, and keep private corpora, generated reports, model caches, and vector indexes out of public commits.

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, checks, and privacy rules.
