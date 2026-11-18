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


def test_fit_name_preserves_suffix():
    assert config.fit_name("GB3CD-L 2m", " FM") == "GB3CD-L 2m FM"


def test_fit_name_truncates_text_not_suffix():
    name = config.fit_name("GB3ABCDEFGHIJ-L 70cm", " TS1")
    assert len(name) == config.MAX_NAME_LENGTH
    assert name.endswith(" TS1")


def test_mode_and_gateway_labels_cover_internal_modes():
    assert set(config.MODE_LABELS) == {"ANL", "DMR"}
    assert set(config.GATEWAY_LABELS) == {"ANL", "DMR"}


def test_repeater_modes_use_radio_spelling():
    """Digital repeaters are labelled DV, the spelling the radio shows."""
    assert config.MODE_LABELS["ANL"] == "FM"
    assert config.MODE_LABELS["DMR"] == "DV"


def test_gateway_labels_keep_analog_digital_prefix():
    """AG/DG still encode analog vs digital, which FM/DV does not."""
    assert config.GATEWAY_LABELS["ANL"] == "AG"
    assert config.GATEWAY_LABELS["DMR"] == "DG"


@pytest.mark.parametrize(
    ("band", "expected"),
    [
        ("2m", "VHF"),
        ("2M", "VHF"),
        ("70cm", "UHF"),
        ("70CM", "UHF"),
        ("70 cm", "UHF"),
    ],
)
def test_band_label_maps_api_bands(band, expected):
    assert config.band_label(band) == expected


def test_band_label_falls_back_for_unknown_band():
    """A new API band must still produce a usable label."""
    assert config.band_label("23cm") == "23CM"


def test_band_rank_orders_ascending_frequency():
    """VHF sorts before UHF so the radio's zone order stays stable."""
    assert config.band_rank("2m") < config.band_rank("70cm")
    assert config.band_rank("70cm") < config.band_rank("23cm")


def test_api_band_ids_are_unchanged():
    """Zone/channel labels changed; the RSGB endpoint path did not."""
    assert config.BANDS == ("2m", "70cm")
