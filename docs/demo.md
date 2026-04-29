# Demo Walkthrough

This demo shows the simplest Alcove Dux loop: scan a short submitted passage against a known source, generate evidence, and inspect two report views.

## Run The Demo

```bash
python scripts/demo.py
```

The script writes demo outputs to `reports/demo/`:

- `demo.alcove-dux`
- `demo.html`
- `demo-review.html`

The `reports/` folder is reserved for local outputs.

## What The Demo Shows

1. Alcove Dux loads two local files from `examples/demo/`.
2. The CLI compares a submitted passage to a known source.
3. The JSON report records match kinds, scores, offsets, hashes, and runtime configuration.
4. The public HTML report summarizes evidence without raw matched text.
5. The local review HTML shows highlighted snippets for human inspection.

## Talk Track

For a live walkthrough, say:

> Alcove Dux does not decide whether misconduct happened. It finds similarity evidence and gives a reviewer enough context to inspect the source trail.

Then run:

```bash
python scripts/demo.py
```

Open the generated local review report and point out:

- the evidence summary
- match type
- score
- offsets
- highlighted suspicious and source passages
- the difference between public and local review exports

## Reset

Remove demo output with:

```bash
rm -rf reports/demo
```
