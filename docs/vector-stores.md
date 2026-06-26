# Vector Stores

Alcove Dux keeps vector storage optional. The base package ships a JSONL-capable local index for tests and demos.

## ChromaDB

ChromaDB is an optional vector database target for persistent local storage.

Install:

```bash
python -m pip install -e ".[vector-chroma]"
```

It supports:

- local persistent vector indexes
- metadata filtering
- collection management

## Experimental Backend: zvec

zvec is an embedded optional vector target under evaluation. Alcove Dux does not
ship a stable runtime adapter for it yet; the current extra is only for dependency
and packaging experiments while the API surface is validated across supported
environments.

Install when experimenting:

```bash
python -m pip install -e ".[vector-zvec]"
```

Today it supports:

- dependency install experiments
- package metadata validation
- planning for a future embedded adapter

## Privacy Rule

Vector indexes can reveal corpus membership or provenance through embeddings, chunk IDs, and metadata.
