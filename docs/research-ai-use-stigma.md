# AI-use stigma, underreporting, and what it means for Alcove Dux

A recent paper, *Underreporting of AI Use: The Role of Social Desirability Bias* (SSRN 5464215), argues that self-reported AI use is systematically distorted in high-stigma settings.

In the paper's educational sample, roughly 60% of students reported using AI themselves while roughly 90% reported that their peers use AI. In a follow-up survey, most respondents attributed the gap to embarrassment and social desirability rather than honest disagreement about actual usage.

## Why this matters for Alcove Dux

Alcove Dux operates in exactly the kind of setting where this distortion matters:

- students may underreport AI assistance because they fear accusations of cheating or laziness
- instructors may overestimate or underestimate AI use based on local norms, recent incidents, or moral panic
- institutional surveys about AI use are not reliable ground truth for product calibration or policy design

This reinforces the core Alcove Dux posture:

- evidence first
- local review first
- reviewer judgment over binary accusations

## Product implications

### 1. Prefer evidence over confession

Alcove Dux should never depend on students truthfully confessing how they used AI.

The product should help reviewers inspect:

- source overlap
- paraphrase cues
- mixed human/AI boundary signals
- reviewer notes and policy context

It should avoid framing that implies the software can determine guilt on its own.

### 2. Treat declared AI use as biased metadata

If a teacher, student, or institution reports whether AI was used, that input can still be useful, but it should be treated as context rather than clean labels.

That matters for:

- benchmark interpretation
- calibration datasets
- evaluation claims
- institutional reporting dashboards

### 3. Use mixed-provenance language

The paper's results are a reminder that shame-heavy environments reward overconfident labels.

Copy and UX should prefer:

- `similarity evidence`
- `possible paraphrase`
- `mixed human/AI boundary`
- `needs review`

And should avoid:

- `caught`
- `proved`
- `cheated`
- `AI verdict`

### 4. Research the norm gap directly

When Alcove Dux does user research, ask both direct and indirect questions.

Examples:

- How often do your students disclose AI use?
- How often do you think students in your department use AI assistance?
- How often do other instructors in your institution believe AI use is acceptable?

The gap between own-report and peer-report is often more informative than either answer alone.

### 5. Keep privacy and local control central

The more stigma-heavy the environment, the more important it is that review artifacts stay under local institutional control.

That means local-first operation, explicit trust boundaries, and conservative exports are not just privacy features; they also reduce the pressure that distorts measurement in the first place.

## Research and evaluation implications

Alcove Dux should distinguish between:

- observed evidence in documents
- reviewer interpretations of that evidence
- self-reported AI use by students or instructors

Those are not interchangeable.

In practice, that means:

- do not advertise self-reported AI-use rates as a benchmark truth source
- document when a dataset relies on disclosure or survey answers
- prefer artifact-linked evaluation where possible
- note that policy and stigma can shift reported usage without changing underlying behavior

## Recommended stance

Alcove Dux should continue to position itself as a local-first review aid for contested authorship and similarity questions, not as a confession extractor or automated misconduct judge.

The paper supports that posture strongly.
