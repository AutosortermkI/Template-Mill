"""Tests for the feedback loop prediction accuracy."""

from src.analyze.reports.feedback_loop import compute_prediction_accuracy


def test_perfect_prediction_gives_high_accuracy() -> None:
    """When predicted score matches actual, accuracy should be high."""
    predictions = [{"keyword_id": 1, "predicted_score": 75.0}]
    actuals = [{"keyword_id": 1, "normalized_sales": 75.0}]

    signals = compute_prediction_accuracy(predictions, actuals)
    assert len(signals) == 1
    assert signals[0].accuracy == 1.0
    assert signals[0].adjustment_needed == ""


def test_overestimation_flagged() -> None:
    """When predicted score is much higher than actual, it should flag score_too_high."""
    predictions = [{"keyword_id": 1, "predicted_score": 80.0}]
    actuals = [{"keyword_id": 1, "normalized_sales": 20.0}]

    signals = compute_prediction_accuracy(predictions, actuals)
    assert len(signals) == 1
    assert signals[0].accuracy < 0.5
    assert signals[0].adjustment_needed == "score_too_high"


def test_underestimation_flagged() -> None:
    """When actual performance far exceeds prediction, flag score_too_low."""
    predictions = [{"keyword_id": 1, "predicted_score": 20.0}]
    actuals = [{"keyword_id": 1, "normalized_sales": 80.0}]

    signals = compute_prediction_accuracy(predictions, actuals)
    assert len(signals) == 1
    assert signals[0].adjustment_needed == "score_too_low"


def test_missing_actuals_skipped() -> None:
    """Keywords without actual data should be skipped."""
    predictions = [
        {"keyword_id": 1, "predicted_score": 50.0},
        {"keyword_id": 2, "predicted_score": 60.0},
    ]
    actuals = [{"keyword_id": 1, "normalized_sales": 50.0}]

    signals = compute_prediction_accuracy(predictions, actuals)
    assert len(signals) == 1
    assert signals[0].keyword_id == 1
