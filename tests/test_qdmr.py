"""Tests for the qDMR / dmrconf YAML writer."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from codeplug_csv.models import AnytoneChannel, AnytoneZone, TalkGroup
from codeplug_csv.qdmr import (
    ANALOG_KEY,
    DIGITAL_KEY,
    GROUP_LIST_ID,
    RADIO_ID_ID,
    build_codeplug,
    write_qdmr,
)


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def analog_channel() -> AnytoneChannel:
    return AnytoneChannel(
        name="GB3CD-L 2m FM",
        rx_freq="145.68750",
        tx_freq="145.08750",
        channel_type="A-Analog",
        bandwidth="12.5K",
        ctcss_encode="118.8",
        ctcss_decode="118.8",
        power="High",
        band="2m",
        mode="ANL",
        region="NE",
        rpt_type="RPT",
    )


@pytest.fixture
def digital_channel() -> AnytoneChannel:
    return AnytoneChannel(
        name="GB7AA 70cm TS2",
        rx_freq="439.45000",
        tx_freq="430.85000",
        channel_type="D-Digital",
        bandwidth="12.5K",
        power="Mid",
        color_code=3,
        slot=2,
        contact="Local",
        band="70cm",
        mode="DMR",
        region="LONDON",
        rpt_type="RPT",
    )


@pytest.fixture
def simplex_channel() -> AnytoneChannel:
    """A static PMR446 style channel: receive only, no repeater type."""
    return AnytoneChannel(
        name="PMR 1",
        rx_freq="446.00625",
        tx_freq="446.00625",
        channel_type="A-Analog",
        bandwidth="12.5K",
        power="Low",
        tx_prohibit="On",
    )


@pytest.fixture
def channels(analog_channel, digital_channel, simplex_channel):
    return [analog_channel, digital_channel, simplex_channel]


@pytest.fixture
def zones(channels) -> list[AnytoneZone]:
    return [
        AnytoneZone(name="NE 2m FM", channels=[channels[0]]),
        AnytoneZone(name="LONDON 70cm DMR", channels=[channels[1]]),
        AnytoneZone(name="PMR446", channels=[channels[2]]),
    ]


@pytest.fixture
def talkgroups() -> list[TalkGroup]:
    return [
        TalkGroup(name="Local", radio_id=9),
        TalkGroup(name="UK Wide", radio_id=235),
        TalkGroup(name="BM Parrot", radio_id=9990, call_type="Private Call"),
    ]


def _body(codeplug: dict, name: str) -> dict:
    """Return the type-specific body of the channel called *name*."""
    for entry in codeplug["channels"]:
        body = next(iter(entry.values()))
        if body["name"] == name:
            return body
    raise AssertionError(f"channel {name!r} not found")


def _key(codeplug: dict, name: str) -> str:
    for entry in codeplug["channels"]:
        body = next(iter(entry.values()))
        if body["name"] == name:
            return next(iter(entry))
    raise AssertionError(f"channel {name!r} not found")


class TestBuildCodeplug:
    def test_top_level_keys(self, channels, zones, talkgroups):
        codeplug = build_codeplug(channels, zones, talkgroups)
        assert list(codeplug) == [
            "version",
            "settings",
            "radioIDs",
            "contacts",
            "groupLists",
            "channels",
            "zones",
        ]
        assert codeplug["version"] == "0.9.0"

    def test_radio_id_and_default(self, channels, zones, talkgroups):
        codeplug = build_codeplug(
            channels, zones, talkgroups, dmr_id=2345678, callsign="m0abc"
        )
        radio = codeplug["radioIDs"][0]["dmr"]
        assert radio == {
            "id": RADIO_ID_ID,
            "name": "M0ABC",
            "number": 2345678,
        }
        assert codeplug["settings"] == {"defaultID": RADIO_ID_ID}

    def test_placeholder_identity_is_valid_yaml(self, channels, zones, talkgroups):
        codeplug = build_codeplug(channels, zones, talkgroups)
        radio = codeplug["radioIDs"][0]["dmr"]
        assert radio["number"] == 0
        assert radio["name"] == "NOCALL"

    def test_long_callsign_is_truncated(self, channels, zones, talkgroups):
        codeplug = build_codeplug(
            channels, zones, talkgroups, dmr_id=1, callsign="GB2RSABCDEFG"
        )
        assert codeplug["radioIDs"][0]["dmr"]["name"] == "GB2RSABC"

    def test_digital_channel_fields(self, channels, zones, talkgroups):
        codeplug = build_codeplug(channels, zones, talkgroups)
        assert _key(codeplug, "GB7AA 70cm TS2") == DIGITAL_KEY
        body = _body(codeplug, "GB7AA 70cm TS2")
        assert body["rxFrequency"] == 439.45
        assert body["txFrequency"] == 430.85
        assert body["colorCode"] == 3
        assert body["timeSlot"] == "TS2"
        assert body["contact"] == "tg9"
        assert body["groupList"] == GROUP_LIST_ID
        assert body["power"] == "Mid"
        # Repeaters admit on colour code
        assert body["admit"] == "ColorCode"
        assert "rxOnly" not in body
        assert "bandwidth" not in body

    def test_analog_channel_fields(self, channels, zones, talkgroups):
        codeplug = build_codeplug(channels, zones, talkgroups)
        assert _key(codeplug, "GB3CD-L 2m FM") == ANALOG_KEY
        body = _body(codeplug, "GB3CD-L 2m FM")
        assert body["bandwidth"] == "Narrow"
        assert body["rxTone"] == {"ctcss": 118.8}
        assert body["txTone"] == {"ctcss": 118.8}
        assert body["admit"] == "Always"
        assert "colorCode" not in body
        assert "contact" not in body

    def test_receive_only_channel(self, channels, zones, talkgroups):
        codeplug = build_codeplug(channels, zones, talkgroups)
        assert _body(codeplug, "PMR 1")["rxOnly"] is True

    def test_simplex_digital_channel_admits_always(
        self, zones, talkgroups
    ):
        simplex_dmr = AnytoneChannel(
            name="DH1 439.4000",
            rx_freq="439.40000",
            tx_freq="439.40000",
            channel_type="D-Digital",
            color_code=1,
            slot=1,
            contact="Local",
            power="High",
        )
        codeplug = build_codeplug(
            [simplex_dmr],
            [AnytoneZone(name="DH SIMPLEX", channels=[simplex_dmr])],
            talkgroups,
        )
        assert _body(codeplug, "DH1 439.4000")["admit"] == "Always"

    def test_talkgroup_9_is_always_defined(self, channels, zones):
        codeplug = build_codeplug(channels, zones, [])
        numbers = {c["dmr"]["number"] for c in codeplug["contacts"]}
        assert 9 in numbers

    def test_contacts_deduplicated(self, channels, zones):
        talkgroups = [
            TalkGroup(name="Local", radio_id=9),
            TalkGroup(name="Duplicate", radio_id=9),
        ]
        codeplug = build_codeplug(channels, zones, talkgroups)
        numbers = [c["dmr"]["number"] for c in codeplug["contacts"]]
        assert numbers.count(9) == 1

    def test_private_calls_excluded_from_group_list(self, channels, zones, talkgroups):
        codeplug = build_codeplug(channels, zones, talkgroups)
        members = codeplug["groupLists"][0]["contacts"]
        assert "tg9990" not in members
        assert "tg9" in members

    def test_private_call_contact_type(self, channels, zones, talkgroups):
        codeplug = build_codeplug(channels, zones, talkgroups)
        parrots = [c for c in codeplug["contacts"] if c["dmr"]["number"] == 9990]
        assert parrots[0]["dmr"]["type"] == "PrivateCall"

    def test_zones_reference_channel_ids(self, channels, zones, talkgroups):
        codeplug = build_codeplug(channels, zones, talkgroups)
        ids = [next(iter(e.values()))["id"] for e in codeplug["channels"]]
        members = [m for z in codeplug["zones"] for m in z["A"]]
        assert sorted(members) == sorted(ids)
        assert codeplug["zones"][0] == {
            "id": "z1",
            "name": "NE 2m FM",
            "A": ["ch1"],
        }

    def test_duplicate_channel_names_rejected(
        self, analog_channel, zones, talkgroups
    ):
        twin = AnytoneChannel(**{**analog_channel.__dict__})
        with pytest.raises(ValueError, match="Duplicate channel names"):
            build_codeplug(
                [analog_channel, twin], zones, talkgroups
            )

    def test_missing_zone_membership_rejected(
        self, channels, analog_channel, talkgroups
    ):
        with pytest.raises(ValueError, match="exactly one zone"):
            build_codeplug(
                channels,
                [AnytoneZone(name="NE 2m FM", channels=[analog_channel])],
                talkgroups,
            )

    def test_channel_outside_zone_rejected(self, channels, zones, talkgroups):
        orphan = AnytoneChannel(
            name="ORPHAN",
            rx_freq="145.50000",
            tx_freq="145.50000",
            channel_type="A-Analog",
        )
        with pytest.raises(ValueError, match="exactly one zone"):
            build_codeplug(channels + [orphan], zones, talkgroups)


class TestWriteQdmr:
    def test_creates_file(self, channels, zones, talkgroups, output_dir):
        path = write_qdmr(channels, zones, talkgroups, output_dir)
        assert path.exists()
        assert path.name == "codeplug.yaml"

    def test_output_is_valid_yaml(self, channels, zones, talkgroups, output_dir):
        path = write_qdmr(channels, zones, talkgroups, output_dir)
        with open(path, encoding="utf-8") as f:
            codeplug = yaml.safe_load(f)
        assert codeplug["version"] == "0.9.0"
        assert len(codeplug["channels"]) == len(channels)
        assert len(codeplug["zones"]) == len(zones)

    def test_placeholder_note_only_without_dmr_id(
        self, channels, zones, talkgroups, output_dir
    ):
        placeholder = write_qdmr(channels, zones, talkgroups, output_dir)
        assert "placeholder radio identity" in placeholder.read_text()

        configured = write_qdmr(
            channels, zones, talkgroups, output_dir, dmr_id=2345678, callsign="M0ABC"
        )
        assert "placeholder radio identity" not in configured.read_text()

    def test_names_fit_radio_limits(self, channels, zones, talkgroups, output_dir):
        path = write_qdmr(channels, zones, talkgroups, output_dir)
        with open(path, encoding="utf-8") as f:
            codeplug = yaml.safe_load(f)
        for entry in codeplug["channels"]:
            body = next(iter(entry.values()))
            assert len(body["name"]) <= 16
            if "colorCode" in body:
                assert 0 <= body["colorCode"] <= 15
        for zone in codeplug["zones"]:
            assert len(zone["name"]) <= 16
        for contact in codeplug["contacts"]:
            assert len(contact["dmr"]["name"]) <= 16
