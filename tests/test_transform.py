"""Tests for the transform module."""

from __future__ import annotations

from codeplug_csv.config import MAX_NAME_LENGTH
from codeplug_csv.models import AnytoneChannel, Repeater
from codeplug_csv.transform import (
    _bandwidth_str,
    _ctcss_str,
    _ensure_unique_channel_names,
    _extract_color_code,
    _hz_to_mhz,
    _make_channel_name,
    filter_repeaters,
    transform_repeaters,
)


def _repeater(
    callsign: str,
    *,
    band: str = "2M",
    tx: int = 145_687_500,
    rx: int = 145_087_500,
    mode_codes: list[str] | None = None,
    locator: str = "IO94DR",
    status: str = "OPERATIONAL",
    rpt_type: str = "RL",
) -> Repeater:
    return Repeater(
        repeater=callsign,
        tx=tx,
        rx=rx,
        band=band,
        mode_codes=mode_codes or ["A"],
        ctcss=118.8,
        txbw=12.5,
        town="TEST",
        status=status,
        type=rpt_type,
        locator=locator,
    )


class TestFilterRepeaters:
    def test_excludes_non_operational(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        callsigns = [r.repeater for r in filtered]
        assert "GB3YK" not in callsigns  # NOT OPERATIONAL

    def test_excludes_beacons(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        callsigns = [r.repeater for r in filtered]
        assert "GB3BA" not in callsigns  # type=BN

    def test_excludes_dstar_only(self, sample_repeaters):
        """D-STAR only repeaters (no A or M) should be excluded."""
        filtered = filter_repeaters(sample_repeaters)
        callsigns = [r.repeater for r in filtered]
        assert "GB7MC" not in callsigns  # modeCodes=["D"]

    def test_keeps_analog(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        callsigns = [r.repeater for r in filtered]
        assert "GB3CD-L" in callsigns

    def test_keeps_dmr(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        callsigns = [r.repeater for r in filtered]
        assert "GB7AA" in callsigns
        assert "GB7AV" in callsigns

    def test_keeps_multimode(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        callsigns = [r.repeater for r in filtered]
        assert "GB3RD" in callsigns  # modeCodes=["A","M:2"]

    def test_locator_filter(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters, locator_prefix="IO91")
        callsigns = [r.repeater for r in filtered]
        assert "GB7AA" in callsigns  # IO91WM
        assert "GB3RD" in callsigns  # IO91LM
        assert "GB3CD-L" not in callsigns  # IO94DR

    def test_bare_m_kept(self, sample_repeaters):
        """Bare 'M' (no color code suffix) should still be treated as DMR."""
        filtered = filter_repeaters(sample_repeaters)
        callsigns = [r.repeater for r in filtered]
        assert "GB7LD" in callsigns  # modeCodes=["M"]

    def test_deduplicates_exact_records(self):
        """Identical API rows must not produce duplicate channel names."""
        original = _repeater("GB3IV")
        duplicate = _repeater("GB3IV")

        filtered = filter_repeaters([original, duplicate])

        assert len(filtered) == 1


class TestHelpers:
    def test_hz_to_mhz(self):
        assert _hz_to_mhz(145687500) == "145.68750"
        assert _hz_to_mhz(439450000) == "439.45000"

    def test_make_channel_name_keeps_callsign_suffix_and_band(self):
        name = _make_channel_name("GB3CD-L", "2m", "FM")
        assert name == "GB3CD-L VHF FM"
        assert len(name) <= MAX_NAME_LENGTH

    def test_make_channel_name_ts_suffix(self):
        assert _make_channel_name("GB7AA", "70cm", "TS1") == "GB7AA UHF TS1"
        assert _make_channel_name("GB7AA", "70cm", "TS2") == "GB7AA UHF TS2"

    def test_make_channel_name_reserves_suffix_when_truncating(self):
        name = _make_channel_name("GB3ABCDEFGHIJ-L", "70cm", "TS1")
        assert len(name) <= MAX_NAME_LENGTH
        assert name.endswith("TS1")

    def test_ensure_unique_channel_names_renames_collisions(self):
        channels = [
            AnytoneChannel(
                name="GB3IM UHF FM",
                rx_freq="430.82500",
                tx_freq="438.42500",
                channel_type="A-Analog",
            ),
            AnytoneChannel(
                name="GB3IM UHF FM",
                rx_freq="430.82500",
                tx_freq="438.42500",
                channel_type="A-Analog",
            ),
        ]

        _ensure_unique_channel_names(channels)

        assert len({ch.name for ch in channels}) == 2
        assert channels[0].name == "GB3IM UHF FM"
        assert channels[1].name.endswith("~2")

    def test_extract_color_code_with_value(self):
        assert _extract_color_code(["M:3"]) == 3
        assert _extract_color_code(["A", "M:1"]) == 1
        assert _extract_color_code(["M:15"]) == 15

    def test_extract_color_code_bare_m(self):
        assert _extract_color_code(["M"]) == 1

    def test_bandwidth_str(self):
        assert _bandwidth_str(25) == "25K"
        assert _bandwidth_str(12.5) == "12.5K"

    def test_ctcss_str(self):
        assert _ctcss_str(118.8) == "118.8"
        assert _ctcss_str(0) == "Off"
        assert _ctcss_str(77.0) == "77.0"


class TestTransformRepeaters:
    def test_frequency_swap(self, sample_repeaters):
        """API tx → Anytone RX, API rx → Anytone TX."""
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        # GB3CD-L: api tx=145687500, api rx=145087500
        gb3cd = next(ch for ch in channels if "GB3CD" in ch.name)
        assert gb3cd.rx_freq == "145.68750"
        assert gb3cd.tx_freq == "145.08750"

    def test_multimode_produces_three_channels(self, sample_repeaters):
        """Repeater with both A and M should produce FM + TS1 + TS2 channels."""
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        gb3rd = [ch for ch in channels if "GB3RD" in ch.name]
        assert len(gb3rd) == 3
        names = {ch.name for ch in gb3rd}
        assert "GB3RD UHF FM" in names
        assert "GB3RD UHF TS1" in names
        assert "GB3RD UHF TS2" in names

    def test_dmr_color_code(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        gb7aa_ts1 = next(ch for ch in channels if ch.name == "GB7AA UHF TS1")
        assert gb7aa_ts1.color_code == 1
        gb7av_ts1 = next(ch for ch in channels if ch.name == "GB7AV UHF TS1")
        assert gb7av_ts1.color_code == 3

    def test_bare_m_default_color_code(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        gb7ld_ts1 = next(ch for ch in channels if ch.name == "GB7LD UHF TS1")
        assert gb7ld_ts1.color_code == 1

    def test_analog_ctcss(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        gb3cd = next(ch for ch in channels if "GB3CD" in ch.name and ch.mode == "ANL")
        assert gb3cd.ctcss_encode == "118.8"

    def test_analog_bandwidth_25k(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        gb3bs = next(ch for ch in channels if "GB3BS" in ch.name)
        assert gb3bs.bandwidth == "25K"

    def test_channel_names_max_length(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        for ch in channels:
            assert len(ch.name) <= MAX_NAME_LENGTH, (
                f"Channel name too long: {ch.name!r}"
            )

    def test_analog_mode_is_anl(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        gb3cd = next(ch for ch in channels if "GB3CD" in ch.name)
        assert gb3cd.mode == "ANL"

    def test_dmr_produces_ts1_and_ts2(self, sample_repeaters):
        """Each DMR repeater should produce two channels with slot 1 and 2."""
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        gb7aa = [ch for ch in channels if "GB7AA" in ch.name]
        assert len(gb7aa) == 2
        assert gb7aa[0].name == "GB7AA UHF TS1"
        assert gb7aa[0].slot == 1
        assert gb7aa[1].name == "GB7AA UHF TS2"
        assert gb7aa[1].slot == 2

    def test_same_callsign_on_both_bands_gets_unique_names(self):
        repeaters = [
            _repeater(
                "GB7HQ",
                band="2M",
                tx=145_662_500,
                rx=145_062_500,
                mode_codes=["M:1"],
                locator="IO93",
            ),
            _repeater(
                "GB7HQ",
                band="70CM",
                tx=433_025_000,
                rx=434_625_000,
                mode_codes=["M:1"],
                locator="IO93",
            ),
        ]

        channels = transform_repeaters(repeaters)
        names = [ch.name for ch in channels]

        assert names == [
            "GB7HQ VHF TS1",
            "GB7HQ VHF TS2",
            "GB7HQ UHF TS1",
            "GB7HQ UHF TS2",
        ]
        assert len(names) == len(set(names))

    def test_suffix_variants_get_unique_names(self):
        repeaters = [
            _repeater(
                "GB3IM-C",
                band="70CM",
                tx=430_825_000,
                rx=438_425_000,
                locator="IO74SD",
            ),
            _repeater(
                "GB3IM-R",
                band="70CM",
                tx=430_825_000,
                rx=438_425_000,
                locator="IO74TI",
            ),
        ]

        channels = transform_repeaters(repeaters)
        names = [ch.name for ch in channels]

        assert names == ["GB3IM-C UHF FM", "GB3IM-R UHF FM"]
        assert len(names) == len(set(names))

    def test_channels_are_ordered_by_callsign_not_api_order(self):
        """The RSGB API returns records in arbitrary order; zones must still
        list their channels in ascending callsign order."""
        repeaters = [
            _repeater(callsign)
            for callsign in ("GB7ZZ", "GB7AA", "GB7MM", "GB7BB")
        ]

        names = [ch.name for ch in transform_repeaters(repeaters)]

        assert names == [
            "GB7AA VHF FM",
            "GB7BB VHF FM",
            "GB7MM VHF FM",
            "GB7ZZ VHF FM",
        ]

    def test_callsign_order_keeps_multimode_channels_together(self):
        """Sorting repeaters, not channel names, keeps FM/TS1/TS2 adjacent."""
        repeaters = [
            _repeater("GB7ZZ", mode_codes=["A", "M:1"]),
            _repeater("GB7AA", mode_codes=["A", "M:1"]),
        ]

        names = [ch.name for ch in transform_repeaters(repeaters)]

        assert names == [
            "GB7AA VHF FM",
            "GB7AA VHF TS1",
            "GB7AA VHF TS2",
            "GB7ZZ VHF FM",
            "GB7ZZ VHF TS1",
            "GB7ZZ VHF TS2",
        ]

    def test_unknown_locator_uses_other_region(self):
        channels = transform_repeaters(
            [_repeater("GB3IV", locator="I065PE")]
        )
        assert channels[0].region == "OTHER"

    def test_region_from_locator(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        # GB3CD-L has locator IO94DR → NE
        gb3cd = next(ch for ch in channels if "GB3CD" in ch.name)
        assert gb3cd.region == "NE"
        # GB7AA has locator IO91WM → LONDON
        gb7aa = next(ch for ch in channels if "GB7AA" in ch.name)
        assert gb7aa.region == "LONDON"
        # GB7AV has locator IO81RJ → SW (column R > L)
        gb7av = next(ch for ch in channels if "GB7AV" in ch.name)
        assert gb7av.region == "SW"

    def test_rpt_type_default_is_rpt(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        # Non-gateway fixtures should all be RPT
        non_gw = [ch for ch in channels if "GB3GW" not in ch.name]
        for ch in non_gw:
            assert ch.rpt_type == "RPT"

    def test_rpt_type_gateway(self, sample_repeaters):
        """Gateway type (AG) should produce rpt_type='GW'."""
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        gw_ch = next(ch for ch in channels if "GB3GW" in ch.name)
        assert gw_ch.rpt_type == "GW"
