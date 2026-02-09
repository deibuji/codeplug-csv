"""Tests for the BrandMeister talkgroup extraction and RadioID download."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

from codeplug_csv.config import CURATED_TALKGROUP_IDS
from codeplug_csv.extract import BrandMeisterClient, RadioIDClient


class TestBrandMeisterFilterAndParse:
    def test_filters_out_non_curated_ids(self, sample_bm_data):
        talkgroups = BrandMeisterClient._filter_and_parse(sample_bm_data)
        ids = {tg.radio_id for tg in talkgroups}
        assert 12345 not in ids
        assert 99999 not in ids

    def test_returns_correct_count(self, sample_bm_data):
        talkgroups = BrandMeisterClient._filter_and_parse(sample_bm_data)
        assert len(talkgroups) == 23

    def test_sorted_by_radio_id(self, sample_bm_data):
        talkgroups = BrandMeisterClient._filter_and_parse(sample_bm_data)
        ids = [tg.radio_id for tg in talkgroups]
        assert ids == sorted(ids)

    def test_tg9_always_named_local(self, sample_bm_data):
        talkgroups = BrandMeisterClient._filter_and_parse(sample_bm_data)
        tg9 = next(tg for tg in talkgroups if tg.radio_id == 9)
        assert tg9.name == "Local"

    def test_names_truncated_to_16_chars(self, sample_bm_data):
        talkgroups = BrandMeisterClient._filter_and_parse(sample_bm_data)
        for tg in talkgroups:
            assert len(tg.name) <= 16

    def test_private_call_ids(self, sample_bm_data):
        talkgroups = BrandMeisterClient._filter_and_parse(sample_bm_data)
        tg9990 = next(tg for tg in talkgroups if tg.radio_id == 9990)
        assert tg9990.call_type == "Private Call"
        tg234997 = next(tg for tg in talkgroups if tg.radio_id == 234997)
        assert tg234997.call_type == "Private Call"

    def test_group_call_ids(self, sample_bm_data):
        talkgroups = BrandMeisterClient._filter_and_parse(sample_bm_data)
        for tg in talkgroups:
            if tg.radio_id not in {9990, 234997}:
                assert tg.call_type == "Group Call"

    def test_all_call_alert_none(self, sample_bm_data):
        talkgroups = BrandMeisterClient._filter_and_parse(sample_bm_data)
        for tg in talkgroups:
            assert tg.call_alert == "None"

    def test_missing_curated_ids_added_as_fallback(self, caplog):
        partial_data = {"9": "Local", "235": "UK Wide"}
        with caplog.at_level(logging.INFO):
            talkgroups = BrandMeisterClient._filter_and_parse(partial_data)
        assert "not in API response" in caplog.text
        ids = {tg.radio_id for tg in talkgroups}
        assert ids == CURATED_TALKGROUP_IDS

    def test_invalid_keys_skipped(self):
        data = {"abc": "Invalid", "9": "Local"}
        talkgroups = BrandMeisterClient._filter_and_parse(data)
        ids = {tg.radio_id for tg in talkgroups}
        assert ids == CURATED_TALKGROUP_IDS
        assert any(tg.radio_id == 9 and tg.name == "Local" for tg in talkgroups)

    def test_empty_response_returns_empty_list(self, caplog):
        with caplog.at_level(logging.WARNING):
            talkgroups = BrandMeisterClient._filter_and_parse({})
        assert talkgroups == []
        assert "Empty response" in caplog.text


class TestRadioIDClient:
    def test_download_writes_file(self, tmp_path):
        sample_csv = b"RADIO_ID,CALLSIGN,FIRST_NAME,LAST_NAME\n1234567,M0ABC,John,Doe\n"
        mock_resp = MagicMock()
        mock_resp.iter_content.return_value = [sample_csv]
        mock_resp.raise_for_status = MagicMock()

        with patch("codeplug_csv.extract.requests.get", return_value=mock_resp) as mock_get:
            dest = tmp_path / "user.csv"
            result = RadioIDClient().download(dest)

            mock_get.assert_called_once_with(
                "https://www.radioid.net/static/user.csv",
                stream=True,
                timeout=60,
            )
            assert result == dest
            assert dest.read_bytes() == sample_csv

    def test_download_streams_multiple_chunks(self, tmp_path):
        chunks = [b"RADIO_ID,CALLSIGN\n", b"1234567,M0ABC\n"]
        mock_resp = MagicMock()
        mock_resp.iter_content.return_value = chunks
        mock_resp.raise_for_status = MagicMock()

        with patch("codeplug_csv.extract.requests.get", return_value=mock_resp):
            dest = tmp_path / "user.csv"
            RadioIDClient().download(dest)
            assert dest.read_bytes() == b"RADIO_ID,CALLSIGN\n1234567,M0ABC\n"

    def test_download_raises_on_http_error(self, tmp_path):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("404 Not Found")

        with patch("codeplug_csv.extract.requests.get", return_value=mock_resp):
            dest = tmp_path / "user.csv"
            try:
                RadioIDClient().download(dest)
                assert False, "Expected exception"
            except Exception as e:
                assert "404" in str(e)
