"""Product management routes."""

from flask import Blueprint, jsonify, request

from src.shared.logger import get_logger

logger = get_logger("routes.products")

products_bp = Blueprint("products", __name__)


@products_bp.route("/")
def list_products():
    """List all products with optional filtering."""
    status_filter = request.args.get("status", "all")
    logger.info("listing_products", status=status_filter)
    return jsonify({"products": [], "filter": status_filter})


@products_bp.route("/<int:product_id>")
def get_product(product_id: int):
    """Get details of a specific product."""
    logger.info("getting_product", id=product_id)
    return jsonify({"id": product_id, "status": "not_found"})


@products_bp.route("/<int:product_id>/publish", methods=["POST"])
def publish_product(product_id: int):
    """Mark a product as ready for publishing."""
    platforms = request.json.get("platforms", []) if request.is_json else []
    logger.info("publishing_product", id=product_id, platforms=platforms)
    return jsonify({"id": product_id, "status": "published", "platforms": platforms})
