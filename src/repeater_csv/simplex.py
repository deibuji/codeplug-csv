"""Static simplex channel and zone builders."""

from __future__ import annotations

from .models import AnytoneChannel, AnytoneZone


def _mhz_str(freq: float) -> str:
    """Format a frequency in MHz to 5 decimal places."""
    return f"{freq:.5f}"


# ---------- Hotspot ----------


def hotspot_zone() -> AnytoneZone:
    """DMR hotspot channels on UK-allocated frequencies 434.000 and 438.800 MHz."""
    channels = [
        AnytoneChannel(
            name="HS 434 SIMPLEX",
            rx_freq=_mhz_str(434.000),
            tx_freq=_mhz_str(434.000),
            channel_type="D-Digital",
            bandwidth="12.5K",
            color_code=1,
            slot=1,
            contact="Local",
        ),
        AnytoneChannel(
            name="HS 438 SIMPLEX",
            rx_freq=_mhz_str(438.800),
            tx_freq=_mhz_str(438.800),
            channel_type="D-Digital",
            bandwidth="12.5K",
            color_code=1,
            slot=1,
            contact="Local",
        ),
        AnytoneChannel(
            name="HS RPT TS1",
            rx_freq=_mhz_str(434.000),
            tx_freq=_mhz_str(438.800),
            channel_type="D-Digital",
            bandwidth="12.5K",
            color_code=1,
            slot=1,
            contact="Local",
        ),
        AnytoneChannel(
            name="HS RPT TS2",
            rx_freq=_mhz_str(434.000),
            tx_freq=_mhz_str(438.800),
            channel_type="D-Digital",
            bandwidth="12.5K",
            color_code=1,
            slot=2,
            contact="Local",
        ),
    ]
    return AnytoneZone(name="HOTSPOT", channels=channels)


# ---------- VHF FM Simplex ----------


def vhf_fm_simplex_zone() -> AnytoneZone:
    """V16-V46: 145.200-145.575 MHz, 12.5K FM. V40 is the calling channel."""
    channels = []
    for i in range(16, 47):
        freq = 145.200 + (i - 16) * 0.0125
        freq_str = _mhz_str(freq)
        name = f"V{i} CALL" if i == 40 else f"V{i}"
        channels.append(
            AnytoneChannel(
                name=name,
                rx_freq=freq_str,
                tx_freq=freq_str,
                channel_type="A-Analog",
                bandwidth="12.5K",
            )
        )
    return AnytoneZone(name="VHF FM SIMPLEX", channels=channels)


# ---------- UHF FM Simplex ----------


def uhf_fm_simplex_zone() -> AnytoneZone:
    """U272-U288: 433.400-433.600 MHz, 12.5K FM. U280 is the calling channel."""
    channels = []
    for i in range(272, 289):
        freq = 433.400 + (i - 272) * 0.0125
        freq_str = _mhz_str(freq)
        name = f"U{i} CALL" if i == 280 else f"U{i}"
        channels.append(
            AnytoneChannel(
                name=name,
                rx_freq=freq_str,
                tx_freq=freq_str,
                channel_type="A-Analog",
                bandwidth="12.5K",
            )
        )
    return AnytoneZone(name="UHF FM SIMPLEX", channels=channels)


# ---------- VHF DV Simplex ----------


def vhf_dv_simplex_zone() -> AnytoneZone:
    """Single channel: 144.6125 MHz, DMR CC1 TS1."""
    freq_str = _mhz_str(144.6125)
    ch = AnytoneChannel(
        name="2M DV CALL",
        rx_freq=freq_str,
        tx_freq=freq_str,
        channel_type="D-Digital",
        bandwidth="12.5K",
        color_code=1,
        slot=1,
        contact="Local",
    )
    return AnytoneZone(name="VHF DV SIMPLEX", channels=[ch])


# ---------- UHF DV Simplex ----------


def uhf_dv_simplex_zone() -> AnytoneZone:
    """DH1-DH8: 438.5875-438.6750 MHz, DMR CC1 TS1. DH3 is the calling channel."""
    channels = []
    for i in range(1, 9):
        freq = 438.5875 + (i - 1) * 0.0125
        freq_str = _mhz_str(freq)
        name = f"DH{i} CALL" if i == 3 else f"DH{i}"
        channels.append(
            AnytoneChannel(
                name=name,
                rx_freq=freq_str,
                tx_freq=freq_str,
                channel_type="D-Digital",
                bandwidth="12.5K",
                color_code=1,
                slot=1,
                contact="Local",
            )
        )
    return AnytoneZone(name="UHF DV SIMPLEX", channels=channels)


# ---------- PMR446 ----------


def pmr446_zone() -> AnytoneZone:
    """PMR 1-16: 446.00625-446.19375 MHz, 12.5K FM, TX prohibited."""
    channels = []
    for i in range(1, 17):
        freq = 446.00625 + (i - 1) * 0.0125
        freq_str = _mhz_str(freq)
        channels.append(
            AnytoneChannel(
                name=f"PMR {i}",
                rx_freq=freq_str,
                tx_freq=freq_str,
                channel_type="A-Analog",
                bandwidth="12.5K",
                tx_prohibit="On",
            )
        )
    return AnytoneZone(name="PMR446", channels=channels)


# ---------- ISS ----------


def iss_zone() -> AnytoneZone:
    """ISS channels: 5 doppler downlinks, cross-band repeater up/down."""
    doppler = [
        ("ISS RISE", 145.8050),
        ("ISS HIGH", 145.8025),
        ("ISS OVER", 145.8000),
        ("ISS LOW", 145.7975),
        ("ISS SET", 145.7950),
    ]
    uplink = _mhz_str(145.200)
    channels = []
    for name, dl_freq in doppler:
        channels.append(
            AnytoneChannel(
                name=name,
                rx_freq=_mhz_str(dl_freq),
                tx_freq=uplink,
                channel_type="A-Analog",
                bandwidth="25K",
            )
        )

    # Cross-band repeater uplink (145.990, CTCSS 67.0 encode)
    rpt_up_freq = _mhz_str(145.990)
    channels.append(
        AnytoneChannel(
            name="ISS RPT UP",
            rx_freq=rpt_up_freq,
            tx_freq=rpt_up_freq,
            channel_type="A-Analog",
            bandwidth="25K",
            ctcss_encode="67.0",
        )
    )

    # Cross-band repeater downlink (437.800)
    rpt_dn_freq = _mhz_str(437.800)
    channels.append(
        AnytoneChannel(
            name="ISS RPT DN",
            rx_freq=rpt_dn_freq,
            tx_freq=rpt_dn_freq,
            channel_type="A-Analog",
            bandwidth="25K",
        )
    )

    return AnytoneZone(name="ISS", channels=channels)


# ---------- Marine VHF ----------

# ITU Marine VHF simplex channels (ship TX = coast TX).
# Excludes Ch 70 (DSC), 75/76 (guard bands).
_MARINE_CHANNELS: list[tuple[int, float]] = [
    (6, 156.300),
    (8, 156.400),
    (9, 156.450),
    (10, 156.500),
    (11, 156.550),
    (12, 156.600),
    (13, 156.650),
    (14, 156.700),
    (15, 156.750),
    (16, 156.800),
    (17, 156.850),
    (27, 157.350),
    (67, 156.375),
    (68, 156.425),
    (69, 156.475),
    (71, 156.575),
    (72, 156.625),
    (73, 156.675),
    (74, 156.725),
    (77, 156.875),
    (87, 157.375),
    (88, 157.425),
]


def marine_vhf_zone() -> AnytoneZone:
    """22 simplex marine VHF channels, TX prohibited. Ch 16 is the calling channel."""
    channels = []
    for ch_num, freq in _MARINE_CHANNELS:
        freq_str = _mhz_str(freq)
        name = f"MAR {ch_num} CALL" if ch_num == 16 else f"MAR {ch_num:02d}"
        channels.append(
            AnytoneChannel(
                name=name,
                rx_freq=freq_str,
                tx_freq=freq_str,
                channel_type="A-Analog",
                bandwidth="25K",
                tx_prohibit="On",
            )
        )
    return AnytoneZone(name="MARINE VHF", channels=channels)


# ---------- Public API ----------


def get_static_zones() -> list[AnytoneZone]:
    """Return all static simplex/utility zones."""
    return [
        hotspot_zone(),
        vhf_fm_simplex_zone(),
        uhf_fm_simplex_zone(),
        vhf_dv_simplex_zone(),
        uhf_dv_simplex_zone(),
        pmr446_zone(),
        iss_zone(),
        marine_vhf_zone(),
    ]
