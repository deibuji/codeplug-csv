"""Tests for environment variable overrides in config."""

from __future__ import annotations

import importlib

import pytest

from codeplug_csv import config


@pytest.fixture(autouse=True)
def _reset_config():
    yield
    importlib.reload(config)


def test_default_api_base_url(monkeypatch):
    monkeypatch.delenv("CODEPLUG_CSV_API_BASE_URL", raising=False)
    importlib.reload(config)
    assert config.API_BASE_URL == "https://api-beta.rsgb.online"


def test_api_base_url_from_env(monkeypatch):
    monkeypatch.setenv("CODEPLUG_CSV_API_BASE_URL", "https://staging.example.com")
    importlib.reload(config)
    assert config.API_BASE_URL == "https://staging.example.com"


def test_brandmeister_url_from_env(monkeypatch):
    monkeypatch.setenv("CODEPLUG_CSV_BRANDMEISTER_URL", "https://bm.example.com/v2")
    importlib.reload(config)
    assert config.BRANDMEISTER_API_URL == "https://bm.example.com/v2"


def test_radioid_url_from_env(monkeypatch):
    monkeypatch.setenv("CODEPLUG_CSV_RADIOID_URL", "https://radioid.example.com/user.csv")
    importlib.reload(config)
    assert config.RADIOID_CSV_URL == "https://radioid.example.com/user.csv"


def test_http_timeout_from_env(monkeypatch):
    monkeypatch.setenv("CODEPLUG_CSV_HTTP_TIMEOUT", "42")
    importlib.reload(config)
    assert config.HTTP_TIMEOUT == 42


def test_http_timeout_invalid_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("CODEPLUG_CSV_HTTP_TIMEOUT", "not-a-number")
    importlib.reload(config)
    assert config.HTTP_TIMEOUT == 30


def test_http_timeout_empty_falls_back_to_default(monkeypatch):
    monkeypatch.setenv("CODEPLUG_CSV_HTTP_TIMEOUT", "")
    importlib.reload(config)
    assert config.HTTP_TIMEOUT == 30


def test_max_concurrent_from_env(monkeypatch):
    monkeypatch.setenv("CODEPLUG_CSV_MAX_CONCURRENT", "10")
    importlib.reload(config)
    assert config.MAX_CONCURRENT == 10


def test_radioid_timeout_default_preserved(monkeypatch):
    monkeypatch.delenv("CODEPLUG_CSV_RADIOID_TIMEOUT", raising=False)
    importlib.reload(config)
    assert config.RADIOID_TIMEOUT == 60


def test_radioid_timeout_from_env(monkeypatch):
    monkeypatch.setenv("CODEPLUG_CSV_RADIOID_TIMEOUT", "120")
    importlib.reload(config)
    assert config.RADIOID_TIMEOUT == 120
