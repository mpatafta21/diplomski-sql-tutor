"""Testovi za extract_json helper."""

import pytest

from scripts.lib.json_extract import extract_json, JsonExtractionError


def test_extracts_plain_json():
    text = '{"foo": "bar"}'
    assert extract_json(text) == '{"foo": "bar"}'


def test_extracts_from_markdown_codeblock():
    text = '```json\n{"foo": "bar"}\n```'
    assert extract_json(text) == '{"foo": "bar"}'


def test_extracts_from_unlabeled_codeblock():
    text = '```\n{"foo": "bar"}\n```'
    assert extract_json(text) == '{"foo": "bar"}'


def test_extracts_with_surrounding_text():
    text = 'Evo zadatka:\n\n```json\n{"foo": "bar"}\n```\n\nNadam se da je OK.'
    assert extract_json(text) == '{"foo": "bar"}'


def test_raises_when_no_json_found():
    with pytest.raises(JsonExtractionError):
        extract_json("nema JSON-a ovdje")
