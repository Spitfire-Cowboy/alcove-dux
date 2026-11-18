import json

import pytest

from alcove_dux.calibration import (
    calibrate_lexical_threshold,
    calibrate_lexical_threshold_by_language,
    calibrate_score_threshold,
)
from alcove_dux.datasets.pairs import PairExample


def test_calibrate_lexical_threshold_selects_best_threshold(tmp_path):
    copied = "Alpha beta gamma delta epsilon zeta eta theta iota."
    examples = [
        PairExample("positive", copied, f"Intro {copied}", True, {}),
        PairExample("negative", "Alpha beta gamma", "finance market earnings", False, {}),
    ]

    profile = calibrate_lexical_threshold(
        examples,
        dataset_id="toy",
        thresholds=(0.50, 0.90),
        language="en",
        task_type="exact_reuse",
    )
    output = tmp_path / "profile.json"
    profile.save(output)

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["dataset_id"] == "toy"
    assert payload["detector_id"] == "baseline_lexical"
    assert payload["selected_threshold"] in {0.50, 0.90}
    assert payload["scores"]
    assert payload["language"] == "en"
    assert payload["task_type"] == "exact_reuse"


def test_calibrate_lexical_threshold_rejects_invalid_examples():
    with pytest.raises(ValueError):
        calibrate_lexical_threshold([], dataset_id="empty")

    with pytest.raises(ValueError):
        calibrate_lexical_threshold(
            [PairExample("stsb", "a", "b", 0.5, {})],
            dataset_id="stsb",
        )


def test_calibrate_lexical_threshold_by_language():
    copied = "Alpha beta gamma delta epsilon zeta eta theta iota."
    examples = [
        PairExample("en-positive", copied, copied, True, {"language": "en"}),
        PairExample("en-negative", "alpha", "omega", False, {"language": "en"}),
        PairExample("es-positive", copied, copied, True, {"language": "es"}),
        PairExample("es-negative", "uno", "dos", False, {"language": "es"}),
    ]

    profiles = calibrate_lexical_threshold_by_language(
        examples,
        dataset_id="toy",
        thresholds=(0.50,),
        task_type="paraphrase",
    )

    assert sorted(profiles) == ["en", "es"]
    assert profiles["es"].language == "es"
    assert profiles["es"].task_type == "paraphrase"


def test_calibrate_lexical_threshold_by_language_requires_metadata():
    with pytest.raises(ValueError):
        calibrate_lexical_threshold_by_language(
            [PairExample("missing", "a", "b", False, {})],
            dataset_id="toy",
        )


def test_calibrate_score_threshold_selects_best_result_under_cap():
    profile = calibrate_score_threshold(
        [True, True, False, False],
        [0.9, 0.7, 0.8, 0.1],
        dataset_id="held-out",
        detector_id="detector-v2",
        thresholds=(0.5, 0.75, 0.85),
        false_positive_rate_cap=0.0,
    )

    assert profile.selected_threshold == 0.85
    assert profile.selection_metric == "true_positive_rate_at_fpr_cap"
    assert profile.false_positive_rate_cap == 0.0
    assert profile.scores[-1].metrics["false_positive_rate"] == 0.0
    assert profile.scores[-1].metrics["true_positive_rate"] == 0.5


def test_calibrate_score_threshold_uses_conservative_threshold_for_ties():
    profile = calibrate_score_threshold(
        [True, False],
        [0.9, 0.7],
        dataset_id="held-out",
        detector_id="detector-v2",
        thresholds=(0.8, 0.85),
        false_positive_rate_cap=0.0,
    )

    assert profile.selected_threshold == 0.85


def test_calibrate_score_threshold_requires_negative_examples():
    with pytest.raises(ValueError, match="negative example"):
        calibrate_score_threshold(
            [True, True],
            [0.9, 0.8],
            dataset_id="held-out",
            detector_id="detector-v2",
            thresholds=(0.5,),
            false_positive_rate_cap=0.01,
        )


def test_calibrate_score_threshold_rejects_grid_without_qualifying_threshold():
    with pytest.raises(ValueError, match="no supplied threshold"):
        calibrate_score_threshold(
            [True, False],
            [0.9, 0.9],
            dataset_id="held-out",
            detector_id="detector-v2",
            thresholds=(0.5, 0.8),
            false_positive_rate_cap=0.0,
        )
