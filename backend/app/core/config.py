import os
import logging

class Settings:
    def __init__(self):
        # Validate critical secrets and configuration on startup
        
        self.JWT_SECRET_KEY = self._require_env("JWT_SECRET_KEY", "ratan_super_secret_dev_key_do_not_use_in_prod")
        
        # We don't mandate Qdrant/Groq in dev, but if this is production (e.g. Render), they are critical
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        
        if self.ENVIRONMENT == "production":
            self._require_env("QDRANT_API_KEY")
            self._require_env("QDRANT_URL")
            self._require_env("GROQ_API_KEY")
            
            # Database strict validations
            self._require_env("TIDB_HOST")
            self._require_env("TIDB_USER")
            self._require_env("TIDB_PASSWORD")
            
            # Enforce memory limits conceptually (informative)
            logging.info("[Config] Production environment detected. Strict validations enabled.")
            
    def _require_env(self, key: str, default: str = None) -> str:
        val = os.getenv(key)
        if not val and default is None:
            raise ValueError(f"CRITICAL ERROR: Missing required environment variable: {key}")
        return val or default

# Instantiate to validate immediately on import
settings = Settings()
