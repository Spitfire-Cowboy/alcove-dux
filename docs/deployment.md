# Deployment Notes

Alcove Dux is local-first by default. The Docker setup runs the API locally with a named SQLite state volume.

```bash
docker compose up --build
```

The container exposes `http://localhost:8000` and keeps local state in the `alcove_dux-state` volume.

Hosted-mode infrastructure experiments can add Postgres plus ChromaDB:

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.hosted.yml up --build
```

The hosted overlay is scaffolding for local experiments. The API uses local SQLite unless a storage adapter explicitly connects it to Postgres.

## Hosted Mode

Hosted deployment depends on the controls in [`hosted-hardening.md`](hosted-hardening.md):

- authentication for all document and scan endpoints
- explicit tenant isolation
- private object storage for uploaded documents
- encrypted database and backups
- retention settings for documents, reports, vectors, and logs
- audit logs that omit raw document text
- a public privacy and data deletion policy

Outbound corpus upload and shared vector indexes involve product and disclosure decisions.
