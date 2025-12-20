"""Configuration management for the API."""

import os


def validate_auth0_config() -> None:
    """
    Validate that all required Auth0 configuration is present.

    Raises:
        RuntimeError: If required configuration is missing.
    """
    required_vars = {
        "AUTH0_DOMAIN": os.getenv("AUTH0_DOMAIN", "rehpublic.eu.auth0.com"),
        "AUTH0_AUDIENCE": os.getenv("AUTH0_AUDIENCE", "https://api.rehpublic.com"),
    }

    missing_vars = [key for key, value in required_vars.items() if not value]

    if missing_vars:
        raise RuntimeError(
            f"Missing required Auth0 configuration: {', '.join(missing_vars)}"
        )


# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "rehpublic.eu.auth0.com")
AUTH0_AUDIENCE = os.getenv("AUTH0_AUDIENCE", "https://api.rehpublic.com")
AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "BOpVwQPgi3yAeaFoAUYt8H2Ho8twfAxz")
AUTH0_CLIENT_SECRET = os.getenv(
    "AUTH0_CLIENT_SECRET",
    "T3U598QWgH683ycf79QyUE2f13nz3C_d3bLKc9NNojlRCb1ka3Rbfg89wEVtoo-s",
)
