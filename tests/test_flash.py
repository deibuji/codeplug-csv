"""Tests for dmrconfig flash/export helpers."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from codeplug_csv.flash import (
    RadioUserLookupError,
    build_flash_command,
    lookup_radio_user,
    write_dmrconfig_config,
)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_lookup_radio_user_finds_match(tmp_path: Path) -> None:
    users_csv = tmp_path / "user.csv"
    _write_csv(
        users_csv,
        [
            "RADIO_ID",
            "CALLSIGN",
            "FIRST_NAME",
            "LAST_NAME",
            "CITY",
            "STATE",
            "COUNTRY",
        ],
        [
            {
                "RADIO_ID": "1234567",
                "CALLSIGN": "N0CALL",
                "FIRST_NAME": "Casey",
                "LAST_NAME": "Operator",
                "CITY": "Denver",
                "STATE": "Colorado",
                "COUNTRY": "United States",
            }
        ],
    )

    user = lookup_radio_user(users_csv, 1234567)

    assert user.callsign == "N0CALL"
    assert user.first_name == "Casey"
    assert user.country == "United States"


def test_lookup_radio_user_missing_raises(tmp_path: Path) -> None:
    users_csv = tmp_path / "user.csv"
    _write_csv(
        users_csv,
        ["RADIO_ID", "CALLSIGN", "FIRST_NAME", "LAST_NAME", "CITY", "STATE", "COUNTRY"],
        [],
    )

    with pytest.raises(RadioUserLookupError):
        lookup_radio_user(users_csv, 9999999)


def test_write_dmrconfig_config_renders_sections(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    users_csv = output_dir / "user.csv"
    channel_csv = output_dir / "Channel.CSV"
    zone_csv = output_dir / "Zone.CSV"
    talkgroup_csv = output_dir / "TalkGroups.CSV"
    conf_path = output_dir / "codeplug-1234567.conf"

    _write_csv(
        users_csv,
        [
            "RADIO_ID",
            "CALLSIGN",
            "FIRST_NAME",
            "LAST_NAME",
            "CITY",
            "STATE",
            "COUNTRY",
        ],
        [
            {
                "RADIO_ID": "1234567",
                "CALLSIGN": "N0CALL",
                "FIRST_NAME": "Casey",
                "LAST_NAME": "Operator",
                "CITY": "Denver",
                "STATE": "Colorado",
                "COUNTRY": "United States",
            }
        ],
    )

    _write_csv(
        channel_csv,
        [
            "No.",
            "Channel Name",
            "Receive Frequency",
            "Transmit Frequency",
            "Channel Type",
            "Transmit Power",
            "TX Prohibit",
            "CTCSS/DCS Decode",
            "CTCSS/DCS Encode",
            "Band Width",
            "Color Code",
            "Slot",
            "Contact",
        ],
        [
            {
                "No.": "1",
                "Channel Name": "GB3AA FM",
                "Receive Frequency": "145.60000",
                "Transmit Frequency": "145.00000",
                "Channel Type": "A-Analog",
                "Transmit Power": "High",
                "TX Prohibit": "Off",
                "CTCSS/DCS Decode": "118.8",
                "CTCSS/DCS Encode": "118.8",
                "Band Width": "12.5K",
                "Color Code": "1",
                "Slot": "1",
                "Contact": "",
            },
            {
                "No.": "2",
                "Channel Name": "GB7AA TS1",
                "Receive Frequency": "439.45000",
                "Transmit Frequency": "430.85000",
                "Channel Type": "D-Digital",
                "Transmit Power": "Mid",
                "TX Prohibit": "Off",
                "CTCSS/DCS Decode": "Off",
                "CTCSS/DCS Encode": "Off",
                "Band Width": "12.5K",
                "Color Code": "1",
                "Slot": "1",
                "Contact": "Local",
            },
        ],
    )

    _write_csv(
        zone_csv,
        ["No.", "Zone Name", "Zone Channel Member", "A Channel", "B Channel"],
        [
            {
                "No.": "1",
                "Zone Name": "Home Zone",
                "Zone Channel Member": "GB3AA FM|GB7AA TS1",
                "A Channel": "GB3AA FM",
                "B Channel": "GB3AA FM",
            }
        ],
    )

    _write_csv(
        talkgroup_csv,
        ["No.", "Radio ID", "Name", "Call Type", "Call Alert"],
        [
            {
                "No.": "1",
                "Radio ID": "9",
                "Name": "Local",
                "Call Type": "Group Call",
                "Call Alert": "None",
            }
        ],
    )

    written_path, user = write_dmrconfig_config(
        radio_id=1234567,
        users_csv=users_csv,
        channel_csv=channel_csv,
        zone_csv=zone_csv,
        talkgroup_csv=talkgroup_csv,
        output_conf=conf_path,
    )

    assert written_path == conf_path
    assert written_path.exists()
    assert user.callsign == "N0CALL"

    rendered = written_path.read_text(encoding="utf-8")
    assert "Radio: Anytone AT-D878UV" in rendered
    assert "ID: 1234567" in rendered
    assert "Name: N0CALL" in rendered
    assert "Contact Name Type ID RxTone" in rendered
    assert "Analog Name Receive Transmit Power Scan TOT RO Admit Squelch RxTone TxTone Width" in rendered
    assert "Digital Name Receive Transmit Power Scan TOT RO Admit Color Slot RxGL TxContact" in rendered
    assert "Zone Name Channels" in rendered
    assert "Home_Zone" in rendered
    assert "1-2" in rendered


def test_build_flash_command_no_resolve() -> None:
    cmd = build_flash_command(
        Path("output/codeplug-1234567.conf"),
        dmrconfig_bin="dmrconfig",
        trace=True,
        resolve_binary=False,
    )

    assert cmd == ["dmrconfig", "-c", "-t", "output/codeplug-1234567.conf"]
