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

zvec is an embedded optional vector target. Alcove Dux marks it experimental while the Python packaging surface and API stability are validated across supported environments.

Install when experimenting:

```bash
python -m pip install -e ".[vector-zvec]"
```

It supports:

- embedded vector storage
- local index experiments
- adapter validation against local corpora

## Privacy Rule

Vector indexes can reveal corpus membership or provenance through embeddings, chunk IDs, and metadata.
