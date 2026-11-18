"""Threshold calibration helpers."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from alcove_dux.datasets.pairs import PairExample
from alcove_dux.evaluation import binary_classification_metrics, score_threshold_sweep
from alcove_dux.matching import compare_texts

BASELINE_LEXICAL_DETECTOR_ID = "baseline_lexical"


def _validated_false_positive_rate_cap(value: object) -> float | None:
    if value is None:
        return None
    try:
        cap = float(value)
    except (OverflowError, TypeError, ValueError) as error:
        raise ValueError("false_positive_rate_cap must be finite and between 0 and 1") from error
    if not math.isfinite(cap) or not 0 <= cap <= 1:
        raise ValueError("false_positive_rate_cap must be finite and between 0 and 1")
    return cap


@dataclass(frozen=True)
class ThresholdScore:
    """Metrics for one threshold."""

    threshold: float
    metrics: dict[str, float | int]

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible data."""

        return {"threshold": self.threshold, "metrics": self.metrics}


@dataclass(frozen=True)
class CalibrationProfile:
    """A saved calibration profile for a detector/dataset pair."""

    dataset_id: str
    detector_id: str
    selected_threshold: float
    selection_metric: str
    scores: tuple[ThresholdScore, ...]
    language: str | None = None
    task_type: str | None = None
    false_positive_rate_cap: float | None = None

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible data."""

        payload = asdict(self)
        payload["scores"] = [score.to_dict() for score in self.scores]
        payload["false_positive_rate_cap"] = _validated_false_positive_rate_cap(
            self.false_positive_rate_cap
        )
        return payload

    def to_json(self, *, indent: int = 2) -> str:
        """Serialize as JSON."""

        return json.dumps(self.to_dict(), indent=indent, sort_keys=True, allow_nan=False)

    def save(self, path: str | Path) -> None:
        """Save the calibration profile."""

        serialized = self.to_json() + "\n"
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized, encoding="utf-8")

    def threshold_for_detector(self, detector_id: str) -> float:
        """Return the threshold only when the profile matches the active detector."""

        if self.detector_id != detector_id:
            raise ValueError(
                f"Calibration profile detector {self.detector_id!r} does not match "
                f"active detector {detector_id!r}"
            )
        return self.selected_threshold

    @classmethod
    def load(cls, path: str | Path) -> CalibrationProfile:
        """Load a calibration profile from JSON."""

        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        cap = _validated_false_positive_rate_cap(payload.get("false_positive_rate_cap"))
        return cls(
            dataset_id=str(payload["dataset_id"]),
            detector_id=str(payload["detector_id"]),
            selected_threshold=float(payload["selected_threshold"]),
            selection_metric=str(payload["selection_metric"]),
            scores=tuple(
                ThresholdScore(
                    threshold=float(score["threshold"]),
                    metrics=dict(score["metrics"]),
                )
                for score in payload.get("scores", [])
            ),
            language=payload.get("language"),
            task_type=payload.get("task_type"),
            false_positive_rate_cap=cap,
        )


def calibrate_score_threshold(
    expected: list[bool],
    scores: list[float],
    *,
    dataset_id: str,
    detector_id: str,
    thresholds: tuple[float, ...],
    false_positive_rate_cap: float,
    language: str | None = None,
    task_type: str | None = None,
) -> CalibrationProfile:
    """Select the most sensitive score threshold within an FPR policy cap."""

    if not 0 <= false_positive_rate_cap <= 1:
        raise ValueError("false_positive_rate_cap must be between 0 and 1")
    if not all(0 <= score <= 1 for score in scores):
        raise ValueError("calibration scores must be normalized between 0 and 1")
    if not all(0 <= threshold <= 1 for threshold in thresholds):
        raise ValueError("calibration thresholds must be between 0 and 1")
    sweep = score_threshold_sweep(expected, scores, thresholds)
    if not any(not label for label in expected):
        raise ValueError("policy-cap calibration requires at least one negative example")
    if not any(expected):
        raise ValueError("policy-cap calibration requires at least one positive example")

    candidates = tuple(
        result for result in sweep if result.metrics.false_positive_rate <= false_positive_rate_cap
    )
    if not candidates:
        raise ValueError("no supplied threshold satisfies the false-positive-rate cap")

    selected = max(
        candidates,
        key=lambda result: (
            result.metrics.true_positive_rate,
            result.metrics.precision,
            -result.metrics.false_positive_rate,
            result.threshold,
        ),
    )
    return CalibrationProfile(
        dataset_id=dataset_id,
        detector_id=detector_id,
        selected_threshold=selected.threshold,
        selection_metric="true_positive_rate_at_fpr_cap",
        scores=tuple(
            ThresholdScore(
                threshold=result.threshold,
                metrics=result.metrics.to_dict(round_digits=None),
            )
            for result in sweep
        ),
        language=language,
        task_type=task_type,
        false_positive_rate_cap=false_positive_rate_cap,
    )


def calibrate_lexical_threshold(
    examples: list[PairExample],
    *,
    dataset_id: str,
    thresholds: tuple[float, ...] = (0.40, 0.50, 0.55, 0.60, 0.70, 0.80, 0.90),
    selection_metric: str = "f1",
    language: str | None = None,
    task_type: str | None = None,
) -> CalibrationProfile:
    """Select a lexical threshold from labeled pair examples."""

    if not examples:
        raise ValueError("examples must not be empty")
    for example in examples:
        if not isinstance(example.label, bool):
            raise ValueError("lexical threshold calibration requires boolean labels")

    scores = tuple(_score_threshold(examples, threshold) for threshold in thresholds)
    selected = max(
        scores,
        key=lambda score: (
            float(score.metrics.get(selection_metric, 0)),
            float(score.metrics.get("precision", 0)),
            float(score.metrics.get("recall", 0)),
        ),
    )
    return CalibrationProfile(
        dataset_id=dataset_id,
        detector_id=BASELINE_LEXICAL_DETECTOR_ID,
        selected_threshold=selected.threshold,
        selection_metric=selection_metric,
        scores=scores,
        language=language,
        task_type=task_type,
    )


def calibrate_lexical_threshold_by_language(
    examples: list[PairExample],
    *,
    dataset_id: str,
    language_metadata_key: str = "language",
    thresholds: tuple[float, ...] = (0.40, 0.50, 0.55, 0.60, 0.70, 0.80, 0.90),
    selection_metric: str = "f1",
    task_type: str | None = None,
) -> dict[str, CalibrationProfile]:
    """Create calibration profiles grouped by language metadata."""

    grouped: dict[str, list[PairExample]] = {}
    for example in examples:
        language = example.metadata.get(language_metadata_key)
        if not language:
            continue
        grouped.setdefault(language, []).append(example)
    if not grouped:
        raise ValueError(f"No examples contained metadata key: {language_metadata_key}")
    return {
        language: calibrate_lexical_threshold(
            language_examples,
            dataset_id=dataset_id,
            thresholds=thresholds,
            selection_metric=selection_metric,
            language=language,
            task_type=task_type,
        )
        for language, language_examples in sorted(grouped.items())
    }


def _score_threshold(examples: list[PairExample], threshold: float) -> ThresholdScore:
    expected = [bool(example.label) for example in examples]
    predicted = [
        bool(compare_texts(example.left_text, example.right_text, min_score=threshold))
        for example in examples
    ]
    return ThresholdScore(
        threshold=threshold,
        metrics=binary_classification_metrics(expected, predicted).to_dict(),
    )
