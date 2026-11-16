"""Tests for the zones module."""

from __future__ import annotations

from codeplug_csv.config import MAX_NAME_LENGTH
from codeplug_csv.models import AnytoneChannel
from codeplug_csv.regions import UK_REGIONS, UNKNOWN_REGION
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
    def test_groups_by_region_band_mode_type(self):
        channels = [
            _make_channel("CH1 FM", "2m", "ANL", region="NE", rpt_type="RPT"),
            _make_channel("CH2 FM", "70cm", "ANL", region="SW", rpt_type="RPT"),
            _make_channel("CH3 DMR", "70cm", "DMR", region="SW", rpt_type="RPT"),
        ]
        zones = assign_zones(channels)
        zone_names = [z.name for z in zones]
        assert "NE 2m FM" in zone_names
        assert "SW 70cm FM" in zone_names
        assert "SW 70cm DMR" in zone_names
        assert len(zones) == 3

    def test_separates_bands_within_same_region_and_mode(self):
        channels = [
            _make_channel("CH1 FM", "2m", "ANL", region="NE", rpt_type="RPT"),
            _make_channel("CH2 FM", "70cm", "ANL", region="NE", rpt_type="RPT"),
        ]
        zones = assign_zones(channels)

        assert [z.name for z in zones] == ["NE 2m FM", "NE 70cm FM"]
        for zone in zones:
            assert len({ch.band for ch in zone.channels}) == 1

    def test_gateway_type_separate_zone(self):
        channels = [
            _make_channel("CH1 FM", "2m", "ANL", region="NE", rpt_type="RPT"),
            _make_channel("CH2 FM", "2m", "ANL", region="NE", rpt_type="GW"),
        ]
        zones = assign_zones(channels)
        zone_names = [z.name for z in zones]
        assert "NE 2m FM" in zone_names
        assert "NE 2m AG" in zone_names

    def test_digital_gateway_label(self):
        channels = [
            _make_channel("CH1 DMR", "70cm", "DMR", region="NE", rpt_type="GW"),
        ]
        zones = assign_zones(channels)

        assert [z.name for z in zones] == ["NE 70cm DG"]

    def test_zone_names_max_length(self):
        channels = [
            _make_channel("CH1", "70cm", "DMR", region="LONDON", rpt_type="RPT"),
            _make_channel("CH2", "70cm", "DMR", region="LONDON", rpt_type="GW"),
        ]
        zones = assign_zones(channels)
        for zone in zones:
            assert len(zone.name) <= MAX_NAME_LENGTH

    def test_splits_large_zones(self):
        channels = [
            _make_channel(f"CH{i:03d} FM", "2m", "ANL", region="SE", rpt_type="RPT")
            for i in range(300)
        ]
        zones = assign_zones(channels)
        se_zones = [z for z in zones if z.name.startswith("SE 2m FM")]
        assert len(se_zones) == 2
        assert se_zones[0].name == "SE 2m FM 1"
        assert se_zones[1].name == "SE 2m FM 2"
        assert len(se_zones[0].channels) == 250
        assert len(se_zones[1].channels) == 50

    def test_split_names_stay_unique_when_key_fills_name_budget(self):
        channels = [
            _make_channel(f"CH{i:03d} DMR", "70cm", "DMR", region="LONDON")
            for i in range(300)
        ]
        zones = assign_zones(channels)
        names = [z.name for z in zones]

        assert len(names) == 2
        assert len(set(names)) == 2
        assert all(len(name) <= MAX_NAME_LENGTH for name in names)

    def test_all_region_band_mode_type_labels_unique_and_short(self):
        channels = [
            _make_channel(
                f"CH-{region}-{band}-{mode}-{rpt_type}",
                band,
                mode,
                region=region,
                rpt_type=rpt_type,
            )
            for region in (*UK_REGIONS, UNKNOWN_REGION)
            for band in ("2m", "70cm")
            for mode in ("ANL", "DMR")
            for rpt_type in ("RPT", "GW")
        ]
        zones = assign_zones(channels)
        names = [z.name for z in zones]

        assert len(names) == len(set(names))
        assert all(len(name) <= MAX_NAME_LENGTH for name in names)
        assert len(zones) == len(channels)

    def test_empty_input(self):
        assert assign_zones([]) == []
