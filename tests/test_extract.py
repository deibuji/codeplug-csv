"""Tests for the BrandMeister talkgroup extraction."""

from __future__ import annotations

import logging

from repeater_csv.config import CURATED_TALKGROUP_IDS
from repeater_csv.extract import BrandMeisterClient


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

    def test_missing_curated_ids_logged(self, caplog):
        partial_data = {"9": "Local", "235": "UK Wide"}
        with caplog.at_level(logging.WARNING):
            BrandMeisterClient._filter_and_parse(partial_data)
        assert "not found in API response" in caplog.text

    def test_invalid_keys_skipped(self):
        data = {"abc": "Invalid", "9": "Local"}
        talkgroups = BrandMeisterClient._filter_and_parse(data)
        assert len(talkgroups) == 1
        assert talkgroups[0].radio_id == 9

    def test_empty_response_returns_empty_list(self, caplog):
        with caplog.at_level(logging.WARNING):
            talkgroups = BrandMeisterClient._filter_and_parse({})
        assert talkgroups == []
        assert "Empty response" in caplog.text
