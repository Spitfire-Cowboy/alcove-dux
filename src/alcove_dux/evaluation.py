"""Benchmark metric helpers."""

from __future__ import annotations

from dataclasses import dataclass
from statistics import mean


@dataclass(frozen=True)
class ClassificationMetrics:
    """Binary classification metrics."""

    accuracy: float
    precision: float
    recall: float
    f1: float
    tp: int
    fp: int
    tn: int
    fn: int

    def to_dict(self) -> dict[str, float | int]:
        return {
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "tp": self.tp,
            "fp": self.fp,
            "tn": self.tn,
            "fn": self.fn,
        }


@dataclass(frozen=True)
class Span:
    """Half-open character span."""

    start: int
    end: int

    @classmethod
    def from_offset_length(cls, offset: int, length: int) -> Span:
        if offset < 0:
            raise ValueError("offset must be non-negative")
        if length < 0:
            raise ValueError("length must be non-negative")
        return cls(start=offset, end=offset + length)

    @property
    def length(self) -> int:
        return max(self.end - self.start, 0)


@dataclass(frozen=True)
class SpanOverlapMetrics:
    """Character overlap metrics for predicted and truth spans."""

    precision: float
    recall: float
    f1: float
    predicted_chars: int
    truth_chars: int
    overlap_chars: int

    def to_dict(self) -> dict[str, float | int]:
        return {
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "predicted_chars": self.predicted_chars,
            "truth_chars": self.truth_chars,
            "overlap_chars": self.overlap_chars,
        }


def binary_classification_metrics(
    expected: list[bool],
    predicted: list[bool],
) -> ClassificationMetrics:
    """Compute binary classification metrics."""

    if len(expected) != len(predicted):
        raise ValueError("expected and predicted must have the same length")

    tp = fp = tn = fn = 0
    for expected_value, predicted_value in zip(expected, predicted, strict=True):
        if predicted_value and expected_value:
            tp += 1
        elif predicted_value and not expected_value:
            fp += 1
        elif not predicted_value and expected_value:
            fn += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / max(tp + tn + fp + fn, 1)
    return ClassificationMetrics(
        accuracy=accuracy,
        precision=precision,
        recall=recall,
        f1=f1,
        tp=tp,
        fp=fp,
        tn=tn,
        fn=fn,
    )


def span_overlap_metrics(truth: list[Span], predicted: list[Span]) -> SpanOverlapMetrics:
    """Compute character-level overlap metrics over two span sets."""

    truth_chars = _covered_chars(truth)
    predicted_chars = _covered_chars(predicted)
    overlap_chars = _overlap_chars(truth, predicted)
    precision = overlap_chars / predicted_chars if predicted_chars else 0.0
    recall = overlap_chars / truth_chars if truth_chars else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return SpanOverlapMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        predicted_chars=predicted_chars,
        truth_chars=truth_chars,
        overlap_chars=overlap_chars,
    )


def mean_absolute_error(expected: list[float], predicted: list[float]) -> float:
    """Compute mean absolute error."""

    if len(expected) != len(predicted):
        raise ValueError("expected and predicted must have the same length")
    if not expected:
        return 0.0
    return mean(abs(left - right) for left, right in zip(expected, predicted, strict=True))


def _covered_chars(spans: list[Span]) -> int:
    return sum(span.length for span in _merge_spans(spans))


def _overlap_chars(left: list[Span], right: list[Span]) -> int:
    left_merged = _merge_spans(left)
    right_merged = _merge_spans(right)
    total = 0
    right_index = 0
    for left_span in left_merged:
        while right_index < len(right_merged) and right_merged[right_index].end <= left_span.start:
            right_index += 1
        probe = right_index
        while probe < len(right_merged) and right_merged[probe].start < left_span.end:
            total += max(
                min(left_span.end, right_merged[probe].end)
                - max(left_span.start, right_merged[probe].start),
                0,
            )
            probe += 1
    return total


def _merge_spans(spans: list[Span]) -> list[Span]:
    normalized = sorted(
        (span for span in spans if span.length > 0),
        key=lambda span: (span.start, span.end),
    )
    if not normalized:
        return []

    merged = [normalized[0]]
    for span in normalized[1:]:
        current = merged[-1]
        if span.start <= current.end:
            merged[-1] = Span(start=current.start, end=max(current.end, span.end))
        else:
            merged.append(span)
    return merged
