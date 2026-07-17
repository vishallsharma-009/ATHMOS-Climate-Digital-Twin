"""
Configuration settings for ATHMOS Climate Digital Twin backend.
"""

import os


class Settings:
    APP_NAME: str = "ATHMOS Climate Digital Twin API"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("APP_PORT", 8000))

    # CORS
    ALLOWED_ORIGINS: list = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Placeholder paths (not used yet)
    DATASETS_DIR: str = "../datasets"
    MODELS_DIR: str = "../models"


settings = Settings()
