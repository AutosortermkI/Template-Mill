"""Tests for build module models."""

from src.build.models import MockupConfig, Product, TemplateSpec


def test_product_defaults() -> None:
    """Product should default to draft status."""
    product = Product(name="Test Template", format="notion")
    assert product.status == "draft"
    assert product.price == 0.0
    assert product.mockup_blob_paths == []


def test_template_spec_creation() -> None:
    """TemplateSpec should accept all fields."""
    spec = TemplateSpec(
        template_name="Student Planner",
        tagline="Plan your semester with ease",
        databases=[{"name": "Tasks", "properties": []}],
    )
    assert spec.template_name == "Student Planner"
    assert len(spec.databases) == 1


def test_mockup_config_defaults() -> None:
    """MockupConfig should have sensible defaults."""
    config = MockupConfig()
    assert config.device_frame == "laptop"
    assert config.aspect_ratio == "square"
    assert config.background_color == "#FFFFFF"
