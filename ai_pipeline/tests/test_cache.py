import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cache


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Each test gets its own SQLite file in a temp dir."""
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test_analyses.db"))


def test_miss_returns_none():
    assert cache.get_cached("nonexistent_hash") is None


def test_store_and_retrieve():
    data = {"tldr": "Test", "clauses": []}
    cache.store_result("abc123", "example.com", data)
    retrieved = cache.get_cached("abc123")
    assert retrieved == data


def test_duplicate_store_does_not_overwrite():
    data1 = {"tldr": "First", "clauses": []}
    data2 = {"tldr": "Second", "clauses": []}
    cache.store_result("dup_hash", "example.com", data1)
    cache.store_result("dup_hash", "example.com", data2)
    retrieved = cache.get_cached("dup_hash")
    assert retrieved["tldr"] == "First"


def test_compute_hash_is_deterministic():
    h1 = cache.compute_hash("hello world")
    h2 = cache.compute_hash("hello world")
    assert h1 == h2


def test_different_texts_produce_different_hashes():
    h1 = cache.compute_hash("text A")
    h2 = cache.compute_hash("text B")
    assert h1 != h2
