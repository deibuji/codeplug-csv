"""Tests for the BrandMeister talkgroup extraction and RadioID download."""

from __future__ import annotations

import logging
import pytest
import asyncio
import httpx
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from codeplug_csv.config import NON_UK_CURATED_IDS, UK_TG_PREFIX
from codeplug_csv.extract import BrandMeisterClient, RadioIDClient


class TestBrandMeisterFilterAndParse:
    def test_filters_out_non_curated_ids(self, sample_bm_data):
        talkgroups = BrandMeisterClient._filter_and_parse(sample_bm_data)
        ids = {tg.radio_id for tg in talkgroups}
        assert 12345 not in ids
        assert 99999 not in ids
        assert 234000 not in ids

    def test_returns_correct_count(self, sample_bm_data):
        talkgroups = BrandMeisterClient._filter_and_parse(sample_bm_data)
        assert len(talkgroups) == 34

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
        tg4000 = next(tg for tg in talkgroups if tg.radio_id == 4000)
        assert tg4000.call_type == "Private Call"
        tg9990 = next(tg for tg in talkgroups if tg.radio_id == 9990)
        assert tg9990.call_type == "Private Call"
        tg234997 = next(tg for tg in talkgroups if tg.radio_id == 234997)
        assert tg234997.call_type == "Private Call"

    def test_group_call_ids(self, sample_bm_data):
        talkgroups = BrandMeisterClient._filter_and_parse(sample_bm_data)
        for tg in talkgroups:
            if tg.radio_id not in {4000, 9990, 234997}:
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
        expected = {9, 235} | NON_UK_CURATED_IDS
        assert ids == expected

    def test_invalid_keys_skipped(self):
        data = {"abc": "Invalid", "9": "Local"}
        talkgroups = BrandMeisterClient._filter_and_parse(data)
        ids = {tg.radio_id for tg in talkgroups}
        assert ids == NON_UK_CURATED_IDS
        assert any(tg.radio_id == 9 and tg.name == "Local" for tg in talkgroups)

    def test_empty_response_returns_empty_list(self, caplog):
        with caplog.at_level(logging.WARNING):
            talkgroups = BrandMeisterClient._filter_and_parse({})
        assert talkgroups == []
        assert "Empty response" in caplog.text

    def test_uk_prefix_tgs_included_dynamically(self, sample_bm_data):
        talkgroups = BrandMeisterClient._filter_and_parse(sample_bm_data)
        ids = {tg.radio_id for tg in talkgroups}
        for tg_id in [
            23500,
            23510,
            23520,
            23530,
            23540,
            23550,
            23560,
            23570,
            23580,
            23590,
        ]:
            assert tg_id in ids

    def test_non_235_prefix_excluded(self):
        data = {"234000": "Some 234 TG", "23599": "A UK TG", "9": "Local"}
        talkgroups = BrandMeisterClient._filter_and_parse(data)
        ids = {tg.radio_id for tg in talkgroups}
        assert 234000 not in ids
        assert 23599 in ids

    def test_uk_prefix_not_backfilled(self, caplog):
        data = {"9": "Local"}
        with caplog.at_level(logging.INFO):
            talkgroups = BrandMeisterClient._filter_and_parse(data)
        ids = {tg.radio_id for tg in talkgroups}
        uk_prefix_ids = {tg_id for tg_id in ids if str(tg_id).startswith(UK_TG_PREFIX)}
        assert uk_prefix_ids == set()


class TestBrandMeisterFetchTalkgroups:
    @pytest.mark.asyncio
    async def test_fetch_talkgroups_returns_parsed_talkgroups(self, sample_bm_data):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(return_value=sample_bm_data)

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.aclose = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("codeplug_csv.extract.httpx.AsyncClient", return_value=mock_client):
            async with BrandMeisterClient() as client:
                talkgroups = await client.fetch_talkgroups()

        assert len(talkgroups) == 34
        tg9 = next(tg for tg in talkgroups if tg.radio_id == 9)
        assert tg9.name == "Local"

    @pytest.mark.asyncio
    async def test_fetch_talkgroups_raises_without_context(self):
        client = BrandMeisterClient()
        with pytest.raises(RuntimeError, match="async context manager"):
            await client.fetch_talkgroups()

    @pytest.mark.asyncio
    async def test_fetch_talkgroups_propagates_http_error(self):
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Bad Request",
                request=MagicMock(),
                response=MagicMock(status_code=400),
            )
        )
        mock_client.aclose = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("codeplug_csv.extract.httpx.AsyncClient", return_value=mock_client):
            with pytest.raises(httpx.HTTPStatusError):
                async with BrandMeisterClient() as client:
                    await client.fetch_talkgroups()


class TestRadioIDClient:
    @pytest.mark.asyncio
    async def test_download_writes_file(self, tmp_path):
        sample_csv = b"RADIO_ID,CALLSIGN,FIRST_NAME,LAST_NAME\n1234567,M0ABC,John,Doe\n"
        dest = tmp_path / "user.csv"

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()

        async def mock_aiter_bytes():
            yield sample_csv

        mock_response.aiter_bytes = MagicMock(return_value=mock_aiter_bytes())

        mock_stream_cm = AsyncMock()
        mock_stream_cm.__aenter__.return_value = mock_response

        mock_client_cm = AsyncMock()
        mock_client_cm.stream = MagicMock(return_value=mock_stream_cm)

        with patch(
            "codeplug_csv.extract.httpx.AsyncClient", return_value=mock_client_cm
        ):
            async with RadioIDClient(url="https://fakeurl.com") as client:
                await client.download(dest)

        assert dest.exists()
        assert dest.read_bytes() == sample_csv
