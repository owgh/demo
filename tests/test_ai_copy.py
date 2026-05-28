import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from ai_copy import get_ai_copy, FALLBACK_COPY


def test_get_ai_copy_returns_dict_with_keys():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"tagline": "Ottawa Cuts Done Right", "subheadline": "Sharp Barbershop delivers premium haircuts in Ottawa."}')]

    with patch("ai_copy.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_response
        result = get_ai_copy("Sharp Barbershop", "barbershop")

    assert "tagline" in result
    assert "subheadline" in result
    assert len(result["tagline"]) > 0
    assert len(result["subheadline"]) > 0


def test_get_ai_copy_falls_back_on_api_error():
    with patch("ai_copy.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.side_effect = Exception("API error")
        result = get_ai_copy("Sharp Barbershop", "barbershop")

    assert result["tagline"] == FALLBACK_COPY["barbershop"]["tagline"]
    assert result["subheadline"] == FALLBACK_COPY["barbershop"]["subheadline"]


def test_get_ai_copy_falls_back_on_invalid_json():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="not valid json at all")]

    with patch("ai_copy.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.return_value = mock_response
        result = get_ai_copy("Sharp Barbershop", "barbershop")

    assert "tagline" in result
    assert "barbershop" in result["subheadline"].lower() or "ottawa" in result["subheadline"].lower()


def test_fallback_used_for_unknown_category():
    with patch("ai_copy.anthropic.Anthropic") as MockClient:
        MockClient.return_value.messages.create.side_effect = Exception("fail")
        result = get_ai_copy("Some Biz", "unknown_category")

    assert result["tagline"] == "Professional Services in Ottawa"
    assert "Ottawa" in result["subheadline"]
