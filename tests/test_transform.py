"""Tests for the transform module."""

from __future__ import annotations

from repeater_csv.models import Repeater
from repeater_csv.transform import (
    _bandwidth_str,
    _clean_callsign,
    _ctcss_str,
    _extract_color_code,
    _hz_to_mhz,
    _make_channel_name,
    filter_repeaters,
    transform_repeaters,
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


class TestHelpers:
    def test_hz_to_mhz(self):
        assert _hz_to_mhz(145687500) == "145.68750"
        assert _hz_to_mhz(439450000) == "439.45000"

    def test_clean_callsign(self):
        assert _clean_callsign("GB3CD-L") == "GB3CD"
        assert _clean_callsign("GB7AA") == "GB7AA"
        assert _clean_callsign("GB3WR-R") == "GB3WR"

    def test_make_channel_name_within_limit(self):
        name = _make_channel_name("GB3CD-L", "CROOK", "FM")
        assert len(name) <= 16
        assert "GB3CD" in name
        assert "FM" in name

    def test_make_channel_name_long_town_truncated(self):
        name = _make_channel_name("GB7AA", "WOLVERHAMPTON", "DMR")
        assert len(name) <= 16

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

    def test_multimode_produces_two_channels(self, sample_repeaters):
        """Repeater with both A and M should produce FM + DMR channels."""
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        gb3rd = [ch for ch in channels if "GB3RD" in ch.name]
        assert len(gb3rd) == 2
        types = {ch.channel_type for ch in gb3rd}
        assert types == {"A-Analog", "D-Digital"}

    def test_dmr_color_code(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        gb7aa = next(ch for ch in channels if "GB7AA" in ch.name)
        assert gb7aa.color_code == 1
        gb7av = next(ch for ch in channels if "GB7AV" in ch.name)
        assert gb7av.color_code == 3

    def test_bare_m_default_color_code(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        gb7ld = next(ch for ch in channels if "GB7LD" in ch.name)
        assert gb7ld.color_code == 1

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
            assert len(ch.name) <= 16, f"Channel name too long: {ch.name!r}"

    def test_analog_mode_is_anl(self, sample_repeaters):
        filtered = filter_repeaters(sample_repeaters)
        channels = transform_repeaters(filtered)
        gb3cd = next(ch for ch in channels if "GB3CD" in ch.name)
        assert gb3cd.mode == "ANL"

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
