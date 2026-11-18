import pytest

from alcove_dux.evaluation import (
    ClassificationMetrics,
    Span,
    binary_classification_metrics,
    mean_absolute_error,
    score_threshold_sweep,
    span_overlap_metrics,
)


def test_binary_classification_metrics():
    metrics = binary_classification_metrics(
        expected=[True, True, False, False],
        predicted=[True, False, True, False],
    )

    assert metrics.tp == 1
    assert metrics.fn == 1
    assert metrics.fp == 1
    assert metrics.tn == 1
    assert metrics.accuracy == 0.5
    assert metrics.precision == 0.5
    assert metrics.recall == 0.5
    assert metrics.f1 == 0.5
    assert metrics.true_positive_rate == 0.5
    assert metrics.false_positive_rate == 0.5
    assert metrics.false_negative_rate == 0.5


def test_score_threshold_sweep_reports_policy_rates():
    sweep = score_threshold_sweep(
        expected=[True, True, False, False],
        scores=[0.9, 0.6, 0.7, 0.1],
        thresholds=(0.5, 0.8),
    )

    assert [result.threshold for result in sweep] == [0.5, 0.8]
    assert sweep[0].metrics.false_positive_rate == 0.5
    assert sweep[1].metrics.true_positive_rate == 0.5
    assert sweep[1].metrics.false_negative_rate == 0.5


def test_classification_metrics_can_preserve_small_policy_rates():
    metrics = ClassificationMetrics(
        accuracy=0.0,
        precision=0.0,
        recall=0.0,
        f1=0.0,
        tp=0,
        fp=1,
        tn=99_999,
        fn=0,
    )

    assert metrics.to_dict()["false_positive_rate"] == 0.0
    assert metrics.to_dict(round_digits=None)["false_positive_rate"] == pytest.approx(0.00001)


def test_score_threshold_sweep_validates_inputs():
    with pytest.raises(ValueError, match="same length"):
        score_threshold_sweep([True], [], (0.5,))

    with pytest.raises(ValueError, match="must not be empty"):
        score_threshold_sweep([], [], (0.5,))

    with pytest.raises(ValueError, match="thresholds"):
        score_threshold_sweep([True], [0.9], ())


def test_score_threshold_sweep_preserves_unsorted_grid_and_inclusive_ties():
    expected = [True, False, True, False]
    scores = [0.8, 0.8, 0.6, 0.2]
    thresholds = (0.8, 0.3, 0.9)

    sweep = score_threshold_sweep(expected, scores, thresholds)

    assert [result.threshold for result in sweep] == list(thresholds)
    for result in sweep:
        direct = binary_classification_metrics(
            expected,
            [score >= result.threshold for score in scores],
        )
        assert result.metrics == direct


def test_mean_absolute_error():
    assert mean_absolute_error([1.0, 0.5, 0.0], [0.8, 0.2, 0.1]) == pytest.approx(0.2)


def test_span_overlap_metrics_merges_spans():
    metrics = span_overlap_metrics(
        truth=[Span(0, 10), Span(8, 20)],
        predicted=[Span(5, 12), Span(30, 40)],
    )

    assert metrics.truth_chars == 20
    assert metrics.predicted_chars == 17
    assert metrics.overlap_chars == 7
    assert metrics.precision == pytest.approx(7 / 17)
    assert metrics.recall == pytest.approx(7 / 20)


def test_span_from_offset_length_validates_input():
    assert Span.from_offset_length(5, 2) == Span(5, 7)

    with pytest.raises(ValueError):
        Span.from_offset_length(-1, 2)


def test_metrics_reject_mismatched_lengths():
    with pytest.raises(ValueError):
        binary_classification_metrics([True], [])

    with pytest.raises(ValueError):
        mean_absolute_error([1.0], [])
