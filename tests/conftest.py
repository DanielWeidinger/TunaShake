import os
import pytest


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Point every test at a fresh temporary database."""
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("TUNASHAKE_DB", str(db_file))
    yield db_file
