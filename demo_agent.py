#!/usr/bin/env python3
"""
UI/UX Demo Agent
Generates personalized HTML website demos for cold email leads.

Usage:
  python3 demo_agent.py                           # all dry_run + sent leads
  python3 demo_agent.py --category barbershop     # one category only
  python3 demo_agent.py --lead "Sharp Barbershop" # single lead by name
"""

import sys
import os

from config import LEADS_CSV, DEMOS_DIR, TEMPLATES_DIR, GITHUB_USERNAME, GITHUB_PAGES_REPO
from utils import make_slug, render_template, filter_leads, read_leads, build_tokens
from ai_copy import get_ai_copy


TEMPLATE_FILE = os.path.join(TEMPLATES_DIR, "base.html")
GITHUB_PAGES_BASE = f"https://{GITHUB_USERNAME}.github.io/{GITHUB_PAGES_REPO}"


def load_template() -> str:
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return f.read()


def generate_demo(lead: dict, template: str) -> str:
    """Generate the full HTML for one lead."""
    name = lead.get("business_name", "")
    category = lead.get("category", "").strip().lower()

    print(f"  → Calling Claude for '{name}'...", end=" ", flush=True)
    ai_copy = get_ai_copy(name, category)
    print("✓")

    tokens = build_tokens(lead, ai_copy)
    return render_template(template, tokens)


def run(category_filter: str = None, lead_filter: str = None):
    os.makedirs(DEMOS_DIR, exist_ok=True)
    template = load_template()
    rows = read_leads(LEADS_CSV)
    leads = filter_leads(rows)

    if category_filter:
        leads = [r for r in leads if r.get("category", "").lower() == category_filter.lower()]
    if lead_filter:
        leads = [r for r in leads if r.get("business_name", "").lower() == lead_filter.lower()]

    if not leads:
        print("No matching leads found.")
        return

    print(f"\nGenerating demos for {len(leads)} leads...\n")
    generated = 0
    skipped = 0

    for lead in leads:
        name = lead.get("business_name", "")
        slug = make_slug(name)
        out_path = os.path.join(DEMOS_DIR, f"{slug}.html")

        if os.path.exists(out_path):
            print(f"  [skip] {name} — already exists")
            skipped += 1
            continue

        html = generate_demo(lead, template)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)

        demo_url = f"{GITHUB_PAGES_BASE}/{slug}.html"
        print(f"  [done] {name}")
        print(f"         {demo_url}")
        generated += 1

    print(f"\n{'─'*52}")
    print(f"  Generated : {generated}")
    print(f"  Skipped   : {skipped}")
    print(f"{'─'*52}")

    if generated > 0:
        ui_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"\nTo publish to GitHub Pages, run:")
        print(f'  git -C "{ui_dir}" add demos/')
        print(f'  git -C "{ui_dir}" commit -m "add demos"')
        print(f'  git -C "{ui_dir}" push')
        print(f"\nDemo URLs will be live at:")
        print(f"  {GITHUB_PAGES_BASE}/{{slug}}.html\n")


if __name__ == "__main__":
    category_filter = None
    lead_filter = None

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--category" and i + 1 < len(args):
            category_filter = args[i + 1]
            i += 2
        elif args[i] == "--lead" and i + 1 < len(args):
            lead_filter = args[i + 1]
            i += 2
        else:
            i += 1

    run(category_filter=category_filter, lead_filter=lead_filter)
