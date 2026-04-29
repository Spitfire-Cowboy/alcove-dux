import json

import pytest

from alcove_dux.calibration import (
    calibrate_lexical_threshold,
    calibrate_lexical_threshold_by_language,
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
