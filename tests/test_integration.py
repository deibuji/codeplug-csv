"""End-to-end integration tests: main() with mocked HTTP."""

from __future__ import annotations

import csv
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from codeplug_csv.cli import main
from codeplug_csv.config import CHANNEL_COLUMNS, TALKGROUP_COLUMNS, ZONE_COLUMNS
from codeplug_csv.simplex import get_static_zones


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_USER_CSV = b"RADIO_ID,CALLSIGN,FIRST_NAME,LAST_NAME\n2340001,M0TST,Test,User\n"


def _make_httpx_mock(
    per_band: dict[str, list[dict]], bm_data: dict, user_csv: bytes = SAMPLE_USER_CSV
):
    """Return a mock that satisfies httpx.AsyncClient for all three clients:
    1. RSGBClient: async with ... as client: await client.get(url)
    2. BrandMeisterClient: async with ... as client: await client.get(url)
    3. RadioIDClient: async with ... as client: client.stream(...)
    """

    async def _get(url: str, **_kwargs):
        if "/talkgroup/" in url:
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            resp.json = MagicMock(return_value=bm_data)
            return resp
        for band, items in per_band.items():
            if f"/band/{band}" in url:
                resp = MagicMock()
                resp.raise_for_status = MagicMock()
                resp.json = MagicMock(return_value={"data": items})
                return resp
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(return_value={"data": []})
        return resp

    # --- RadioIDClient: stream context manager ---
    mock_dl_response = MagicMock()
    mock_dl_response.raise_for_status = MagicMock()

    async def _aiter_bytes():
        yield user_csv

    mock_dl_response.aiter_bytes = MagicMock(return_value=_aiter_bytes())

    mock_stream_cm = AsyncMock()
    mock_stream_cm.__aenter__.return_value = mock_dl_response

    mock_client = AsyncMock()
    mock_client.get = _get
    mock_client.aclose = AsyncMock()
    mock_client.stream = MagicMock(return_value=mock_stream_cm)  # sync in httpx
    mock_client.__aenter__.return_value = mock_client

    return mock_client


@contextmanager
def mocked_http(
    per_band: dict[str, list[dict]], bm_data: dict, user_csv: bytes = SAMPLE_USER_CSV
):
    httpx_mock = _make_httpx_mock(per_band, bm_data, user_csv)
    with patch("codeplug_csv.extract.httpx.AsyncClient", return_value=httpx_mock):
        yield


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def per_band_api_data(sample_api_data):
    """Partition sample API records by band (lowercased), matching CLI arg format."""
    out: dict[str, list[dict]] = {}
    for item in sample_api_data:
        band = item["band"].lower()  # "2M" -> "2m", "70CM" -> "70cm"
        out.setdefault(band, []).append(item)
    return out


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEndToEnd:
    def test_main_generates_all_csvs(self, tmp_path, per_band_api_data, sample_bm_data):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "-q"])

        channel_csv = tmp_path / "Channel.CSV"
        zone_csv = tmp_path / "Zone.CSV"
        tg_csv = tmp_path / "TalkGroups.CSV"
        user_csv = tmp_path / "user.csv"

        assert channel_csv.exists()
        assert zone_csv.exists()
        assert tg_csv.exists()
        assert user_csv.exists()
        assert user_csv.read_bytes() == SAMPLE_USER_CSV

    def test_channel_csv_structure(self, tmp_path, per_band_api_data, sample_bm_data):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "-q"])

        with open(tmp_path / "Channel.CSV") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert reader.fieldnames == CHANNEL_COLUMNS

        assert len(rows) > 0

        callsigns = {r["Channel Name"] for r in rows}
        # GB3CD-L is analog in the fixture
        gb3cd_rows = [r for r in rows if "GB3CD" in r["Channel Name"]]
        assert gb3cd_rows, "GB3CD channels missing"
        assert gb3cd_rows[0]["Channel Type"] == "A-Analog"

        # GB7AA is DMR in the fixture (modeCodes: ["M:1"])
        gb7aa_rows = [r for r in rows if "GB7AA" in r["Channel Name"]]
        assert gb7aa_rows, "GB7AA channels missing"
        assert gb7aa_rows[0]["Channel Type"] == "D-Digital"

        # Frequency swap: fixture tx=439450000, rx=430850000
        # → radio Receive = repeater TX = 439.45000, radio TX = repeater RX = 430.85000
        gb7aa_ts1 = next(r for r in gb7aa_rows if "TS1" in r["Channel Name"])
        assert gb7aa_ts1["Receive Frequency"] == "439.45000"
        assert gb7aa_ts1["Transmit Frequency"] == "430.85000"

        # All frequency fields match MHz format
        import re

        freq_pattern = re.compile(r"^\d{3}\.\d{5}$")
        for row in rows:
            assert freq_pattern.match(row["Receive Frequency"]), row[
                "Receive Frequency"
            ]
            assert freq_pattern.match(row["Transmit Frequency"]), row[
                "Transmit Frequency"
            ]

    def test_zone_csv_structure(self, tmp_path, per_band_api_data, sample_bm_data):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "-q"])

        with open(tmp_path / "Zone.CSV") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert reader.fieldnames == ZONE_COLUMNS

        zone_names = {r["Zone Name"] for r in rows}

        # At least one static simplex zone must appear
        static_names = {z.name for z in get_static_zones()}
        assert zone_names & static_names, f"No static zones found in {zone_names}"

        # At least one dynamic zone containing GB7AA
        gb7aa_zones = [r for r in rows if "GB7AA" in r["Zone Channel Member"]]
        assert gb7aa_zones, "No zone contains GB7AA"

    def test_talkgroups_csv_structure(
        self, tmp_path, per_band_api_data, sample_bm_data
    ):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "-q"])

        with open(tmp_path / "TalkGroups.CSV") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert reader.fieldnames == TALKGROUP_COLUMNS

        assert len(rows) == 34  # matches test_extract.py:26

        ids = [int(r["Radio ID"]) for r in rows]
        assert ids == sorted(ids)

        tg9 = next(r for r in rows if r["Radio ID"] == "9")
        assert tg9["Name"] == "Local"

        tg4000 = next(r for r in rows if r["Radio ID"] == "4000")
        assert tg4000["Call Type"] == "Private Call"

    def test_no_contacts_flag(self, tmp_path, per_band_api_data, sample_bm_data):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "--no-contacts", "-q"])

        assert not (tmp_path / "user.csv").exists()

    def test_locator_filter(self, tmp_path, per_band_api_data, sample_bm_data):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "--locator", "IO91", "-q"])

        with open(tmp_path / "Channel.CSV") as f:
            rows = list(csv.DictReader(f))

        channel_names = {r["Channel Name"] for r in rows}
        # GB7AA is IO91WM — should be included
        assert any("GB7AA" in n for n in channel_names)
        # GB3CD-L is IO94DR — should be excluded
        assert not any("GB3CD" in n for n in channel_names)

    def test_exits_zero_when_no_repeaters_match(
        self, tmp_path, per_band_api_data, sample_bm_data
    ):
        with mocked_http(per_band_api_data, sample_bm_data):
            with pytest.raises(SystemExit) as exc_info:
                main(["-o", str(tmp_path), "--locator", "ZZ99", "-q"])
        assert exc_info.value.code == 0

    def test_exits_one_on_rsgb_failure(self, tmp_path, sample_bm_data):
        import httpx as _httpx

        failing_cm = AsyncMock()
        failing_cm.get = AsyncMock(side_effect=_httpx.ConnectError("network down"))

        with patch("codeplug_csv.extract.httpx.AsyncClient", return_value=failing_cm):
            with pytest.raises(SystemExit) as exc_info:
                main(["-o", str(tmp_path), "-q"])
        assert exc_info.value.code == 1
