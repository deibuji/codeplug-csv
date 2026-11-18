"""Tests for the zones module."""

from __future__ import annotations

from codeplug_csv.config import MAX_NAME_LENGTH
from codeplug_csv.models import AnytoneChannel, AnytoneZone
from codeplug_csv.regions import UK_REGIONS, UNKNOWN_REGION
from codeplug_csv.zones import assign_zones, drop_empty_zones


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


class TestDropEmptyZones:
    def test_removes_channel_less_zone(self):
        zones = [
            AnytoneZone(name="NE VHF FM", channels=[_make_channel("CH1", "2m", "ANL")]),
            AnytoneZone(name=f"{UNKNOWN_REGION} VHF FM", channels=[]),
        ]

        assert [z.name for z in drop_empty_zones(zones)] == ["NE VHF FM"]

    def test_keeps_remaining_zones_in_order(self):
        zones = [
            AnytoneZone(name="A", channels=[_make_channel("CH1", "2m", "ANL")]),
            AnytoneZone(name="B", channels=[]),
            AnytoneZone(name="C", channels=[_make_channel("CH2", "2m", "ANL")]),
        ]

        assert [z.name for z in drop_empty_zones(zones)] == ["A", "C"]

    def test_warns_when_dropping(self, caplog):
        zones = [AnytoneZone(name="EMPTY", channels=[])]

        with caplog.at_level("WARNING"):
            assert drop_empty_zones(zones) == []

        assert "Dropping empty zone 'EMPTY'" in caplog.text


class TestAssignZones:
    def test_groups_by_region_band_mode_type(self):
        channels = [
            _make_channel("CH1 FM", "2m", "ANL", region="NE", rpt_type="RPT"),
            _make_channel("CH2 FM", "70cm", "ANL", region="SW", rpt_type="RPT"),
            _make_channel("CH3 DMR", "70cm", "DMR", region="SW", rpt_type="RPT"),
        ]
        zones = assign_zones(channels)
        zone_names = [z.name for z in zones]
        assert "NE VHF FM" in zone_names
        assert "SW UHF FM" in zone_names
        assert "SW UHF DV" in zone_names
        assert len(zones) == 3

    def test_separates_bands_within_same_region_and_mode(self):
        channels = [
            _make_channel("CH1 FM", "2m", "ANL", region="NE", rpt_type="RPT"),
            _make_channel("CH2 FM", "70cm", "ANL", region="NE", rpt_type="RPT"),
        ]
        zones = assign_zones(channels)

        assert [z.name for z in zones] == ["NE VHF FM", "NE UHF FM"]
        for zone in zones:
            assert len({ch.band for ch in zone.channels}) == 1

    def test_gateway_type_separate_zone(self):
        channels = [
            _make_channel("CH1 FM", "2m", "ANL", region="NE", rpt_type="RPT"),
            _make_channel("CH2 FM", "2m", "ANL", region="NE", rpt_type="GW"),
        ]
        zones = assign_zones(channels)
        zone_names = [z.name for z in zones]
        assert "NE VHF FM" in zone_names
        assert "NE VHF AG" in zone_names

    def test_digital_gateway_label(self):
        channels = [
            _make_channel("CH1 DMR", "70cm", "DMR", region="NE", rpt_type="GW"),
        ]
        zones = assign_zones(channels)

        assert [z.name for z in zones] == ["NE UHF DG"]

    def test_digital_repeater_label_is_dv(self):
        channels = [
            _make_channel("CH1 DMR", "70cm", "DMR", region="NE", rpt_type="RPT"),
        ]
        zones = assign_zones(channels)

        assert [z.name for z in zones] == ["NE UHF DV"]

    def test_vhf_zones_sort_before_uhf(self):
        """Zone order drives channel numbering, so it must not follow the
        text order of the labels (which would put UHF first)."""
        channels = [
            _make_channel("CH1 FM", "70cm", "ANL", region="NE", rpt_type="RPT"),
            _make_channel("CH2 FM", "2m", "ANL", region="NE", rpt_type="RPT"),
        ]
        zones = assign_zones(channels)

        assert [z.name for z in zones] == ["NE VHF FM", "NE UHF FM"]

    def test_other_region_zones_sort_last(self):
        """Unmapped locators are a catch-all, so they must not interleave
        with real regions just because "OTHER" starts with O."""
        channels = [
            _make_channel("CH1", "2m", "ANL", region=UNKNOWN_REGION),
            _make_channel("CH2", "2m", "ANL", region="WAL"),
            _make_channel("CH3", "2m", "ANL", region="E.ANG"),
        ]
        zones = assign_zones(channels)

        assert [z.name for z in zones] == [
            "E.ANG VHF FM",
            "WAL VHF FM",
            f"{UNKNOWN_REGION} VHF FM",
        ]

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
        se_zones = [z for z in zones if z.name.startswith("SE VHF FM")]
        assert len(se_zones) == 2
        assert se_zones[0].name == "SE VHF FM 1"
        assert se_zones[1].name == "SE VHF FM 2"
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
