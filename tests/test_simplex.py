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
        assert zone.name == "VHF FM SMPLX"

    def test_channel_count(self):
        zone = vhf_fm_simplex_zone()
        assert len(zone.channels) == 30

    def test_first_channel_freq(self):
        zone = vhf_fm_simplex_zone()
        assert zone.channels[0].rx_freq == "145.20000"

    def test_last_channel_freq(self):
        zone = vhf_fm_simplex_zone()
        assert zone.channels[-1].rx_freq == "145.56250"

    def test_calling_channel_name(self):
        zone = vhf_fm_simplex_zone()
        # V40 (145.500 MHz) is index 40-16=24
        assert zone.channels[24].name == "V40 145.5000 CL"

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

    def test_excludes_adhoc_repeater_outputs(self):
        zone = vhf_fm_simplex_zone()
        names = {ch.name for ch in zone.channels}
        assert not any(name.startswith("V46 ") for name in names)
        assert not any(name.startswith("V47 ") for name in names)


class TestUhfFmSimplex:
    def test_zone_name(self):
        zone = uhf_fm_simplex_zone()
        assert zone.name == "UHF FM SMPLX"

    def test_channel_count(self):
        zone = uhf_fm_simplex_zone()
        assert len(zone.channels) == 8

    def test_first_channel_freq(self):
        zone = uhf_fm_simplex_zone()
        assert zone.channels[0].rx_freq == "433.40000"

    def test_last_channel_freq(self):
        zone = uhf_fm_simplex_zone()
        assert zone.channels[-1].rx_freq == "433.57500"

    def test_calling_channel_name(self):
        zone = uhf_fm_simplex_zone()
        # U280 (433.500 MHz) is index 4 in the 25 kHz channel list
        assert zone.channels[4].name == "U280 433.5000 CL"

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

    def test_uses_25khz_channel_numbers(self):
        zone = uhf_fm_simplex_zone()
        numbers = [int(ch.name.split()[0][1:]) for ch in zone.channels]
        assert numbers == [272, 274, 276, 278, 280, 282, 284, 286]


class TestVhfDvSimplex:
    def test_zone_name(self):
        zone = vhf_dv_simplex_zone()
        assert zone.name == "VHF DV SMPLX"

    def test_channel_count(self):
        zone = vhf_dv_simplex_zone()
        assert len(zone.channels) == 20

    def test_channel_name(self):
        zone = vhf_dv_simplex_zone()
        assert zone.channels[0].name == "DV 144.6125 CL"

    def test_frequency(self):
        zone = vhf_dv_simplex_zone()
        assert zone.channels[0].rx_freq == "144.61250"

    def test_last_channel_freq(self):
        zone = vhf_dv_simplex_zone()
        assert zone.channels[-1].name == "V45 DV 145.5625"
        assert zone.channels[-1].rx_freq == "145.56250"

    def test_usable_v_channels_are_present(self):
        zone = vhf_dv_simplex_zone()
        names = {ch.name for ch in zone.channels}
        for v in (
            16,
            22,
            24,
            26,
            28,
            29,
            30,
            31,
            32,
            33,
            34,
            35,
            36,
            37,
            38,
            39,
            41,
            43,
            45,
        ):
            assert any(name.startswith(f"V{v} DV ") for name in names), v

    def test_designated_non_simplex_channels_are_excluded(self):
        zone = vhf_dv_simplex_zone()
        names = {ch.name for ch in zone.channels}
        for v in (17, 18, 19, 20, 21, 23, 25, 27, 40, 42, 44):
            assert not any(name.startswith(f"V{v} DV ") for name in names), v

    def test_simplex(self):
        zone = vhf_dv_simplex_zone()
        for ch in zone.channels:
            assert ch.rx_freq == ch.tx_freq

    def test_channel_type(self):
        zone = vhf_dv_simplex_zone()
        for ch in zone.channels:
            assert ch.channel_type == "D-Digital"

    def test_dmr_params(self):
        zone = vhf_dv_simplex_zone()
        for ch in zone.channels:
            assert ch.color_code == 1
            assert ch.slot == 1

    def test_name_lengths(self):
        zone = vhf_dv_simplex_zone()
        for ch in zone.channels:
            assert len(ch.name) <= 16

    def test_all_contact_local(self):
        zone = vhf_dv_simplex_zone()
        for ch in zone.channels:
            assert ch.contact == "Local"


class TestUhfDvSimplex:
    def test_zone_name(self):
        zone = uhf_dv_simplex_zone()
        assert zone.name == "UHF DV SMPLX"

    def test_channel_count(self):
        zone = uhf_dv_simplex_zone()
        assert len(zone.channels) == 16

    def test_first_channel_freq(self):
        zone = uhf_dv_simplex_zone()
        assert zone.channels[0].rx_freq == "438.58750"

    def test_dh_block_frequencies(self):
        zone = uhf_dv_simplex_zone()
        assert [ch.name for ch in zone.channels[:8]] == [
            "DH1 438.5875",
            "DH2 438.6000",
            "DH3 438.6125 CL",
            "DH4 438.6250",
            "DH5 438.6375",
            "DH6 438.6500",
            "DH7 438.6625",
            "DH8 438.6750",
        ]
        assert [ch.rx_freq for ch in zone.channels[:8]] == [
            "438.58750",
            "438.60000",
            "438.61250",
            "438.62500",
            "438.63750",
            "438.65000",
            "438.66250",
            "438.67500",
        ]

    def test_u_dv_copies(self):
        zone = uhf_dv_simplex_zone()
        copies = zone.channels[8:]
        assert [ch.name for ch in copies] == [
            "U272 DV 433.4000",
            "U274 DV 433.4250",
            "U276 DV 433.4500",
            "U278 DV 433.4750",
            "U280 DV 433.5000",
            "U282 DV 433.5250",
            "U284 DV 433.5500",
            "U286 DV 433.5750",
        ]
        assert copies[-1].rx_freq == "433.57500"

    def test_calling_channel_name(self):
        zone = uhf_dv_simplex_zone()
        # DH3 is index 2
        assert zone.channels[2].name == "DH3 438.6125 CL"

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
        assert ch16.name == "MAR 16 CL"

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
        assert total == 123

    def test_zone_names(self):
        zones = get_static_zones()
        names = [z.name for z in zones]
        assert names == [
            "HOTSPOT",
            "VHF FM SMPLX",
            "UHF FM SMPLX",
            "VHF DV SMPLX",
            "UHF DV SMPLX",
            "PMR446",
            "ISS",
            "MARINE VHF",
        ]

    def test_frequency_names_use_four_decimals(self):
        for zone in get_static_zones():
            for channel in zone.channels:
                for token in channel.name.split():
                    if "." not in token or not token[0].isdigit():
                        continue
                    assert len(token.split(".")[1]) == 4, channel.name
