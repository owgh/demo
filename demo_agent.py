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
ASSET_VERSION = "2.1.0"

THEME_COLOR = {"care": "#edf1ee", "trades": "#1c3fa8", "food": "#fff4e6", "barber": "#122033", "salon": "#f8e7e2",
               "pro": "#f5f6f8", "gym": "#0e1630", "kids": "#ffffff", "pets": "#ecf5f2", "florist": "#fbf0ee", "shop": "#f3f1f7"}

HOOK_FEATURE = sd.HOOK_FEATURE
GALLERY_TITLE = {"trades": "Our work", "food": "From our kitchen", "florist": "Recent arrangements", "gym": "Inside the gym"}


def load_template() -> str:
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def _phone_short(phone):
    return phone.strip() or "Contact us"


def page_tokens(site: dict, full_name: str) -> dict:
    """Template tokens for one site (demo or live). Uses the site's own phone and address."""
    phone = (site.get("phone") or "").strip()
    phone_raw = re.sub(r"[^0-9+]", "", phone)
    hook = site["hook"]
    esc = lambda v: html.escape(str(v), quote=True)
    where = f"{site['street']}, {site['city']}" if site.get("street") and site.get("city") else site.get("city") or ""
    return {
        "THEME": site["theme"],
        "HOOK": hook,
        "THEME_COLOR": THEME_COLOR[site["theme"]],
        "FONTS_URL": esc(sd.fonts_url(site["theme"])),
        "ASSET_V": ASSET_VERSION,
        "PRIMARY_STYLE": f'<style>html[data-theme]{{--primary:{site["primary"]}}}</style>' if site.get("primary") else "",
        "BUSINESS_NAME": esc(full_name),
        "DISPLAY_NAME": esc(site["name"]),
        "HEADLINE": esc(site["headline"]),
        "SUB": esc(site["sub"]),
        "CTA": esc(site["cta"]),
        "WHERE": esc(where),
        "ADDRESS": esc(site["address"]),
        "MAP_Q": esc(re.sub(r"\s+", "+", f"{site['name']}, {site['address']}").replace("&", "%26").replace("#", "%23")),
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
        "BRAND_LOGO": "",
        "HEAD_EXTRA": "",
        "FOOTER_EXTRA": "",
        "GALLERY_TITLE": GALLERY_TITLE.get(site["theme"], "Take a look inside"),
    }


def strip_location(page: str) -> str:
    """For businesses without an address: no map, no directions, no location line."""
    page = re.sub(r'\s*<div class="map">.*?</iframe>\s*</div>', "", page, flags=re.S)
    page = re.sub(r'\s*<a class="btn btn-primary" href="https://www.google.com/maps/dir/[^"]*"[^>]*>Get directions</a>', "", page)
    page = re.sub(r'\s*<address class="addr"></address>', "", page)
    page = re.sub(r'\s*<p class="where">.*?</p>', "", page, flags=re.S)
    return page.replace(">Come and see us<", ">Hours and contact<")


def generate_demo(lead: dict, template: str, mode: str = "lead", slug: str = None) -> str:
    """Generate the full HTML for one demo. mode: lead (cold email), job (job post reply), example (portfolio)."""
    name = lead.get("business_name", "").strip()
    site = sd.build_site(lead, slug or make_slug(name), {"price": SITE_PRICE, "days": DELIVERY_DAYS})
    page = render_template(template, page_tokens(site, name))
    if not site["address"]:
        page = strip_location(page)
    if mode != "lead":
        page = page.replace('href="assets/', 'href="../assets/').replace('src="assets/', 'src="../assets/')
    # offer bar + noindex (see offer_bar.py)
    return offer_patch(page, site["name"] if mode != "lead" else name, mode=mode)


def build_custom(name: str, category: str, slug: str, mode: str, city: str = "", phone: str = "") -> str:
    """A demo for a business that isn't in the lead log: a job post or a portfolio example.
    Written to demos/jobs/<slug>.html or demos/examples/<slug>.html; returns the public URL."""
    folder = {"job": "jobs", "example": "examples"}[mode]
    lead = {"business_name": name, "category": category, "address": "", "phone": phone, "city": city}
    os.makedirs(os.path.join(DEMOS_DIR, folder), exist_ok=True)
    with open(os.path.join(DEMOS_DIR, folder, f"{slug}.html"), "w", encoding="utf-8") as f:
        f.write(generate_demo(lead, load_template(), mode=mode, slug=slug))
    return f"{GITHUB_PAGES_BASE}/demos/{folder}/{slug}.html"


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
    if "--custom" in args:
        # python3 demo_agent.py --custom --mode job --name "Bella's Bakery" --category bakery --slug for-bellas-bakery [--city Austin]
        opt = lambda k, dflt="": args[args.index(k) + 1] if k in args else dflt
        print(build_custom(opt("--name"), opt("--category"), opt("--slug") or make_slug(opt("--name")), opt("--mode", "job"), opt("--city"), opt("--phone")))
    else:
        run(category_filter=category_filter, lead_filter=lead_filter, rebuild="--rebuild" in args)
