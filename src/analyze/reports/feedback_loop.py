"""Feed performance data back into the discover module for scoring calibration."""

from src.analyze.models import FeedbackSignal
from src.shared.logger import get_logger

logger = get_logger("feedback_loop")


def compute_prediction_accuracy(
    predicted_scores: list[dict],
    actual_performance: list[dict],
) -> list[FeedbackSignal]:
    """Compare predicted opportunity scores vs actual sales performance.

    Args:
        predicted_scores: List of dicts with keyword_id, predicted_score, and component scores.
        actual_performance: List of dicts with keyword_id and normalized sales metrics.

    Returns:
        List of FeedbackSignal objects with accuracy assessments.
    """
    logger.info(
        "computing_prediction_accuracy",
        predicted_count=len(predicted_scores),
        actual_count=len(actual_performance),
    )

    actual_by_keyword = {a["keyword_id"]: a for a in actual_performance}
    signals: list[FeedbackSignal] = []

    for pred in predicted_scores:
        keyword_id = pred["keyword_id"]
        actual = actual_by_keyword.get(keyword_id)

        if not actual:
            continue

        predicted = pred["predicted_score"]
        actual_perf = actual.get("normalized_sales", 0.0)

        # Accuracy: 1.0 = perfect, 0.0 = completely wrong
        if predicted > 0:
            accuracy = 1.0 - min(abs(predicted - actual_perf) / predicted, 1.0)
        else:
            accuracy = 0.0

        # Determine which component needs adjustment
        adjustment = ""
        if accuracy < 0.5:
            if actual_perf > predicted:
                adjustment = "score_too_low"
            else:
                adjustment = "score_too_high"

        signal = FeedbackSignal(
            keyword_id=keyword_id,
            predicted_score=predicted,
            actual_performance=actual_perf,
            accuracy=round(accuracy, 3),
            adjustment_needed=adjustment,
        )
        signals.append(signal)

    # Log summary
    if signals:
        avg_accuracy = sum(s.accuracy for s in signals) / len(signals)
        false_positives = sum(1 for s in signals if s.adjustment_needed == "score_too_high")
        false_negatives = sum(1 for s in signals if s.adjustment_needed == "score_too_low")

        logger.info(
            "prediction_accuracy_computed",
            avg_accuracy=round(avg_accuracy, 3),
            false_positives=false_positives,
            false_negatives=false_negatives,
            total_signals=len(signals),
        )

    return signals
