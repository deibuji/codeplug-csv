"""Tests for the zones module."""

from __future__ import annotations

from codeplug_csv.models import AnytoneChannel
from codeplug_csv.zones import assign_zones


def _make_channel(
    name: str,
    band: str,
    mode: str,
    region: str = "SE",
    rpt_type: str = "RPT",
) -> AnytoneChannel:
    return AnytoneChannel(
        name=name,
        rx_freq="145.00000",
        tx_freq="145.60000",
        channel_type="A-Analog" if mode == "ANL" else "D-Digital",
        band=band,
        mode=mode,
        region=region,
        rpt_type=rpt_type,
    )


class TestAssignZones:
    def test_groups_by_region_mode_type(self):
        channels = [
            _make_channel("CH1 FM", "2m", "ANL", region="NE", rpt_type="RPT"),
            _make_channel("CH2 FM", "70cm", "ANL", region="SW", rpt_type="RPT"),
            _make_channel("CH3 DMR", "70cm", "DMR", region="SW", rpt_type="RPT"),
        ]
        zones = assign_zones(channels)
        zone_names = [z.name for z in zones]
        assert "NE ANL RPT" in zone_names
        assert "SW ANL RPT" in zone_names
        assert "SW DMR RPT" in zone_names

    def test_gateway_type_separate_zone(self):
        channels = [
            _make_channel("CH1 FM", "2m", "ANL", region="NE", rpt_type="RPT"),
            _make_channel("CH2 FM", "2m", "ANL", region="NE", rpt_type="GW"),
        ]
        zones = assign_zones(channels)
        zone_names = [z.name for z in zones]
        assert "NE ANL RPT" in zone_names
        assert "NE ANL GW" in zone_names

    def test_zone_names_max_length(self):
        channels = [_make_channel("CH1", "2m", "ANL", region="LONDON", rpt_type="RPT")]
        zones = assign_zones(channels)
        for z in zones:
            assert len(z.name) <= 16

    def test_splits_large_zones(self):
        channels = [
            _make_channel(f"CH{i:03d} FM", "2m", "ANL", region="SE", rpt_type="RPT")
            for i in range(300)
        ]
        zones = assign_zones(channels)
        se_zones = [z for z in zones if "SE ANL RPT" in z.name]
        assert len(se_zones) == 2
        assert len(se_zones[0].channels) == 250
        assert len(se_zones[1].channels) == 50

    def test_empty_input(self):
        assert assign_zones([]) == []
