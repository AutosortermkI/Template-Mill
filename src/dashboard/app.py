"""Flask app factory for the TemplateMill dashboard."""

from flask import Flask

from src.shared.logger import setup_logging


def create_app() -> Flask:
    """Create and configure the Flask application."""
    setup_logging()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = "dev-secret-change-in-production"

    # Register blueprints
    from src.dashboard.routes.analytics import analytics_bp
    from src.dashboard.routes.opportunities import opportunities_bp
    from src.dashboard.routes.products import products_bp
    from src.dashboard.routes.settings import settings_bp

    app.register_blueprint(opportunities_bp, url_prefix="/opportunities")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(settings_bp, url_prefix="/settings")

    @app.route("/")
    def index():
        return "<h1>TemplateMill Dashboard</h1><p>Pipeline status: OK</p>"

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app
