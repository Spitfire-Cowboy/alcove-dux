# Deployment Notes

Alcove Dux is local-first by default. The Docker setup runs the API locally with a named SQLite state volume.

## Quick institutional path

For a shared departmental or school server, start here:

```bash
docker compose up --build
```

This gives you a local dashboard on `http://localhost:8000` backed by the default local state volume, which is usually the simplest first deployment for an internal-only pilot.

```bash
docker compose up --build
```

The container exposes `http://localhost:8000` and keeps local state in the `alcove_dux-state` volume.

For schools and universities, the most practical deployment is usually an inward-facing departmental or institutional server on the school network rather than a public internet-facing service.

Hosted-mode infrastructure experiments can add Postgres plus ChromaDB:

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.hosted.yml up --build
```

The hosted overlay is scaffolding for local experiments. The API uses local SQLite unless a storage adapter explicitly connects it to Postgres.

## Hosted Mode

For institutional use, role separation matters:

- teachers or reviewers upload documents and inspect reports
- IT administrators maintain the host, backups, access controls, and retention settings
- access to student work should follow the institution's existing policy and case-handling rules

Recommended retention posture for academic deployments:

- keep scan reports local
- delete routine scan artifacts after the academic term unless policy requires longer retention
- treat exported reports as student records when they contain identifiable submission context

Hosted deployment depends on the controls in [`hosted-hardening.md`](hosted-hardening.md):

- authentication for all document and scan endpoints
- explicit tenant isolation
- private object storage for uploaded documents
- encrypted database and backups
- retention settings for documents, reports, vectors, and logs
- audit logs that omit raw document text
- a public privacy and data deletion policy

Outbound corpus upload and shared vector indexes involve product and disclosure decisions.
