import re
import csv
import os


def make_slug(name: str) -> str:
    """Convert a business name to a URL-safe filename slug."""
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def render_template(template: str, tokens: dict) -> str:
    """Replace {{TOKEN}} placeholders with values from tokens dict.
    Missing tokens are replaced with empty string."""
    def replacer(match):
        key = match.group(1)
        return tokens.get(key, "")
    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", replacer, template)


def filter_leads(rows: list) -> list:
    """Return only rows with status dry_run or sent that have a contact email."""
    return [
        r for r in rows
        if r.get("status") in ("dry_run", "sent")
        and r.get("contact_email", "").strip()
    ]


def read_leads(csv_path: str) -> list:
    """Read all rows from leads_log.csv."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Leads file not found: {csv_path}")
    with open(csv_path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build_tokens(lead: dict, ai_copy: dict) -> dict:
    """Build the full token dict for template rendering from a lead row + AI copy."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from category_config import CATEGORY_CONFIG, DEFAULT_CATEGORY
    from config import SENDER_EMAIL, YOUR_PHONE

    name = lead.get("business_name", "")
    category = lead.get("category", "").strip().lower()
    phone = lead.get("phone", "")
    address = lead.get("address", "")

    cfg = CATEGORY_CONFIG.get(category, DEFAULT_CATEGORY)
    s1, s2, s3 = cfg["services"]
    about1, about2 = cfg["about"]

    phone_raw = re.sub(r"[^0-9]", "", phone)

    return {
        "BUSINESS_NAME": name,
        "TAGLINE": ai_copy.get("tagline", ""),
        "SUBHEADLINE": ai_copy.get("subheadline", ""),
        "PHONE": phone,
        "PHONE_RAW": phone_raw,
        "ADDRESS": address,
        "CITY": "Ottawa",
        "HERO_COLOR": cfg["color"],
        "SERVICE_1": s1,
        "SERVICE_2": s2,
        "SERVICE_3": s3,
        "SERVICE_1_LOWER": s1.lower(),
        "SERVICE_2_LOWER": s2.lower(),
        "SERVICE_3_LOWER": s3.lower(),
        "ABOUT_1": about1.format(name=name),
        "ABOUT_2": about2,
        "SENDER_EMAIL": SENDER_EMAIL,
        "YOUR_PHONE": YOUR_PHONE,
        "YOUR_PHONE_RAW": re.sub(r"[^0-9]", "", YOUR_PHONE),
    }
