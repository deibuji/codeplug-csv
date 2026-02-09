"""Tests for the regions module."""

from __future__ import annotations

from codeplug_csv.regions import locator_to_region


class TestLocatorToRegion:
    # --- Each region ---

    def test_ne(self):
        assert locator_to_region("IO94DR") == "NE"
        assert locator_to_region("IO93GS") == "NE"

    def test_nw(self):
        assert locator_to_region("IO84AA") == "NW"
        # IO83 columns K-X → NW
        assert locator_to_region("IO83WJ") == "NW"
        assert locator_to_region("IO83KA") == "NW"

    def test_se(self):
        assert locator_to_region("IO91LM") == "SE"
        assert locator_to_region("JO00AA") == "SE"
        assert locator_to_region("JO01BB") == "SE"

    def test_sw(self):
        assert locator_to_region("IO70AA") == "SW"
        assert locator_to_region("IO80BB") == "SW"
        assert locator_to_region("IO90CC") == "SW"
        # IO81 columns M-X → SW
        assert locator_to_region("IO81RJ") == "SW"
        assert locator_to_region("IO81MA") == "SW"

    def test_midlands(self):
        assert locator_to_region("IO82AA") == "MIDL"
        assert locator_to_region("IO92BB") == "MIDL"

    def test_east_anglia(self):
        assert locator_to_region("JO02AA") == "E.ANG"
        assert locator_to_region("JO03BB") == "E.ANG"

    def test_london(self):
        # IO91 columns T-X → LONDON
        assert locator_to_region("IO91WM") == "LONDON"
        assert locator_to_region("IO91TA") == "LONDON"
        assert locator_to_region("IO91XA") == "LONDON"

    def test_scotland(self):
        assert locator_to_region("IO85AA") == "SCOT"
        assert locator_to_region("IO77BB") == "SCOT"
        assert locator_to_region("IO67CC") == "SCOT"
        assert locator_to_region("IP90AA") == "SCOT"

    def test_wales(self):
        assert locator_to_region("IO71AA") == "WAL"
        assert locator_to_region("IO72BB") == "WAL"
        assert locator_to_region("IO73CC") == "WAL"
        # IO81 columns A-L → WAL
        assert locator_to_region("IO81AA") == "WAL"
        assert locator_to_region("IO81LA") == "WAL"
        # IO83 columns A-J → WAL
        assert locator_to_region("IO83AA") == "WAL"
        assert locator_to_region("IO83JA") == "WAL"

    def test_northern_ireland(self):
        assert locator_to_region("IO54AA") == "N.IRE"
        assert locator_to_region("IO64BB") == "N.IRE"
        assert locator_to_region("IO65CC") == "N.IRE"
        # IO74 columns A-F → N.IRE
        assert locator_to_region("IO74AA") == "N.IRE"
        assert locator_to_region("IO74FA") == "N.IRE"

    def test_channel_islands(self):
        assert locator_to_region("IN79AA") == "CH.IS"
        assert locator_to_region("IN89BB") == "CH.IS"

    # --- Subsquare boundary cases ---

    def test_io81_boundary(self):
        """IO81: A-L → WAL, M-X → SW."""
        assert locator_to_region("IO81LA") == "WAL"
        assert locator_to_region("IO81MA") == "SW"

    def test_io83_boundary(self):
        """IO83: A-J → WAL, K-X → NW."""
        assert locator_to_region("IO83JA") == "WAL"
        assert locator_to_region("IO83KA") == "NW"

    def test_io91_boundary(self):
        """IO91: A-S → SE, T-X → LONDON."""
        assert locator_to_region("IO91SA") == "SE"
        assert locator_to_region("IO91TA") == "LONDON"

    def test_io74_boundary(self):
        """IO74: A-F → N.IRE, G-X → NW."""
        assert locator_to_region("IO74FA") == "N.IRE"
        assert locator_to_region("IO74GA") == "NW"

    # --- Edge cases ---

    def test_short_locator_returns_default(self):
        assert locator_to_region("IO9") == "SE"
        assert locator_to_region("IO") == "SE"
        assert locator_to_region("I") == "SE"

    def test_empty_locator_returns_default(self):
        assert locator_to_region("") == "SE"

    def test_unknown_grid_returns_default(self):
        assert locator_to_region("ZZ99AA") == "SE"

    def test_four_char_locator_uses_base_only(self):
        """With only 4 chars, no subsquare override is applied."""
        # IO81 default is SW (no 5th char to trigger WAL override)
        assert locator_to_region("IO81") == "SW"

    def test_case_insensitive(self):
        assert locator_to_region("io94dr") == "NE"
        assert locator_to_region("io91wm") == "LONDON"
