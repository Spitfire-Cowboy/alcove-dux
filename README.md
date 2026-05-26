<h1 align="center">Alcove Dux</h1>

<p align="center">
  <strong>Local-first similarity evidence for teachers and academic reviewers — you decide what it means.</strong>
</p>

<p align="center">
  <a href="https://github.com/Spitfire-Cowboy/alcove-dux/actions/workflows/ci.yml"><img src="https://github.com/Spitfire-Cowboy/alcove-dux/actions/workflows/ci.yml/badge.svg" alt="CI" /></a>
  <img src="https://img.shields.io/badge/status-pre--alpha-orange.svg" alt="Pre-alpha" />
  <img src="https://img.shields.io/badge/python-3.11%20%7C%203.12-blue.svg" alt="Python 3.11 and 3.12" />
  <a href="https://github.com/Spitfire-Cowboy/alcove-dux/blob/develop/LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-lightgrey.svg" alt="License" /></a>
</p>

![Alcove Dux review screenshot](docs/assets/hero.png)

Alcove Dux is an open-source, local-first toolkit for K-12 teachers, instructors, academic reviewers, and small institutions that need transparent similarity review without sending student documents to a closed service.

Alcove Dux is a review aid, not a verdict machine. It helps teachers and reviewers inspect similarity evidence on their own hardware, and unlike Turnitin and similar cloud services, Alcove Dux never uploads student documents to a third-party server. Similarity evidence stays on your device and is reviewed by you, not scored by an algorithm and stored by a vendor.

## ⚡ Start Here

- [Quick Start](docs/quickstart.md): install locally and run a sample scan.
- [Institutional Deployment](docs/deployment.md): run Alcove Dux on a shared departmental or school server.
- [Demo Walkthrough](docs/demo.md): run the sample demo and inspect the generated report.
- [CLI Usage](docs/cli.md): command reference for pairwise scans, corpus scans, semantic matching, and calibration.
- [Reports](docs/reports.md): JSON, public HTML, local review HTML, and report privacy behavior.
- [Privacy Boundary](docs/privacy.md): what Alcove Dux does and does not expose.

## 🔎 What It Does

An instructor uploads two documents, runs a scan, and gets a side-by-side highlighted report — locally, without sending text to any server.

No command line is required for the main workflow: open the local dashboard in your browser, upload documents, and review the results there.

## 🖥️ Dashboard preview

The local dashboard is the main review surface for most teachers and academic reviewers:

![Alcove Dux dashboard screenshot](docs/assets/dashboard-screenshot.png)

- Local FastAPI dashboard for document upload, scan creation, and side-by-side review.
- Text, Markdown, PDF, and DOCX ingestion.
- Exact, fuzzy, semantic, and reranked similarity evidence.
- Pairwise scans and local-corpus scans from the CLI.
- Screen-reader-friendly dashboard and HTML reports with privacy-preserving exports.

## 👩‍🏫 Who This Is For

- Classroom teachers reviewing student submissions.
- Instructors comparing assignments against known sources.
- Department or institution-level academic integrity reviewers.
- Small schools and colleges that want local control instead of cloud document retention.

## 🏫 Institutional deployment quick path

For a shared departmental or school installation, the fastest path is usually Docker Compose on an inward-facing server:

```bash
docker compose up --build
```

Then open `http://localhost:8000` on that machine, or place it behind your institution's normal internal access controls. See [Deployment Notes](docs/deployment.md) for role separation, retention, and hosted-mode guidance.

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
