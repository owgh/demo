#!/usr/bin/env python3
"""
Launch kit: turns a client's demo into their real website.

  python3 launch.py <client.json> [--out DIR]

client.json holds what the client sent you (see clients/TEMPLATE.json in the
company-agents repo). Anything you leave out comes from their demo. The output
folder is a finished static site: upload it to Cloudflare Pages (or any static
host) and point their domain at it. See LAUNCH.md.

What changes from the demo:
  - no demo bar, no "noindex", no "Sample ..." notes, no "made for you" section
  - their real hours, services, prices, menu, photos and logo
  - booking, estimate, order, consultation and gift card requests are emailed
    to the owner (FormSubmit; the first request asks them to confirm once)
  - optional links to their own Square booking, gift card or ordering pages
  - search engine basics: canonical URL, social preview, LocalBusiness data,
    robots.txt and sitemap.xml
"""
import argparse
import csv
import html
import json
import os
import re
import shutil
import sys
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import site_data as sd  # noqa: E402
from utils import make_slug, render_template  # noqa: E402

LEADS_CSV = os.path.join(HERE, "..", "cold-email-agent", "leads_log.csv")

SCHEMA_TYPE = {
    "restaurant": "Restaurant", "cafe": "CafeOrCoffeeShop", "bakery": "Bakery", "pizza": "Restaurant", "catering": "FoodEstablishment",
    "barbershop": "HairSalon", "hair salon": "HairSalon", "nail salon": "NailSalon", "spa": "DaySpa", "dental clinic": "Dentist",
    "optometrist": "Optician", "veterinarian": "VeterinaryCare", "florist": "Florist", "plumber": "Plumber", "electrician": "Electrician",
    "painting contractor": "HousePainter", "roofing contractor": "RoofingContractor", "hvac contractor": "HVACBusiness",
    "locksmith": "Locksmith", "moving company": "MovingCompany", "auto repair": "AutoRepair", "law firm": "LegalService",
    "accountant": "AccountingService", "real estate agent": "RealEstateAgent", "daycare": "ChildCare", "personal trainer": "HealthClub",
    "insurance broker": "InsuranceAgency", "travel agency": "TravelAgency", "notary": "Notary", "tattoo shop": "TattooParlor",
}
DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
OVERRIDES = ("headline", "sub", "cta", "about", "services", "jobs", "staff", "matters", "quiz", "classes",
             "schedule", "zones", "popular", "primary", "faq", "gift")


def find_lead(name):
    if not name or not os.path.exists(LEADS_CSV):
        return None
    for r in csv.DictReader(open(LEADS_CSV, encoding="utf-8")):
        if r.get("business_name", "").strip().lower() == name.strip().lower():
            return r
    return None


def parse_address(addr):
    """'1390 Prince of Wales Dr, Ottawa, ON K2C 3N6' -> parts for structured data."""
    parts = [p.strip() for p in (addr or "").replace(", Canada", "").split(",") if p.strip()]
    out = {"@type": "PostalAddress", "addressCountry": "CA"}
    for i, p in enumerate(parts):
        m = re.match(r"^(ON|QC|Ontario|Quebec|Québec)\s*([A-Z]\d[A-Z]\s?\d[A-Z]\d)?$", p, re.I)
        if m:
            out["addressRegion"] = "ON" if m.group(1).upper().startswith("ON") else "QC"
            if m.group(2):
                out["postalCode"] = m.group(2).upper()
            if i > 0:
                out["addressLocality"] = parts[i - 1]
            out["streetAddress"] = ", ".join(parts[:max(0, i - 1)]) or parts[0]
            break
    else:
        if parts:
            out["streetAddress"] = parts[0]
    return out


def hhmm(h):
    return f"{int(h):02d}:{int(round((h % 1) * 60)):02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("client")
    ap.add_argument("--out")
    a = ap.parse_args()

    cfg = json.load(open(a.client, encoding="utf-8"))
    cdir = os.path.dirname(os.path.abspath(a.client))
    lead = find_lead(cfg.get("lead")) or {}
    lead = dict(lead)
    for k_cfg, k_lead in (("name", "business_name"), ("category", "category"), ("phone", "phone"), ("address", "address")):
        if cfg.get(k_cfg):
            lead[k_lead] = cfg[k_cfg]
    if not lead.get("business_name"):
        sys.exit("client.json needs \"lead\" (their name in the lead log) or \"name\" and \"category\".")
    slug = cfg.get("slug") or make_slug(lead["business_name"])
    out = os.path.abspath(a.out or os.path.join(HERE, "..", "sites", slug))

    import demo_agent as da  # needs config.py next to it (cp ../ui-ux-config.py config.py)

    site = sd.build_site(lead, slug, {"price": 0, "days": 0})
    if cfg.get("name"):
        site["name"] = sd.display_name(cfg["name"])
    for k in OVERRIDES:
        if k in cfg:
            site[k] = cfg[k]
    if "menu" in cfg:
        site["menu"] = {sec: [it if isinstance(it, dict) else {"name": it[0], "desc": it[1], "price": it[2], "veg": len(it) > 3} for it in items]
                        for sec, items in cfg["menu"].items()}
    if "hours" in cfg:
        site["hours"] = [{"label": h[0], "days": h[1], "open": h[2], "close": h[3]} for h in cfg["hours"]]
    site["live"] = True
    site.pop("offer", None)
    site["links"] = {k: v.strip() for k, v in (cfg.get("links") or {}).items() if isinstance(v, str) and v.strip().startswith("http")}
    if cfg.get("email"):
        site["form"] = cfg.get("formEndpoint") or "https://formsubmit.co/ajax/" + cfg["email"]
    elif cfg.get("formEndpoint"):
        site["form"] = cfg["formEndpoint"]
    else:
        print("WARNING: no \"email\" in client.json, so booking and order requests won't be delivered anywhere.")

    # files: photos and logo
    if os.path.isdir(out):
        shutil.rmtree(out)
    os.makedirs(os.path.join(out, "assets", "v2"))
    for f in ("site.css", "site.js"):
        shutil.copy(os.path.join(HERE, "demos", "assets", "v2", f), os.path.join(out, "assets", "v2", f))

    def copy_media(src):
        if re.match(r"^https?://", src):
            return src
        s = os.path.join(cdir, src)
        if not os.path.exists(s):
            print(f"WARNING: photo not found: {src}")
            return None
        os.makedirs(os.path.join(out, "photos"), exist_ok=True)
        name = make_slug(os.path.splitext(os.path.basename(src))[0]) + os.path.splitext(src)[1].lower()
        shutil.copy(s, os.path.join(out, "photos", name))
        return "photos/" + name

    photos = []
    for p in cfg.get("photos") or []:
        p = {"src": p} if isinstance(p, str) else dict(p)
        src = copy_media(p["src"])
        if src:
            p["src"] = src
            p.setdefault("alt", site["name"])
            photos.append(p)
    if photos:
        site["photos"] = photos
    logo = copy_media(cfg["logo"]) if cfg.get("logo") else None

    tokens = da.page_tokens(site, lead["business_name"])
    esc = lambda v: html.escape(str(v), quote=True)
    domain = (cfg.get("domain") or "").strip().lower().replace("https://", "").replace("http://", "").strip("/")
    url = f"https://{domain}/" if domain else ""
    image = (url + photos[0]["src"]) if (url and photos and not photos[0]["src"].startswith("http")) else (photos[0]["src"] if photos else "")

    biz = {"@context": "https://schema.org", "@type": SCHEMA_TYPE.get(site["category"], "LocalBusiness"),
           "name": site["name"], "telephone": site.get("phone") or None, "address": parse_address(site["address"]),
           "url": url or None, "image": image or None,
           "openingHoursSpecification": [{"@type": "OpeningHoursSpecification", "dayOfWeek": [DAYS[d] for d in hr["days"]],
                                          "opens": hhmm(hr["open"]), "closes": hhmm(hr["close"])}
                                         for hr in site["hours"] if hr.get("open") is not None],
           "sameAs": [v for v in (cfg.get("social") or {}).values() if v] or None}
    biz = {k: v for k, v in biz.items() if v}
    head = []
    if url:
        head.append(f'<link rel="canonical" href="{esc(url)}">')
    head += [f'<meta property="og:type" content="website">',
             f'<meta property="og:title" content="{esc(site["name"])}">',
             f'<meta property="og:description" content="{esc(site["sub"])}">']
    if url:
        head.append(f'<meta property="og:url" content="{esc(url)}">')
    if image:
        head.append(f'<meta property="og:image" content="{esc(image)}">')
    if logo:
        head.append(f'<link rel="icon" href="{esc(logo)}">')
    head.append('<script type="application/ld+json">' + json.dumps(biz, ensure_ascii=False).replace("</", "<\\/") + "</script>")
    tokens["HEAD_EXTRA"] = "\n  ".join(head)
    tokens["BUSINESS_NAME"] = esc(site["name"])  # page title: the name people use
    if logo:
        tokens["BRAND_LOGO"] = f'<img src="{esc(logo)}" alt="" width="40" height="40">'
    social = [(k.capitalize(), v) for k, v in (cfg.get("social") or {}).items() if v]
    foot = f'<p class="ftr-small">&copy; {date.today().year} {esc(site["name"])}'
    if social:
        foot += " · " + " · ".join(f'<a href="{esc(v)}" target="_blank" rel="noopener">{esc(k)}</a>' for k, v in social)
    tokens["FOOTER_EXTRA"] = foot + "</p>"

    page = render_template(da.load_template(), tokens)
    page = re.sub(r"<!-- DEMO-ONLY:START -->.*?<!-- DEMO-ONLY:END -->\n?", "", page, flags=re.S)
    page = page.replace(f"<title>{tokens['BUSINESS_NAME']} — Ottawa</title>", f"<title>{tokens['BUSINESS_NAME']} | {esc(site['city'])}</title>")
    open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(page)
    open(os.path.join(out, "404.html"), "w", encoding="utf-8").write(
        '<!DOCTYPE html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url=/"><title>Page not found</title><a href="/">Go to the home page</a>')
    open(os.path.join(out, "robots.txt"), "w").write("User-agent: *\nAllow: /\n" + (f"Sitemap: {url}sitemap.xml\n" if url else ""))
    if url:
        open(os.path.join(out, "sitemap.xml"), "w").write(
            f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{url}</loc><lastmod>{date.today().isoformat()}</lastmod></url></urlset>\n')
        open(os.path.join(out, "CNAME"), "w").write(domain + "\n")

    leftovers = [w for w in ("offer-bar", "noindex", "Sample services", "Demo prepared", "{{") if w in page]
    print(json.dumps({"site": out, "name": site["name"], "hook": site["hook"], "theme": site["theme"], "photos": len(photos),
                      "requests_go_to": cfg.get("email") or None, "links": site["links"], "domain": domain or None,
                      "check": "clean" if not leftovers else "found demo leftovers: " + ", ".join(leftovers)}, indent=1))


if __name__ == "__main__":
    main()
