"""Tests for the CSV load module."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from repeater_csv.config import CHANNEL_COLUMNS, TALKGROUP_COLUMNS, ZONE_COLUMNS
from repeater_csv.load import write_channels, write_talkgroups, write_zones
from repeater_csv.models import AnytoneChannel, AnytoneZone


@pytest.fixture
def output_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture
def sample_channels() -> list[AnytoneChannel]:
    return [
        AnytoneChannel(
            name="GB3CD FM",
            rx_freq="145.68750",
            tx_freq="145.08750",
            channel_type="A-Analog",
            bandwidth="12.5K",
            ctcss_encode="118.8",
            ctcss_decode="118.8",
            power="High",
            band="2m",
            mode="ANL",
        ),
        AnytoneChannel(
            name="GB7AA TS1",
            rx_freq="439.45000",
            tx_freq="430.85000",
            channel_type="D-Digital",
            bandwidth="12.5K",
            power="High",
            color_code=1,
            slot=1,
            contact="Local",
            contact_call_type="Group Call",
            band="70cm",
            mode="DMR",
        ),
    ]


class TestWriteChannels:
    def test_creates_file(self, sample_channels, output_dir):
        path = write_channels(sample_channels, output_dir)
        assert path.exists()
        assert path.name == "Channel.CSV"

    def test_has_all_columns(self, sample_channels, output_dir):
        write_channels(sample_channels, output_dir)
        with open(output_dir / "Channel.CSV") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == CHANNEL_COLUMNS

    def test_correct_row_count(self, sample_channels, output_dir):
        write_channels(sample_channels, output_dir)
        with open(output_dir / "Channel.CSV") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 2

    def test_analog_channel_values(self, sample_channels, output_dir):
        write_channels(sample_channels, output_dir)
        with open(output_dir / "Channel.CSV") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        analog = rows[0]
        assert analog["Channel Name"] == "GB3CD FM"
        assert analog["Channel Type"] == "A-Analog"
        assert analog["Receive Frequency"] == "145.68750"
        assert analog["Transmit Frequency"] == "145.08750"
        assert analog["CTCSS/DCS Encode"] == "118.8"
        assert analog["Band Width"] == "12.5K"

    def test_digital_channel_values(self, sample_channels, output_dir):
        write_channels(sample_channels, output_dir)
        with open(output_dir / "Channel.CSV") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        digital = rows[1]
        assert digital["Channel Name"] == "GB7AA TS1"
        assert digital["Channel Type"] == "D-Digital"
        assert digital["Color Code"] == "1"
        assert digital["Contact"] == "Local"

    def test_no_missing_columns(self, sample_channels, output_dir):
        """Every column in CHANNEL_COLUMNS must have a value (not missing key)."""
        write_channels(sample_channels, output_dir)
        with open(output_dir / "Channel.CSV") as f:
            reader = csv.DictReader(f)
            for row in reader:
                for col in CHANNEL_COLUMNS:
                    assert col in row, f"Missing column: {col}"


    def test_tx_prohibit_on(self, output_dir):
        """TX Prohibit field should be written to CSV."""
        ch = AnytoneChannel(
            name="PMR 1",
            rx_freq="446.00625",
            tx_freq="446.00625",
            channel_type="A-Analog",
            tx_prohibit="On",
        )
        write_channels([ch], output_dir)
        with open(output_dir / "Channel.CSV") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert row["TX Prohibit"] == "On"


class TestWriteZones:
    def test_creates_file(self, sample_channels, output_dir):
        zones = [AnytoneZone(name="2m FM", channels=sample_channels[:1])]
        path = write_zones(zones, output_dir)
        assert path.exists()
        assert path.name == "Zone.CSV"

    def test_has_correct_columns(self, sample_channels, output_dir):
        zones = [AnytoneZone(name="2m FM", channels=sample_channels[:1])]
        write_zones(zones, output_dir)
        with open(output_dir / "Zone.CSV") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == ZONE_COLUMNS

    def test_pipe_delimited_members(self, sample_channels, output_dir):
        zones = [AnytoneZone(name="test", channels=sample_channels)]
        write_zones(zones, output_dir)
        with open(output_dir / "Zone.CSV") as f:
            reader = csv.DictReader(f)
            row = next(reader)
        assert "|" in row["Zone Channel Member"]
        members = row["Zone Channel Member"].split("|")
        assert len(members) == 2


class TestWriteTalkgroups:
    def test_creates_file(self, output_dir):
        path = write_talkgroups(output_dir)
        assert path.exists()
        assert path.name == "TalkGroups.CSV"

    def test_has_correct_columns(self, output_dir):
        write_talkgroups(output_dir)
        with open(output_dir / "TalkGroups.CSV") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == TALKGROUP_COLUMNS

    def test_default_talkgroups(self, output_dir):
        write_talkgroups(output_dir)
        with open(output_dir / "TalkGroups.CSV") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        names = [r["Name"] for r in rows]
        assert "Local" in names
        assert "UK Wide" in names
        ids = [r["Radio ID"] for r in rows]
        assert "9" in ids
        assert "235" in ids
