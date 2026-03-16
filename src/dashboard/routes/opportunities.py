"""Opportunity management routes — view, filter, approve/reject opportunities."""

from flask import Blueprint, jsonify, request

from src.shared.logger import get_logger

logger = get_logger("routes.opportunities")

opportunities_bp = Blueprint("opportunities", __name__)


@opportunities_bp.route("/")
def list_opportunities():
    """List all opportunities with optional filtering."""
    status_filter = request.args.get("status", "all")
    min_score = request.args.get("min_score", 0, type=float)
    sort_by = request.args.get("sort", "opportunity_score")

    logger.info("listing_opportunities", status=status_filter, min_score=min_score)

    # Placeholder — will query database
    return jsonify({
        "opportunities": [],
        "filters": {"status": status_filter, "min_score": min_score, "sort": sort_by},
    })


@opportunities_bp.route("/<int:opp_id>")
def get_opportunity(opp_id: int):
    """Get details of a specific opportunity."""
    logger.info("getting_opportunity", id=opp_id)
    return jsonify({"id": opp_id, "status": "not_found"})


@opportunities_bp.route("/<int:opp_id>/approve", methods=["POST"])
def approve_opportunity(opp_id: int):
    """Approve an opportunity for product creation."""
    logger.info("approving_opportunity", id=opp_id)
    return jsonify({"id": opp_id, "status": "approved"})


@opportunities_bp.route("/<int:opp_id>/reject", methods=["POST"])
def reject_opportunity(opp_id: int):
    """Reject an opportunity."""
    notes = request.json.get("notes", "") if request.is_json else ""
    logger.info("rejecting_opportunity", id=opp_id, notes=notes)
    return jsonify({"id": opp_id, "status": "rejected"})
