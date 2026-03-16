"""Custom exception hierarchy for TemplateMill."""


class TemplateMillException(Exception):
    """Base exception for all TemplateMill errors."""


# Scraping exceptions
class ScraperException(TemplateMillException):
    """Base exception for scraper errors."""


class CaptchaDetectedError(ScraperException):
    """Raised when a CAPTCHA is detected during scraping."""


class SelectorChangedError(ScraperException):
    """Raised when expected DOM selectors are not found, indicating site changes."""


class RateLimitError(TemplateMillException):
    """Raised when an API or scraping rate limit is hit."""


# API client exceptions
class APIClientException(TemplateMillException):
    """Base exception for API client errors."""


class EtsyAPIError(APIClientException):
    """Etsy API error."""


class EtsyRateLimitError(EtsyAPIError, RateLimitError):
    """Etsy API rate limit exceeded."""


class EtsyAuthError(EtsyAPIError):
    """Etsy authentication/authorization failure."""


class GumroadAPIError(APIClientException):
    """Gumroad API error."""


class GumroadAuthError(GumroadAPIError):
    """Gumroad authentication failure."""


class ShopifyAPIError(APIClientException):
    """Shopify API error."""


class ShopifyAuthError(ShopifyAPIError):
    """Shopify authentication failure."""


class PinterestAPIError(APIClientException):
    """Pinterest API error."""


# Database exceptions
class DatabaseException(TemplateMillException):
    """Database-related error."""


# LLM exceptions
class LLMException(TemplateMillException):
    """LLM API error."""


class LLMParseError(LLMException):
    """Failed to parse LLM response into expected format."""
