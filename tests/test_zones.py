"""Tests for the zones module."""

from __future__ import annotations

from repeater_csv.models import AnytoneChannel
from repeater_csv.zones import assign_zones


def _make_channel(name: str, band: str, mode: str) -> AnytoneChannel:
    return AnytoneChannel(
        name=name,
        rx_freq="145.00000",
        tx_freq="145.60000",
        channel_type="A-Analog" if mode == "FM" else "D-Digital",
        band=band,
        mode=mode,
    )


class TestAssignZones:
    def test_groups_by_band_and_mode(self):
        channels = [
            _make_channel("CH1 FM", "2m", "FM"),
            _make_channel("CH2 FM", "70cm", "FM"),
            _make_channel("CH3 DMR", "70cm", "DMR"),
        ]
        zones = assign_zones(channels)
        zone_names = [z.name for z in zones]
        assert "2m FM" in zone_names
        assert "70cm DMR" in zone_names
        assert "70cm FM" in zone_names

    def test_zone_names_max_length(self):
        channels = [_make_channel("CH1", "2m", "FM")]
        zones = assign_zones(channels)
        for z in zones:
            assert len(z.name) <= 16

    def test_splits_large_zones(self):
        channels = [_make_channel(f"CH{i:03d} FM", "2m", "FM") for i in range(300)]
        zones = assign_zones(channels)
        fm_zones = [z for z in zones if "2m FM" in z.name]
        assert len(fm_zones) == 2
        assert len(fm_zones[0].channels) == 250
        assert len(fm_zones[1].channels) == 50

    def test_empty_input(self):
        assert assign_zones([]) == []
