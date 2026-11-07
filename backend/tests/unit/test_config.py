import os
from unittest.mock import patch

from app.core.config import Settings


def test_default_settings():
    with patch.dict(os.environ, {}, clear=True):
        settings = Settings(_env_file=None)
    assert settings.app_name == "Semantic Search API"
    assert settings.app_version == "2.0.0"
    assert settings.embedding_dimension == 384
    assert settings.chunk_size == 250
    assert settings.chunk_overlap == 50
    assert settings.collection_name == "nco_roles"
    assert len(settings.cors_origins) > 0


def test_custom_settings():
    settings = Settings(
        _env_file=None,
        app_name="Custom Name",
        app_version="3.0.0",
        debug=True,
        sqlite_db_path="custom.db",
        embedding_dimension=512,
    )
    assert settings.app_name == "Custom Name"
    assert settings.app_version == "3.0.0"
    assert settings.debug is True
    assert settings.sqlite_db_path == "custom.db"
    assert settings.embedding_dimension == 512
