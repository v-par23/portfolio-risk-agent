import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import memory.store as store


@pytest.fixture
def isolated_db(tmp_path, monkeypatch):
    """Points memory.store at a throwaway SQLite file so tests never touch the real memory.db."""
    monkeypatch.setattr(store, "DB_PATH", str(tmp_path / "test_memory.db"))
    return store
