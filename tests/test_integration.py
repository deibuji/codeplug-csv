"""End-to-end integration tests: main() with mocked HTTP."""

from __future__ import annotations

import csv
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import yaml

from codeplug_csv.cli import main
from codeplug_csv.config import CHANNEL_COLUMNS, TALKGROUP_COLUMNS, ZONE_COLUMNS
from codeplug_csv.simplex import get_static_zones


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_USER_CSV = b"RADIO_ID,CALLSIGN,FIRST_NAME,LAST_NAME\n2340001,M0TST,Test,User\n"


def _make_httpx_mock(
    per_band: dict[str, list[dict]],
    bm_data: dict,
    user_csv: bytes = SAMPLE_USER_CSV,
    rsgb_error: Exception | None = None,
    talkgroup_error: Exception | None = None,
    stream_error: Exception | None = None,
):
    """Return a mock that satisfies httpx.AsyncClient for all three clients:
    1. RSGBClient: async with ... as client: await client.get(url)
    2. BrandMeisterClient: async with ... as client: await client.get(url)
    3. RadioIDClient: async with ... as client: client.stream(...)

    The optional error arguments make exactly one data source fail.
    """

    # Use a custom mock for get to handle both sync and async scenarios correctly
    def _get_mock(url: str, **_kwargs):
        if "/talkgroup/" in url:
            if talkgroup_error is not None:
                raise talkgroup_error
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            resp.json = MagicMock(return_value=bm_data)
            return resp
        for band, items in per_band.items():
            if f"/band/{band}" in url:
                if rsgb_error is not None:
                    raise rsgb_error
                resp = MagicMock()
                resp.raise_for_status = MagicMock()
                resp.json = MagicMock(return_value={"data": items})
                return resp
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json = MagicMock(return_value={"data": []})
        return resp

    # Fix for the RadioIDClient: stream context manager
    mock_dl_response = MagicMock()
    mock_dl_response.raise_for_status = MagicMock()

    async def _aiter_bytes():
        yield user_csv
        if stream_error is not None:
            raise stream_error

    mock_dl_response.aiter_bytes = MagicMock(return_value=_aiter_bytes())

    mock_stream_cm = AsyncMock()
    mock_stream_cm.__aenter__.return_value = mock_dl_response
    mock_stream_cm.__aexit__ = AsyncMock(return_value=None)

    # The client should be an AsyncMock but we must ensure its methods
    # behave as the real httpx.AsyncClient does.
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=_get_mock)
    mock_client.aclose = AsyncMock()
    mock_client.stream = MagicMock(return_value=mock_stream_cm)
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__ = AsyncMock(return_value=None)

    return mock_client


@contextmanager
def mocked_http(
    per_band: dict[str, list[dict]],
    bm_data: dict,
    user_csv: bytes = SAMPLE_USER_CSV,
    **failures: Exception,
):
    httpx_mock = _make_httpx_mock(per_band, bm_data, user_csv, **failures)
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
        qdmr_yaml = tmp_path / "codeplug.yaml"

        assert channel_csv.exists()
        assert zone_csv.exists()
        assert tg_csv.exists()
        assert user_csv.exists()
        assert user_csv.read_bytes() == SAMPLE_USER_CSV
        assert qdmr_yaml.exists()

    def test_qdmr_codeplug_structure(
        self, tmp_path, per_band_api_data, sample_bm_data
    ):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "-q", "--dmr-id", "2345678",
                  "--callsign", "M0ABC"])

        with open(tmp_path / "codeplug.yaml", encoding="utf-8") as f:
            codeplug = yaml.safe_load(f)

        assert codeplug["radioIDs"][0]["dmr"]["number"] == 2345678
        assert codeplug["radioIDs"][0]["dmr"]["name"] == "M0ABC"

        # Every Anytone channel has exactly one qDMR channel with the same name
        with open(tmp_path / "Channel.CSV") as f:
            csv_names = [r["Channel Name"] for r in csv.DictReader(f)]
        yaml_names = [
            next(iter(entry.values()))["name"] for entry in codeplug["channels"]
        ]
        assert yaml_names == csv_names

        # Zone membership stays total and disjoint, as with Zone.CSV
        ids = [next(iter(e.values()))["id"] for e in codeplug["channels"]]
        members = [m for zone in codeplug["zones"] for m in zone["A"]]
        assert sorted(members) == sorted(ids)

        # Every reference resolves
        contact_ids = {c["dmr"]["id"] for c in codeplug["contacts"]}
        group_ids = {g["id"] for g in codeplug["groupLists"]}
        for entry in codeplug["channels"]:
            body = next(iter(entry.values()))
            assert body.get("contact") is None or body["contact"] in contact_ids
            assert (
                body.get("groupList") is None
                or body["groupList"] in group_ids
            )

    def test_format_anytone_omits_qdmr(
        self, tmp_path, per_band_api_data, sample_bm_data
    ):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "-q", "--format", "anytone"])

        assert (tmp_path / "Channel.CSV").exists()
        assert not (tmp_path / "codeplug.yaml").exists()

    def test_format_qdmr_omits_anytone_csvs(
        self, tmp_path, per_band_api_data, sample_bm_data
    ):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "-q", "--format", "qdmr"])

        assert (tmp_path / "codeplug.yaml").exists()
        assert not (tmp_path / "Channel.CSV").exists()
        assert not (tmp_path / "Zone.CSV").exists()

    def test_channel_csv_structure(self, tmp_path, per_band_api_data, sample_bm_data):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "-q"])

        with open(tmp_path / "Channel.CSV") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert reader.fieldnames == CHANNEL_COLUMNS

        assert len(rows) > 0

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

        # Every static simplex zone must appear
        static_names = {z.name for z in get_static_zones()}
        assert zone_names >= static_names, f"Missing static zones in {zone_names}"

        # The fixture has a LONDON UHF DV repeater (GB7AA)
        assert "LONDON UHF DV" in zone_names
        gb7aa_zones = [r for r in rows if "GB7AA" in r["Zone Channel Member"]]
        assert gb7aa_zones, "No zone contains GB7AA"

    def test_zone_names_are_unique(
        self, tmp_path, per_band_api_data, sample_bm_data
    ):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "-q"])

        with open(tmp_path / "Zone.CSV") as f:
            rows = list(csv.DictReader(f))

        names = [r["Zone Name"] for r in rows]
        assert len(names) == len(set(names))

    def test_channel_names_are_unique(
        self, tmp_path, per_band_api_data, sample_bm_data
    ):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "-q"])

        with open(tmp_path / "Channel.CSV") as f:
            rows = list(csv.DictReader(f))

        names = [r["Channel Name"] for r in rows]
        assert len(names) == len(set(names))

    def test_zone_membership_is_total_and_disjoint(
        self, tmp_path, per_band_api_data, sample_bm_data
    ):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "-q"])

        with open(tmp_path / "Channel.CSV") as f:
            channel_names = [r["Channel Name"] for r in csv.DictReader(f)]
        with open(tmp_path / "Zone.CSV") as f:
            zone_rows = list(csv.DictReader(f))

        members = [
            member
            for row in zone_rows
            for member in row["Zone Channel Member"].split("|")
        ]
        known = set(channel_names)

        assert sorted(members) == sorted(channel_names)
        for row in zone_rows:
            row_members = row["Zone Channel Member"].split("|")
            assert len(row_members) == len(set(row_members)), row["Zone Name"]
            assert all(member in known for member in row_members), row["Zone Name"]
            assert row["A Channel"] in known, row["Zone Name"]
            assert row["B Channel"] in known, row["Zone Name"]

    def test_dynamic_zones_do_not_mix_bands(
        self, tmp_path, per_band_api_data, sample_bm_data
    ):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "-q"])

        with open(tmp_path / "Channel.CSV") as f:
            band_by_name = {
                row["Channel Name"]: (
                    "2m" if float(row["Receive Frequency"]) < 200 else "70cm"
                )
                for row in csv.DictReader(f)
            }
        with open(tmp_path / "Zone.CSV") as f:
            zone_rows = list(csv.DictReader(f))

        static_names = {z.name for z in get_static_zones()}
        for row in zone_rows:
            if row["Zone Name"] in static_names:
                continue
            member_bands = {
                band_by_name[member]
                for member in row["Zone Channel Member"].split("|")
            }
            assert len(member_bands) == 1, (
                f"{row['Zone Name']} mixes {member_bands}"
            )

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
        # A run that produces no channels must not leave a contact list behind.
        assert not (tmp_path / "user.csv").exists()

    def test_exits_one_on_rsgb_failure(
        self, tmp_path, per_band_api_data, sample_bm_data, caplog
    ):
        error = httpx.ConnectError("network down")
        with mocked_http(per_band_api_data, sample_bm_data, rsgb_error=error):
            with pytest.raises(SystemExit) as exc_info:
                main(["-o", str(tmp_path), "-q"])
        assert exc_info.value.code == 1
        assert "Failed to fetch repeater data: network down" in caplog.text
        # The optional contact download must not outlive the failed run.
        assert not (tmp_path / "user.csv").exists()
        assert not list(tmp_path.glob("*.part"))

    def test_exits_one_on_brandmeister_failure(
        self, tmp_path, per_band_api_data, sample_bm_data, caplog
    ):
        error = httpx.ConnectError("brandmeister down")
        with mocked_http(per_band_api_data, sample_bm_data, talkgroup_error=error):
            with pytest.raises(SystemExit) as exc_info:
                main(["-o", str(tmp_path), "-q"])
        assert exc_info.value.code == 1
        assert "Failed to fetch talkgroup data: brandmeister down" in caplog.text
        assert not (tmp_path / "user.csv").exists()

    def test_quiet_suppresses_stdout(
        self, tmp_path, per_band_api_data, sample_bm_data, capsys
    ):
        with mocked_http(per_band_api_data, sample_bm_data):
            main(["-o", str(tmp_path), "-q"])

        assert (tmp_path / "Channel.CSV").exists()
        assert capsys.readouterr().out == ""

    def test_download_failure_continues_without_contacts(
        self, tmp_path, per_band_api_data, sample_bm_data, caplog
    ):
        error = httpx.ReadError("connection lost")
        with mocked_http(per_band_api_data, sample_bm_data, stream_error=error):
            main(["-o", str(tmp_path), "-q"])

        for name in ("Channel.CSV", "Zone.CSV", "TalkGroups.CSV"):
            assert (tmp_path / name).exists(), name
        # A partly downloaded contact list must never be promoted to user.csv.
        assert not (tmp_path / "user.csv").exists()
        assert "Failed to download RadioID contacts: connection lost" in caplog.text
