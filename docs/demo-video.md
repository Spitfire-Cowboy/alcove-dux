# Demo Video Script

This script supports a short Alcove Dux walkthrough video.

## Goal

Show Alcove Dux as a local-first evidence review tool, not an automated misconduct decision system.

Target length: 90 to 120 seconds.

## Shot list

| Time | Visual | Voiceover |
| --- | --- | --- |
| 0:00 | README title and badges | "This is Alcove Dux, a local-first toolkit for similarity and text-reuse evidence." |
| 0:08 | Quick start page | "It is designed for reviewers who need source trails, offsets, and transparent evidence without sending private documents to a closed service." |
| 0:18 | Demo command | "The demo scans a submitted passage against a known source and creates two report views." |
| 0:35 | Generated JSON report | "The JSON report records hashes, offsets, match kinds, scores, and runtime configuration." |
| 0:50 | Public HTML report | "The public HTML summary avoids raw private text. It is meant for safe sharing of evidence metadata." |
| 1:05 | Local review HTML report | "The local review page includes highlighted snippets so a human can inspect what matched and why." |
| 1:25 | Privacy page | "Alcove Dux is a review aid. It does not declare misconduct. It keeps private documents local unless a reviewer deliberately exports them." |
| 1:40 | Documentation list | "The documentation covers benchmarks, multilingual detection, vector-store options, deployment, and Alcove integration." |

## Full narration

Alcove Dux is a local-first toolkit for similarity and text-reuse evidence.

It is built for reviewers who need source trails, offsets, and transparent evidence without sending private documents to a closed service.

In this demo, everything runs from local files. We scan a short submitted passage against a known source and generate two report views.

The JSON report records the evidence in structured form: document hashes, match kinds, scores, offsets, selected configuration, and explanations.

The public HTML report summarizes evidence without exposing raw matched text.

The local review report is for private review. It includes highlighted snippets so a human can inspect what matched and decide what context matters.

Alcove Dux does not decide whether misconduct happened. It helps reviewers inspect similarity evidence with a clear privacy boundary.

The documentation also covers benchmarks, multilingual detection, vector-store options, deployment, and Alcove integration.

## Recording notes

- Increase terminal font size before recording.
- Prefer the demo files under `examples/demo/`.
- Keep unrelated browser tabs and local documents out of frame.
- Publish the finished video through the project's chosen video or documentation host.

## Production checklist

- Run `python scripts/demo.py`.
- Open `reports/demo/demo.html`.
- Open `reports/demo/demo-review.html`.
- Record the walkthrough.
- Add narration using the script above.
- Review captions for accuracy.
- Verify no private material appears in the recording.
