"""Tests for the simplex/utility zone builders."""

from __future__ import annotations

from codeplug_csv.simplex import (
    get_static_zones,
    hotspot_zone,
    iss_zone,
    marine_vhf_zone,
    pmr446_zone,
    uhf_dv_simplex_zone,
    uhf_fm_simplex_zone,
    vhf_dv_simplex_zone,
    vhf_fm_simplex_zone,
)


class TestHotspot:
    def test_zone_name(self):
        zone = hotspot_zone()
        assert zone.name == "HOTSPOT"

    def test_channel_count(self):
        zone = hotspot_zone()
        assert len(zone.channels) == 4

    def test_simplex_channels_are_simplex(self):
        zone = hotspot_zone()
        # First two channels are simplex (RX == TX)
        assert zone.channels[0].rx_freq == zone.channels[0].tx_freq
        assert zone.channels[0].rx_freq == "434.00000"
        assert zone.channels[1].rx_freq == zone.channels[1].tx_freq
        assert zone.channels[1].rx_freq == "438.80000"

    def test_repeater_channels(self):
        zone = hotspot_zone()
        # HS RPT TS1 and HS RPT TS2
        for ch in zone.channels[2:]:
            assert ch.rx_freq == "434.00000"
            assert ch.tx_freq == "438.80000"

    def test_ts1_slot(self):
        zone = hotspot_zone()
        ts1 = zone.channels[2]
        assert ts1.name == "HS RPT TS1"
        assert ts1.slot == 1

    def test_ts2_slot(self):
        zone = hotspot_zone()
        ts2 = zone.channels[3]
        assert ts2.name == "HS RPT TS2"
        assert ts2.slot == 2

    def test_all_digital(self):
        zone = hotspot_zone()
        for ch in zone.channels:
            assert ch.channel_type == "D-Digital"

    def test_all_cc1(self):
        zone = hotspot_zone()
        for ch in zone.channels:
            assert ch.color_code == 1

    def test_all_12_5k(self):
        zone = hotspot_zone()
        for ch in zone.channels:
            assert ch.bandwidth == "12.5K"

    def test_name_lengths(self):
        zone = hotspot_zone()
        for ch in zone.channels:
            assert len(ch.name) <= 16

    def test_all_contact_local(self):
        zone = hotspot_zone()
        for ch in zone.channels:
            assert ch.contact == "Local"


class TestVhfFmSimplex:
    def test_zone_name(self):
        zone = vhf_fm_simplex_zone()
        assert zone.name == "VHF FM SIMPLEX"

    def test_channel_count(self):
        zone = vhf_fm_simplex_zone()
        assert len(zone.channels) == 31

    def test_first_channel_freq(self):
        zone = vhf_fm_simplex_zone()
        assert zone.channels[0].rx_freq == "145.20000"

    def test_last_channel_freq(self):
        zone = vhf_fm_simplex_zone()
        assert zone.channels[-1].rx_freq == "145.57500"

    def test_calling_channel_name(self):
        zone = vhf_fm_simplex_zone()
        # V40 is index 40-16=24
        assert zone.channels[24].name == "V40 CALL"

    def test_simplex(self):
        zone = vhf_fm_simplex_zone()
        for ch in zone.channels:
            assert ch.rx_freq == ch.tx_freq

    def test_channel_type(self):
        zone = vhf_fm_simplex_zone()
        for ch in zone.channels:
            assert ch.channel_type == "A-Analog"

    def test_name_lengths(self):
        zone = vhf_fm_simplex_zone()
        for ch in zone.channels:
            assert len(ch.name) <= 16


class TestUhfFmSimplex:
    def test_zone_name(self):
        zone = uhf_fm_simplex_zone()
        assert zone.name == "UHF FM SIMPLEX"

    def test_channel_count(self):
        zone = uhf_fm_simplex_zone()
        assert len(zone.channels) == 17

    def test_first_channel_freq(self):
        zone = uhf_fm_simplex_zone()
        assert zone.channels[0].rx_freq == "433.40000"

    def test_last_channel_freq(self):
        zone = uhf_fm_simplex_zone()
        assert zone.channels[-1].rx_freq == "433.60000"

    def test_calling_channel_name(self):
        zone = uhf_fm_simplex_zone()
        # U280 is index 280-272=8
        assert zone.channels[8].name == "U280 CALL"

    def test_simplex(self):
        zone = uhf_fm_simplex_zone()
        for ch in zone.channels:
            assert ch.rx_freq == ch.tx_freq

    def test_channel_type(self):
        zone = uhf_fm_simplex_zone()
        for ch in zone.channels:
            assert ch.channel_type == "A-Analog"

    def test_name_lengths(self):
        zone = uhf_fm_simplex_zone()
        for ch in zone.channels:
            assert len(ch.name) <= 16


class TestVhfDvSimplex:
    def test_zone_name(self):
        zone = vhf_dv_simplex_zone()
        assert zone.name == "VHF DV SIMPLEX"

    def test_channel_count(self):
        zone = vhf_dv_simplex_zone()
        assert len(zone.channels) == 1

    def test_channel_name(self):
        zone = vhf_dv_simplex_zone()
        assert zone.channels[0].name == "2M DV CALL"

    def test_frequency(self):
        zone = vhf_dv_simplex_zone()
        assert zone.channels[0].rx_freq == "144.61250"

    def test_simplex(self):
        zone = vhf_dv_simplex_zone()
        assert zone.channels[0].rx_freq == zone.channels[0].tx_freq

    def test_channel_type(self):
        zone = vhf_dv_simplex_zone()
        assert zone.channels[0].channel_type == "D-Digital"

    def test_dmr_params(self):
        zone = vhf_dv_simplex_zone()
        assert zone.channels[0].color_code == 1
        assert zone.channels[0].slot == 1

    def test_name_length(self):
        zone = vhf_dv_simplex_zone()
        assert len(zone.channels[0].name) <= 16

    def test_contact_local(self):
        zone = vhf_dv_simplex_zone()
        assert zone.channels[0].contact == "Local"


class TestUhfDvSimplex:
    def test_zone_name(self):
        zone = uhf_dv_simplex_zone()
        assert zone.name == "UHF DV SIMPLEX"

    def test_channel_count(self):
        zone = uhf_dv_simplex_zone()
        assert len(zone.channels) == 8

    def test_first_channel_freq(self):
        zone = uhf_dv_simplex_zone()
        assert zone.channels[0].rx_freq == "438.58750"

    def test_last_channel_freq(self):
        zone = uhf_dv_simplex_zone()
        assert zone.channels[-1].rx_freq == "438.67500"

    def test_calling_channel_name(self):
        zone = uhf_dv_simplex_zone()
        # DH3 is index 2
        assert zone.channels[2].name == "DH3 CALL"

    def test_simplex(self):
        zone = uhf_dv_simplex_zone()
        for ch in zone.channels:
            assert ch.rx_freq == ch.tx_freq

    def test_channel_type(self):
        zone = uhf_dv_simplex_zone()
        for ch in zone.channels:
            assert ch.channel_type == "D-Digital"

    def test_dmr_params(self):
        zone = uhf_dv_simplex_zone()
        for ch in zone.channels:
            assert ch.color_code == 1
            assert ch.slot == 1

    def test_name_lengths(self):
        zone = uhf_dv_simplex_zone()
        for ch in zone.channels:
            assert len(ch.name) <= 16

    def test_all_contact_local(self):
        zone = uhf_dv_simplex_zone()
        for ch in zone.channels:
            assert ch.contact == "Local"


class TestPmr446:
    def test_zone_name(self):
        zone = pmr446_zone()
        assert zone.name == "PMR446"

    def test_channel_count(self):
        zone = pmr446_zone()
        assert len(zone.channels) == 16

    def test_first_channel_freq(self):
        zone = pmr446_zone()
        assert zone.channels[0].rx_freq == "446.00625"

    def test_last_channel_freq(self):
        zone = pmr446_zone()
        assert zone.channels[-1].rx_freq == "446.19375"

    def test_simplex(self):
        zone = pmr446_zone()
        for ch in zone.channels:
            assert ch.rx_freq == ch.tx_freq

    def test_tx_prohibit(self):
        zone = pmr446_zone()
        for ch in zone.channels:
            assert ch.tx_prohibit == "On"

    def test_bandwidth(self):
        zone = pmr446_zone()
        for ch in zone.channels:
            assert ch.bandwidth == "12.5K"

    def test_channel_type(self):
        zone = pmr446_zone()
        for ch in zone.channels:
            assert ch.channel_type == "A-Analog"

    def test_name_lengths(self):
        zone = pmr446_zone()
        for ch in zone.channels:
            assert len(ch.name) <= 16


class TestIss:
    def test_zone_name(self):
        zone = iss_zone()
        assert zone.name == "ISS"

    def test_channel_count(self):
        zone = iss_zone()
        assert len(zone.channels) == 7

    def test_doppler_downlink_frequencies(self):
        zone = iss_zone()
        expected_rx = [
            "145.80500",
            "145.80250",
            "145.80000",
            "145.79750",
            "145.79500",
        ]
        for i, expected in enumerate(expected_rx):
            assert zone.channels[i].rx_freq == expected

    def test_doppler_uplink(self):
        zone = iss_zone()
        for i in range(5):
            assert zone.channels[i].tx_freq == "145.20000"

    def test_rpt_up_ctcss(self):
        zone = iss_zone()
        rpt_up = zone.channels[5]
        assert rpt_up.name == "ISS RPT UP"
        assert rpt_up.ctcss_encode == "67.0"

    def test_rpt_up_simplex(self):
        zone = iss_zone()
        rpt_up = zone.channels[5]
        assert rpt_up.rx_freq == rpt_up.tx_freq
        assert rpt_up.rx_freq == "145.99000"

    def test_rpt_dn_simplex(self):
        zone = iss_zone()
        rpt_dn = zone.channels[6]
        assert rpt_dn.name == "ISS RPT DN"
        assert rpt_dn.rx_freq == rpt_dn.tx_freq
        assert rpt_dn.rx_freq == "437.80000"

    def test_bandwidth(self):
        zone = iss_zone()
        for ch in zone.channels:
            assert ch.bandwidth == "25K"

    def test_channel_type(self):
        zone = iss_zone()
        for ch in zone.channels:
            assert ch.channel_type == "A-Analog"

    def test_name_lengths(self):
        zone = iss_zone()
        for ch in zone.channels:
            assert len(ch.name) <= 16


class TestMarineVhf:
    def test_zone_name(self):
        zone = marine_vhf_zone()
        assert zone.name == "MARINE VHF"

    def test_channel_count(self):
        zone = marine_vhf_zone()
        assert len(zone.channels) == 22

    def test_first_channel_freq(self):
        zone = marine_vhf_zone()
        assert zone.channels[0].rx_freq == "156.30000"

    def test_last_channel_freq(self):
        zone = marine_vhf_zone()
        assert zone.channels[-1].rx_freq == "157.42500"

    def test_calling_channel_name(self):
        zone = marine_vhf_zone()
        ch16 = next(ch for ch in zone.channels if "16" in ch.name)
        assert ch16.name == "MAR 16 CALL"

    def test_simplex(self):
        zone = marine_vhf_zone()
        for ch in zone.channels:
            assert ch.rx_freq == ch.tx_freq

    def test_tx_prohibit(self):
        zone = marine_vhf_zone()
        for ch in zone.channels:
            assert ch.tx_prohibit == "On"

    def test_bandwidth(self):
        zone = marine_vhf_zone()
        for ch in zone.channels:
            assert ch.bandwidth == "25K"

    def test_channel_type(self):
        zone = marine_vhf_zone()
        for ch in zone.channels:
            assert ch.channel_type == "A-Analog"

    def test_name_lengths(self):
        zone = marine_vhf_zone()
        for ch in zone.channels:
            assert len(ch.name) <= 16

    def test_excludes_dsc_and_guard(self):
        """Ch 70 (DSC), 75, 76 (guard) should not be present."""
        zone = marine_vhf_zone()
        names = [ch.name for ch in zone.channels]
        for excluded in [70, 75, 76]:
            assert not any(
                f"MAR {excluded:02d}" in n or f"MAR {excluded} " in n for n in names
            )


class TestGetStaticZones:
    def test_returns_eight_zones(self):
        zones = get_static_zones()
        assert len(zones) == 8

    def test_total_channel_count(self):
        zones = get_static_zones()
        total = sum(len(z.channels) for z in zones)
        assert total == 106

    def test_zone_names(self):
        zones = get_static_zones()
        names = [z.name for z in zones]
        assert names == [
            "HOTSPOT",
            "VHF FM SIMPLEX",
            "UHF FM SIMPLEX",
            "VHF DV SIMPLEX",
            "UHF DV SIMPLEX",
            "PMR446",
            "ISS",
            "MARINE VHF",
        ]
