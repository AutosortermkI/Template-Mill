"""Performance analytics dashboard routes."""

from flask import Blueprint, jsonify, request

from src.shared.logger import get_logger

logger = get_logger("routes.analytics")

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/")
def dashboard():
    """Main analytics dashboard overview."""
    logger.info("viewing_analytics_dashboard")
    return jsonify({
        "total_revenue": 0.0,
        "total_sales": 0,
        "active_listings": 0,
        "top_products": [],
    })


@analytics_bp.route("/product/<int:product_id>")
def product_analytics(product_id: int):
    """Analytics for a specific product across all platforms."""
    logger.info("viewing_product_analytics", product_id=product_id)
    return jsonify({"product_id": product_id, "stats": {}})


@analytics_bp.route("/digest")
def latest_digest():
    """Get the most recent weekly digest."""
    logger.info("viewing_latest_digest")
    return jsonify({"digest": None, "message": "No digest generated yet"})
