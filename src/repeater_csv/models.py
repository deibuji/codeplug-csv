"""Data models for the RSGB-to-Anytone conversion pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Repeater:
    """Raw repeater record from the RSGB API."""

    repeater: str  # callsign, e.g. "GB3CD-L"
    tx: int  # repeater TX frequency in Hz
    rx: int  # repeater RX frequency in Hz
    band: str  # e.g. "2M", "70CM"
    mode_codes: list[str] = field(default_factory=list)  # e.g. ["A", "M:3"]
    ctcss: float = 0.0
    txbw: float = 12.5
    town: str = ""
    status: str = ""
    type: str = ""
    locator: str = ""


@dataclass
class AnytoneChannel:
    """A single channel row for Anytone Channel.CSV."""

    name: str  # max 16 chars
    rx_freq: str  # MHz, 5 decimal places (radio receives = repeater TX)
    tx_freq: str  # MHz, 5 decimal places (radio transmits = repeater RX)
    channel_type: str  # "A-Analog" or "D-Digital"
    bandwidth: str = "12.5K"
    ctcss_encode: str = "Off"
    ctcss_decode: str = "Off"
    power: str = "High"
    color_code: int = 1
    slot: int = 1
    contact: str = ""
    contact_call_type: str = "Group Call"
    # For zone assignment
    band: str = ""  # "2m" or "70cm"
    mode: str = ""  # "FM" or "DMR"


@dataclass
class AnytoneZone:
    """A zone for Anytone Zone.CSV."""

    name: str  # max 16 chars
    channels: list[AnytoneChannel] = field(default_factory=list)


@dataclass
class TalkGroup:
    """A DMR talkgroup for TalkGroups.CSV."""

    name: str
    radio_id: int
    call_type: str = "Group Call"
    call_alert: str = "None"
