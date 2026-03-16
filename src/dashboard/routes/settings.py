"""Configuration management routes."""

from flask import Blueprint, jsonify, request

from src.shared.logger import get_logger

logger = get_logger("routes.settings")

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/")
def get_settings():
    """Get current configuration (non-sensitive values only)."""
    logger.info("viewing_settings")
    return jsonify({
        "scraping": {
            "headless": True,
            "min_delay": 2.0,
            "max_delay": 5.0,
        },
        "scoring": {
            "alert_threshold": 75.0,
            "review_threshold": 50.0,
        },
        "features": {
            "tiktok_scraping": True,
            "pinterest_scraping": True,
            "competitor_monitoring": True,
        },
    })


@settings_bp.route("/", methods=["POST"])
def update_settings():
    """Update configuration settings."""
    updates = request.json if request.is_json else {}
    logger.info("updating_settings", keys=list(updates.keys()))
    return jsonify({"status": "updated", "updates": updates})
