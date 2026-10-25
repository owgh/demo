#!/usr/bin/env python3
"""
UI/UX Demo Agent
Builds a personal, working demo website for every cold-email lead.

Design v2 (Oct 2026): one page skeleton (templates/v2.html), a theme per kind
of business, and one working "hook" in the hero (body map, instant estimate,
online ordering, booking, calculators, plan finder, class schedule, bouquet
builder). Styles and scripts live in demos/assets/v2/, shared by every demo,
so a design fix reaches all demos at once. See site_data.py.

Usage:
  python3 demo_agent.py                           # new demos for queued and sent leads
  python3 demo_agent.py --rebuild                 # rebuild every existing demo in the new design
  python3 demo_agent.py --category barbershop     # one category only
  python3 demo_agent.py --lead "Sharp Barbershop" # single lead by name
"""

import html
import os
import re
import sys

from config import LEADS_CSV, DEMOS_DIR, TEMPLATES_DIR, GITHUB_USERNAME, GITHUB_PAGES_REPO, SENDER_NAME
from utils import make_slug, render_template, filter_leads, read_leads
from offer_bar import patch as offer_patch, SITE_PRICE, DELIVERY_DAYS
import site_data as sd

TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, "v2.html")
GITHUB_PAGES_BASE = f"https://{GITHUB_USERNAME}.github.io/{GITHUB_PAGES_REPO}"
ASSET_VERSION = "2.0.0"

THEME_COLOR = {"care": "#edf1ee", "trades": "#1c3fa8", "food": "#fff4e6", "barber": "#122033", "salon": "#f8e7e2",
               "pro": "#f5f6f8", "gym": "#0e1630", "kids": "#ffffff", "pets": "#ecf5f2", "florist": "#fbf0ee", "shop": "#f3f1f7"}

HOOK_FEATURE = {
    "bodymap": "A body map that turns “it hurts here” into a booked visit",
    "estimate": "Instant price estimates that turn into booked visits",
    "order": "Online ordering for pickup, with live order status",
    "booking": "Online booking with real open times and calendar invites",
    "mortgage": "A payment calculator that books calls",
    "taxday": "A tax-deadline countdown and checklist that books appointments",
    "intake": "A three-question form that books free consultations",
    "quiz": "A plan finder that turns visitors into first appointments",
    "timetable": "A class schedule people can reserve from",
    "bouquet": "A bouquet builder that takes delivery orders",
}


def load_template() -> str:
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def _phone_short(phone):
    return phone.strip() or "Contact us"


def generate_demo(lead: dict, template: str) -> str:
    """Generate the full HTML for one lead."""
    name = lead.get("business_name", "").strip()
    slug = make_slug(name)
    offer = {"price": SITE_PRICE, "days": DELIVERY_DAYS}
    site = sd.build_site(lead, slug, offer)
    phone = (lead.get("phone") or "").strip()
    phone_raw = re.sub(r"[^0-9+]", "", phone)
    hook = site["hook"]
    esc = lambda v: html.escape(str(v), quote=True)

    where = f"{site['street']}, {site['city']}" if site["street"] else site["city"]
    tokens = {
        "THEME": site["theme"],
        "HOOK": hook,
        "THEME_COLOR": THEME_COLOR[site["theme"]],
        "FONTS_URL": esc(sd.fonts_url(site["theme"])),
        "ASSET_V": ASSET_VERSION,
        "PRIMARY_STYLE": f'<style>html[data-theme]{{--primary:{site["primary"]}}}</style>' if site.get("primary") else "",
        "BUSINESS_NAME": esc(name),
        "HEADLINE": esc(site["headline"]),
        "SUB": esc(site["sub"]),
        "CTA": esc(site["cta"]),
        "WHERE": esc(where),
        "ADDRESS": esc(site["address"]),
        "MAP_Q": esc(re.sub(r"\s+", "+", f"{name}, {site['address']}").replace("&", "%26").replace("#", "%23")),
        "CALL_HREF": esc(f"tel:{phone_raw}" if phone_raw else "#visit"),
        "CALL_TEXT": esc(f"Call {phone}" if phone else "Contact us"),
        "PHONE_SHORT": esc(_phone_short(phone)),
        "SERVICES_LABEL": "Menu" if hook == "order" else "Services",
        "SERVICES_TITLE": "The menu" if hook == "order" else "Services and prices",
        "SERVICES_SUB": ("Tap to add. Your order is ready when you arrive." if hook == "order"
                         else "Book a free call about any of these." if hook in ("intake", "mortgage")
                         else "Pick one and book it in under a minute."),
        "ABOUT": esc(site["about"]),
        "HOOK_FEATURE": esc(HOOK_FEATURE.get(hook, HOOK_FEATURE["booking"])),
        "SITE_PRICE": str(SITE_PRICE),
        "DELIVERY_DAYS": str(DELIVERY_DAYS),
        "SENDER_NAME": esc(SENDER_NAME),
        "SITE_JSON": sd.site_json(site),
    }
    # offer bar + noindex (see offer_bar.py)
    return offer_patch(render_template(template, tokens), name)


def _pick_leads(rows, rebuild):
    """Queued/sent leads with an email, plus (when rebuilding) every lead that already has a demo."""
    leads = filter_leads(rows)
    if rebuild:
        existing = {f[:-5] for f in os.listdir(DEMOS_DIR) if f.endswith(".html")}
        seen = {make_slug(r.get("business_name", "")) for r in leads}
        for r in rows:
            sl = make_slug(r.get("business_name", ""))
            if sl in existing and sl not in seen:
                leads.append(r)
                seen.add(sl)
    out, seen = [], set()
    for r in leads:  # one demo per business name
        sl = make_slug(r.get("business_name", ""))
        if sl and sl not in seen:
            seen.add(sl)
            out.append(r)
    return out


def run(category_filter: str = None, lead_filter: str = None, rebuild: bool = False):
    os.makedirs(DEMOS_DIR, exist_ok=True)
    template = load_template()
    rows = read_leads(LEADS_CSV)
    leads = _pick_leads(rows, rebuild)

    if category_filter:
        leads = [r for r in leads if r.get("category", "").lower() == category_filter.lower()]
    if lead_filter:
        leads = [r for r in leads if r.get("business_name", "").lower() == lead_filter.lower()]

    if not leads:
        print("No matching leads found.")
        return

    print(f"\n{'Rebuilding' if rebuild else 'Generating'} demos for {len(leads)} leads...\n")
    generated = skipped = 0
    for lead in leads:
        name = lead.get("business_name", "")
        slug = make_slug(name)
        out_path = os.path.join(DEMOS_DIR, f"{slug}.html")
        if os.path.exists(out_path) and not rebuild and not lead_filter:
            skipped += 1
            continue
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(generate_demo(lead, template))
        print(f"  [done] {name}  ->  {GITHUB_PAGES_BASE}/demos/{slug}.html")
        generated += 1

    print(f"\n{'─'*52}\n  Generated : {generated}\n  Skipped   : {skipped} (already had a demo)\n{'─'*52}")
    if generated:
        ui_dir = os.path.dirname(os.path.abspath(__file__))
        print(f'\nPublish: git -C "{ui_dir}" add demos && git -C "{ui_dir}" commit -m "Demos" && git -C "{ui_dir}" push\n')


if __name__ == "__main__":
    args = sys.argv[1:]
    category_filter = lead_filter = None
    if "--category" in args:
        category_filter = args[args.index("--category") + 1]
    if "--lead" in args:
        lead_filter = args[args.index("--lead") + 1]
    run(category_filter=category_filter, lead_filter=lead_filter, rebuild="--rebuild" in args)
