import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils import make_slug, render_template, filter_leads, build_tokens


def test_make_slug_basic():
    assert make_slug("Sharp Barbershop") == "sharp-barbershop"


def test_make_slug_special_chars():
    assert make_slug("The King's Barbershop") == "the-king-s-barbershop"


def test_make_slug_apostrophe_stripped():
    result = make_slug("O'Brien's Plumbing")
    assert result == "o-brien-s-plumbing"


def test_make_slug_leading_trailing():
    assert make_slug("  My Business  ") == "my-business"


def test_render_template_replaces_tokens():
    tmpl = "Hello {{NAME}}, welcome to {{CITY}}."
    result = render_template(tmpl, {"NAME": "Ahmed", "CITY": "Ottawa"})
    assert result == "Hello Ahmed, welcome to Ottawa."


def test_render_template_missing_token_left_blank():
    tmpl = "Hello {{NAME}}, phone: {{PHONE}}."
    result = render_template(tmpl, {"NAME": "Ahmed"})
    assert result == "Hello Ahmed, phone: ."


def test_filter_leads_returns_dry_run_with_email():
    rows = [
        {"status": "dry_run", "contact_email": "info@example.biz", "business_name": "A"},
        {"status": "sent", "contact_email": "hello@shop.ca", "business_name": "B"},
        {"status": "no_email_found", "contact_email": "", "business_name": "C"},
        {"status": "skipped_good_website", "contact_email": "", "business_name": "D"},
        {"status": "dry_run", "contact_email": "", "business_name": "E"},
    ]
    result = filter_leads(rows)
    assert len(result) == 2
    assert result[0]["business_name"] == "A"
    assert result[1]["business_name"] == "B"


def test_build_tokens_barbershop():
    lead = {
        "business_name": "Sharp Barbershop",
        "category": "barbershop",
        "phone": "(613) 422-8484",
        "address": "1016 Merivale Rd, Ottawa, ON K1Z 6A5, Canada",
    }
    ai = {"tagline": "Ottawa Cuts Done Right", "subheadline": "We cut hair."}
    tokens = build_tokens(lead, ai)

    assert tokens["BUSINESS_NAME"] == "Sharp Barbershop"
    assert tokens["TAGLINE"] == "Ottawa Cuts Done Right"
    assert tokens["SUBHEADLINE"] == "We cut hair."
    assert tokens["PHONE"] == "(613) 422-8484"
    assert tokens["ADDRESS"] == "1016 Merivale Rd, Ottawa, ON K1Z 6A5, Canada"
    assert tokens["HERO_COLOR"] == "#0f172a"
    assert tokens["SERVICE_1"] == "Haircut"
    assert tokens["SERVICE_2"] == "Fade"
    assert tokens["SERVICE_3"] == "Beard Trim"
    assert tokens["SERVICE_1_LOWER"] == "haircut"


def test_build_tokens_missing_phone():
    lead = {"business_name": "No Phone Biz", "category": "restaurant", "phone": "", "address": ""}
    ai = {"tagline": "T", "subheadline": "S"}
    tokens = build_tokens(lead, ai)
    assert tokens["PHONE"] == ""
    assert tokens["PHONE_RAW"] == ""


def test_build_tokens_unknown_category_uses_default():
    lead = {"business_name": "Mystery Biz", "category": "mystery", "phone": "", "address": ""}
    ai = {"tagline": "T", "subheadline": "S"}
    tokens = build_tokens(lead, ai)
    assert tokens["HERO_COLOR"] == "#1f2937"
    assert tokens["SERVICE_1"] == "Consultation"
