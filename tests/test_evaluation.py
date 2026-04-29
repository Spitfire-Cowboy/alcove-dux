import pytest

from alcove_dux.evaluation import (
    Span,
    binary_classification_metrics,
    mean_absolute_error,
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
