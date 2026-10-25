#!/usr/bin/env python3
"""
Offer bar for demo sites (added Oct 23, 2026).

Every demo gets:
  - a bar at the bottom: "Demo prepared for <Business> by Hussein. Not the official site."
    with the price and a one-tap "yes" (text message) and, once PAY_LINK is set,
    a deposit button
  - <meta name="robots" content="noindex"> so demos stay out of Google
  - the pitch section's old "$500" line updated to the current price

Prices, phone and PAY_LINK come from ../cold-email-agent/config.py.

Usage:
  python3 offer_bar.py            # update every file in demos/ (safe to run again)
  python3 offer_bar.py --check    # only count what would change
"""
import html
import importlib.util
import os
import re
import sys
from urllib.parse import quote

HERE = os.path.dirname(os.path.abspath(__file__))
# Settings come from the Cold Email Agent's config.py when it sits next door (on the Mac),
# otherwise from environment variables (in the cloud), otherwise from the defaults below.
_cold = None
for _path in (os.environ.get("COLD_EMAIL_CONFIG", ""), os.path.join(HERE, "..", "cold-email-agent", "config.py")):
    if _path and os.path.exists(_path):
        _spec = importlib.util.spec_from_file_location("cold_email_config_offer", _path)
        _cold = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_cold)
        break


def _setting(name, default):
    if os.environ.get(name):
        return os.environ[name]
    return getattr(_cold, name, default) if _cold is not None else default


SITE_PRICE = int(_setting("SITE_PRICE", 650))
DELIVERY_DAYS = int(_setting("DELIVERY_DAYS", 7))
PAY_LINK = (_setting("PAY_LINK", "") or "https://square.link/u/FyF7a0uB").strip()  # Square: "Website deposit (50%)", $325
YOUR_PHONE = _setting("YOUR_PHONE", "(343) 597-5450") or ""
SENDER_NAME = _setting("SENDER_NAME", "Hussein") or "Hussein"

START, END = "<!-- OFFER-BAR:START -->", "<!-- OFFER-BAR:END -->"
NOINDEX = '<meta name="robots" content="noindex, nofollow">'

CSS = """<style>
.offer-bar{position:fixed;left:0;right:0;bottom:0;z-index:2147483000;background:#121110;color:#fff;
  font:500 14px/1.35 'DM Sans',system-ui,-apple-system,sans-serif;padding:10px 16px calc(10px + env(safe-area-inset-bottom,0px));
  display:flex;align-items:center;justify-content:center;gap:8px 16px;flex-wrap:wrap;box-shadow:0 -8px 28px rgba(0,0,0,.28);text-align:left}
.offer-bar .ob-text{max-width:620px}
.offer-bar b{font-weight:700}
.offer-bar small{display:block;color:#c9c3b6;font-size:12.5px;margin-top:2px}
.offer-bar .ob-actions{display:flex;gap:8px;flex-wrap:wrap}
.offer-bar a{display:inline-block;background:#fff;color:#121110;text-decoration:none;font-weight:700;font-size:14px;
  padding:10px 16px;border-radius:999px;white-space:nowrap}
.offer-bar a.ob-pay{background:#f0b239}
body{padding-bottom:calc(var(--obh,120px) + 8px)!important}
html,body{overflow-x:hidden;overflow-x:clip}
@media print{.offer-bar{display:none}}
</style>"""


FIT_JS = """<script>(function(){function f(){var b=document.querySelector('.offer-bar');if(b)document.documentElement.style.setProperty('--obh',b.offsetHeight+'px');}window.addEventListener('resize',f);window.addEventListener('load',f);f();})();</script>"""


def _phone_e164(raw):
    digits = re.sub(r"[^0-9]", "", raw or "")
    if len(digits) == 10:
        digits = "1" + digits
    return "+" + digits if digits else ""


def bar_html(business_name):
    name = html.escape(business_name)
    actions = []
    phone = _phone_e164(YOUR_PHONE)
    if phone:
        body = quote(f"Yes, build the website for {business_name}")
        actions.append(f'<a href="sms:{phone}?&amp;body={body}">Text me &ldquo;yes&rdquo;</a>')
    if PAY_LINK:
        actions.append(f'<a class="ob-pay" href="{html.escape(PAY_LINK)}">Pay the 50% deposit</a>')
    return (f'{START}\n{CSS}\n<div class="offer-bar" role="region" aria-label="About this demo">'
            f'<div class="ob-text"><b>Demo prepared for {name}</b> by {html.escape(SENDER_NAME)}, an Ottawa web developer. '
            f'Not the official website.<small>Yours for ${SITE_PRICE}, live in {DELIVERY_DAYS} days, '
            f'online gift cards included.</small></div>'
            f'<div class="ob-actions">{"".join(actions)}</div></div>\n{FIT_JS}\n{END}')


def business_name_from(page):
    m = re.search(r"<title>(.*?)\s+—\s+Ottawa</title>", page, re.S)
    return html.unescape(m.group(1).strip()) if m else ""


def patch(page, business_name=None):
    """Return the page with the offer bar, noindex and current price. Idempotent."""
    name = business_name or business_name_from(page)
    if not name:
        return page
    page = re.sub(re.escape(START) + r".*?" + re.escape(END) + r"\n?", "", page, flags=re.S)
    if NOINDEX not in page:
        page = re.sub(r"(<meta charset=[^>]*>)", r"\1\n  " + NOINDEX, page, count=1, flags=re.I)
    page = re.sub(r"Starting at \$\d+ flat fee",
                  f"${SITE_PRICE} · live in {DELIVERY_DAYS} days · online gift cards included", page)
    page = page.replace("bring it to life in 1–2 weeks", f"bring it to life in {DELIVERY_DAYS} days")
    page = re.sub(r"\$\d+ · live in \d+ days · online gift cards included",
                  f"${SITE_PRICE} · live in {DELIVERY_DAYS} days · online gift cards included", page)
    return page.replace("</body>", bar_html(name) + "\n</body>", 1)


def main():
    demos = os.path.join(HERE, "demos")
    check = "--check" in sys.argv
    changed = skipped = 0
    for fn in sorted(os.listdir(demos)):
        if not fn.endswith(".html"):
            continue
        path = os.path.join(demos, fn)
        with open(path, encoding="utf-8") as f:
            page = f.read()
        new = patch(page)
        if new == page:
            skipped += 1
            continue
        changed += 1
        if not check:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new)
    verb = "would change" if check else "updated"
    print(f"Offer bar: {verb} {changed} demo(s), {skipped} already current.")


if __name__ == "__main__":
    main()
