# Hosted Hardening

Alcove Dux is local-first. Hosted deployments depend on the controls below.

## Recommended Controls

- Authentication and authorization on every document, scan, report, and vector endpoint.
- Tenant isolation at the database, object storage, job, and vector-index layers.
- TLS at the public edge and private network boundaries between services.
- Secret storage through the hosting platform or a dedicated secret manager, not checked-in files.
- Private object storage for uploaded documents with encryption at rest.
- Encrypted database backups with a documented restore test.
- Retention settings for documents, extracted chunks, reports, vectors, logs, and backups.
- Audit logging that records actions without raw document text, local paths, or private provenance.
- Upload limits, file type validation, malware scanning, and request rate limits.
- CORS, cookie, and session settings locked to the deployed domain.
- Administrative deletion tools for documents, reports, vectors, and user accounts.

## Current Overlay

`docker-compose.hosted.yml` adds Postgres with pgvector and ChromaDB for local infrastructure experiments. It does not turn the API into a production hosted service, and the API still uses SQLite until a storage adapter connects hosted services.

Copy `.env.example` to `.env` for local Docker experiments and replace every placeholder before putting anything on a network. Keep `.env`, corpora, reports, model caches, and vector indexes out of source control.

## Privacy Boundary

Hosted reports and logs can expose stable document IDs, hashes, offsets, scores, and reviewer decisions. They are designed to omit raw private text, local filesystem paths, private infrastructure names, credentials, and personally identifying information unless a user explicitly exports a local review artifact for their own use.
