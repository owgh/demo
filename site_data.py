"""
Site data for the v2 interactive demos.

Every demo is the same page skeleton (templates/v2.html) dressed in one of a
handful of themes, with one working "hook" in the hero that matches what the
business sells:

  bodymap    tap where it hurts -> the right treatment -> book     (massage, chiro, physio)
  estimate   pick the job, slide the size -> instant price range    (trades, cleaning, auto)
  order      add dishes -> cart -> pickup time -> live order status (restaurants, cafes)
  booking    service -> day -> time -> confirmed ticket + calendar  (salons, clinics, vets)
  mortgage   price, down payment, rate -> monthly payment           (mortgage, real estate)
  taxday     countdown to the filing deadline + what-to-bring list  (accountants)
  intake     3 questions -> free consultation request               (law, insurance, immigration)
  quiz       3 questions -> recommended program -> book             (trainers, tutors, driving)
  timetable  this week's classes -> reserve a spot                  (yoga, dance, martial arts)
  bouquet    pick stems and wrap -> live bouquet -> order           (florists)

Plus, on every demo: services with "Book", a live gift card builder, the
business's real address on a map, sample hours with an open-now badge, FAQ.

Prices, hours and menus are samples (each widget says so); the business name,
phone and address are the lead's real ones.
"""
import json
import re

# ── Themes: palette + type. Fonts are loaded per theme. ─────────────────────
THEMES = {
    "care":    {"fonts": "family=Young+Serif&family=Figtree:wght@400;500;600;700"},
    "trades":  {"fonts": "family=Archivo:wdth,wght@62..125,400..900"},
    "food":    {"fonts": "family=Caprasimo&family=Work+Sans:wght@400;500;600;700"},
    "barber":  {"fonts": "family=Alfa+Slab+One&family=Karla:wght@400;500;600;700"},
    "salon":   {"fonts": "family=Bodoni+Moda:ital,opsz,wght@0,6..96,400..800;1,6..96,400..800&family=Karla:wght@400;500;600;700"},
    "pro":     {"fonts": "family=Newsreader:ital,opsz,wght@0,6..72,400..700;1,6..72,400..700&family=Public+Sans:wght@400;500;600;700"},
    "gym":     {"fonts": "family=Big+Shoulders+Display:wght@600;800;900&family=Barlow:wght@400;500;600;700"},
    "kids":    {"fonts": "family=Fredoka:wght@500;600;700&family=Nunito:wght@400;600;700;800"},
    "pets":    {"fonts": "family=Gabarito:wght@500;600;700;800&family=Nunito:wght@400;600;700"},
    "florist": {"fonts": "family=Gloock&family=Outfit:wght@400;500;600;700"},
    "shop":    {"fonts": "family=Gloock&family=Outfit:wght@400;500;600;700"},
}

# Per-category primary colour overrides (the theme supplies everything else)
PRIMARY = {
    "landscaping": "#1d6b3a", "cleaning service": "#0b7285", "electrician": "#1c3fa8",
    "painting contractor": "#a8361a", "plumber": "#0b4f8a", "auto repair": "#a61e1e",
    "roofing contractor": "#6b2c12", "hvac contractor": "#0a5c8f", "locksmith": "#3a3f8f",
    "pest control": "#4d6b12", "carpet cleaning": "#0e6f6a", "window cleaning": "#0a6aa8",
    "snow removal": "#1e3f9e", "fence contractor": "#5a4318", "moving company": "#5b2fa3",
    "law firm": "#7a1f2b", "accountant": "#1d6b4f", "mortgage broker": "#0f5f73",
    "real estate agent": "#0f5f73", "insurance broker": "#23408e", "financial advisor": "#1d5b4f",
    "immigration consultant": "#9b2232", "notary": "#3d3a8c", "travel agency": "#0f6b8c",
    "private investigator": "#2b2f3a",
}

DAYS_ALL = [1, 2, 3, 4, 5, 6, 0]

HOURS = {  # sample hours: (label, weekday list Mon=1..Sun=0, open, close)
    "care":    [("Mon–Fri", [1, 2, 3, 4, 5], 9, 20), ("Saturday", [6], 9, 15), ("Sunday", [0], None, None)],
    "trades":  [("Mon–Fri", [1, 2, 3, 4, 5], 7, 18), ("Saturday", [6], 8, 14), ("Sunday", [0], None, None)],
    "food":    [("Mon–Thu", [1, 2, 3, 4], 11, 21), ("Fri–Sat", [5, 6], 11, 22), ("Sunday", [0], 12, 20)],
    "barber":  [("Mon–Fri", [1, 2, 3, 4, 5], 10, 19), ("Saturday", [6], 9, 17), ("Sunday", [0], 11, 16)],
    "salon":   [("Tue–Fri", [2, 3, 4, 5], 10, 19), ("Saturday", [6], 9, 17), ("Sun–Mon", [0, 1], None, None)],
    "pro":     [("Mon–Fri", [1, 2, 3, 4, 5], 9, 17), ("Weekends", [6, 0], None, None)],
    "gym":     [("Mon–Fri", [1, 2, 3, 4, 5], 6, 21), ("Saturday", [6], 8, 16), ("Sunday", [0], 9, 14)],
    "kids":    [("Mon–Fri", [1, 2, 3, 4, 5], 7, 18), ("Weekends", [6, 0], None, None)],
    "pets":    [("Mon–Fri", [1, 2, 3, 4, 5], 8, 19), ("Saturday", [6], 9, 15), ("Sunday", [0], None, None)],
    "florist": [("Mon–Fri", [1, 2, 3, 4, 5], 9, 18), ("Saturday", [6], 9, 17), ("Sunday", [0], 10, 15)],
    "shop":    [("Tue–Fri", [2, 3, 4, 5], 10, 18), ("Saturday", [6], 10, 17), ("Sun–Mon", [0, 1], None, None)],
}

FAQ = {
    "care": [
        ("Do I need a doctor's referral?", "No. You can book directly. If your insurance plan asks for a referral, bring it to your first visit."),
        ("Can I bill my insurance?", "Yes. We give you an official receipt after every visit, and we can bill many plans directly."),
        ("What happens at the first visit?", "A short assessment of where it hurts and what makes it worse, then treatment in the same visit."),
        ("What if I need to cancel?", "Let us know 24 hours ahead and there's no charge. You can move your time online."),
    ],
    "trades": [
        ("Is the online price final?", "It's an estimate. We confirm the exact price on site before any work starts, and it won't change without your OK."),
        ("Are you licensed and insured?", "Yes. We'll send proof of insurance with your quote."),
        ("How soon can you come?", "Most jobs get a visit within a few days. Emergencies go to the front of the line."),
        ("Do you clean up after?", "Always. We leave the space the way we found it, minus the problem."),
    ],
    "food": [
        ("How long does pickup take?", "Most orders are ready in about 20 minutes. You'll see the time before you order."),
        ("Can I order for a group?", "Yes. For 10 or more people, order a day ahead or call us."),
        ("Do you have vegetarian options?", "Yes, they're marked on the menu. Ask us about allergies when you pick up."),
        ("Can I pay when I pick up?", "Yes, or pay online when you order so you can grab it and go."),
    ],
    "barber": [
        ("Do you take walk-ins?", "Yes, when a chair is free. Booking online guarantees your time."),
        ("How long is a cut?", "About 30 minutes. Cut and beard together is about 45."),
        ("Can I pick my barber?", "Yes. Choose a barber when you book, or take the first available."),
        ("What if I'm running late?", "Text us. We'll hold your chair for 10 minutes."),
    ],
    "salon": [
        ("Do I need to book ahead?", "Booking is best, especially Fridays and Saturdays. We take walk-ins when we can."),
        ("How long will my appointment take?", "Each service shows its time when you book, so you can plan your day."),
        ("Can I buy a gift card?", "Yes. Gift cards arrive by email and can be used for any service."),
        ("What's your cancellation policy?", "Cancel or move your booking up to 24 hours before at no charge."),
    ],
    "pro": [
        ("Is the first call free?", "Yes. The first 15-minute call is free and there's no obligation."),
        ("Can we meet online?", "Yes. Meet in person, by phone or by video, whichever suits you."),
        ("What should I prepare?", "Any letters, forms or documents about your situation. We'll tell you exactly what to bring when we call."),
        ("How do your fees work?", "We explain our fees on the first call, before any work starts."),
    ],
    "gym": [
        ("I'm a complete beginner. Is that OK?", "Yes. Every plan starts from where you are today."),
        ("Is the first session free?", "Yes. Your first session is an assessment and a workout, at no charge."),
        ("Do you help with food?", "Yes. Every plan comes with simple eating guidelines that fit your goal."),
        ("Can I train with a friend?", "Yes. Partner sessions cost less per person."),
    ],
    "kids": [
        ("Can we visit first?", "Yes. Book a visit and we'll show you around and answer your questions."),
        ("How do you keep us updated?", "You get updates after each session, and you can always call or text."),
        ("What ages do you work with?", "It depends on the program. Pick an age in the finder above to see what fits."),
        ("Is there a trial?", "Yes. Your first session is a trial, so you can see if it's the right fit."),
    ],
    "pets": [
        ("Do you see new patients?", "Yes. Book online and bring any records you have."),
        ("What should I bring?", "Your pet's records, any medication they take, and a leash or carrier."),
        ("Do you see cats and dogs only?", "Mostly dogs and cats. Call us about other animals."),
        ("What if it's an emergency?", "Call us right away. We keep time free for urgent cases every day."),
    ],
    "florist": [
        ("Do you deliver the same day?", "Yes, for orders placed before 1 pm, Monday to Saturday."),
        ("Can I add a card?", "Yes. Write your message when you order and we'll handwrite it."),
        ("Where do you deliver?", "Across Ottawa. Delivery is free over $75."),
        ("Do you do weddings and events?", "Yes. Book a free consultation and bring your ideas."),
    ],
    "shop": [
        ("Do I need an appointment?", "Booking means we're ready for you. Walk-ins are welcome when we're free."),
        ("How long does it take?", "Most orders are ready within a week. Rush service is available."),
        ("Can I see examples?", "Yes. Ask us at your appointment or by email."),
        ("Do you sell gift cards?", "Yes. Gift cards arrive by email and never expire."),
    ],
}

# ── Categories ───────────────────────────────────────────────────────────────
# theme, hook, headline, sub, cta, services [name, description, minutes, price]
# {city} and {name} are filled in per lead.

def _s(name, desc, mins, price):
    return {"name": name, "desc": desc, "mins": mins, "price": price}


BODY_ZONES = ["head", "neck", "shoulders", "upperback", "lowerback", "hips", "legs", "feet"]

CATEGORIES = {
    # ── care + body map
    "massage therapist": {
        "theme": "care", "hook": "bodymap", "noun": "massage",
        "headline": "Tell us where it hurts.",
        "sub": "Registered massage therapy in {city}. Tap the body, see which treatment fits, and book a time that suits you.",
        "cta": "Book a massage",
        "services": [
            _s("Therapeutic massage", "Focused work on one problem area: neck, back or hips.", 60, 120),
            _s("Deep tissue massage", "Slow, firm pressure for long-held tension and knots.", 60, 125),
            _s("Relaxation massage", "Full body, lighter pressure. For stress and sleep.", 60, 110),
            _s("Sports massage", "Before or after training, races and games.", 45, 95),
            _s("Extended treatment", "Two problem areas, or one that needs more time.", 90, 165),
        ],
        "zones": {"head": (0, "Tension headaches often start in the neck and jaw."),
                  "neck": (0, "Desk work and phones load the neck all day."),
                  "shoulders": (1, "Knots between the shoulder blades respond well to deep work."),
                  "upperback": (1, "Firm pressure loosens the muscles around the shoulder blades."),
                  "lowerback": (4, "Lower back pain usually involves the hips too, so it needs the extra time."),
                  "hips": (1, "Tight hips pull on the lower back and knees."),
                  "legs": (3, "Calves and hamstrings tighten from running, standing and sitting."),
                  "feet": (2, "Sore feet from long days standing. A full-body session helps everything settle.")},
    },
    "chiropractor": {
        "theme": "care", "hook": "bodymap", "noun": "visit",
        "headline": "Back, neck or headaches? Start here.",
        "sub": "Chiropractic care in {city}. Tap where you feel it and book your first visit in under a minute.",
        "cta": "Book your first visit",
        "services": [
            _s("First visit and assessment", "History, movement tests and your first adjustment.", 45, 95),
            _s("Follow-up adjustment", "Adjustment and a check on how you're moving.", 20, 65),
            _s("Adjustment with soft tissue", "Adjustment plus hands-on muscle work.", 30, 85),
            _s("Posture assessment", "For desk workers and teens with forward head posture.", 30, 75),
        ],
        "zones": {"head": (0, "Many headaches start in the joints at the top of the neck."),
                  "neck": (0, "A stiff neck that won't turn is a common first visit."),
                  "shoulders": (2, "Shoulder pain often comes from the neck and upper back."),
                  "upperback": (3, "Rounded shoulders and a stiff upper back go together."),
                  "lowerback": (0, "Lower back pain is the most common reason people see a chiropractor."),
                  "hips": (2, "Hip and pelvis alignment affects your whole walk."),
                  "legs": (0, "Pain down the leg can come from the lower back. We'll check."),
                  "feet": (0, "Flat feet and sore knees change how your hips and back move.")},
    },
    "physiotherapy clinic": {
        "theme": "care", "hook": "bodymap", "noun": "assessment",
        "headline": "Point to the injury. We'll plan the recovery.",
        "sub": "Physiotherapy in {city}. Tap where it hurts and book an assessment with a registered physiotherapist.",
        "cta": "Book an assessment",
        "services": [
            _s("Initial assessment", "Find the cause, start treatment and leave with a plan.", 60, 120),
            _s("Follow-up treatment", "Hands-on care and exercises that move you forward.", 30, 90),
            _s("Sports injury rehab", "Back to your sport with a step-by-step return plan.", 45, 105),
            _s("Post-surgery rehab", "Knee, hip and shoulder recovery after surgery.", 45, 105),
        ],
        "zones": {"head": (0, "Dizziness and headaches after a fall need a proper assessment."),
                  "neck": (1, "Neck pain responds well to manual therapy and exercise."),
                  "shoulders": (2, "Rotator cuff and frozen shoulder are among the most common cases."),
                  "upperback": (1, "Upper back stiffness improves fast with the right exercises."),
                  "lowerback": (0, "Lower back pain gets a full assessment so we treat the cause."),
                  "hips": (3, "Hip pain, before or after surgery."),
                  "legs": (2, "Knee, hamstring and calf injuries from sport and running."),
                  "feet": (2, "Ankle sprains and plantar fasciitis.")},
    },
    "acupuncture": {
        "theme": "care", "hook": "bodymap", "noun": "treatment",
        "headline": "Show us where it aches.",
        "sub": "Acupuncture in {city}. Tap the area that bothers you and book a treatment.",
        "cta": "Book a treatment",
        "services": [
            _s("First treatment", "Health history, assessment and your first treatment.", 75, 110),
            _s("Follow-up treatment", "Acupuncture for pain, stress or sleep.", 50, 85),
            _s("Cupping", "Added to any treatment for tight muscles.", 20, 40),
        ],
        "zones": {z: (1, "Acupuncture is often used for pain in this area.") for z in BODY_ZONES},
    },
    "spa": {
        "theme": "care", "hook": "bodymap", "noun": "treatment",
        "headline": "Where do you hold your stress?",
        "sub": "Massage, facials and quiet time in {city}. Tap the body to find your treatment.",
        "cta": "Book a treatment",
        "services": [
            _s("Signature massage", "Full body, medium pressure, warm oils.", 60, 125),
            _s("Facial", "Cleanse, exfoliate and hydrate.", 60, 120),
            _s("Hot stone massage", "Warm stones melt deep tension.", 75, 145),
            _s("Foot ritual", "Soak, scrub and massage.", 45, 75),
        ],
        "zones": {"head": (1, "A facial takes the strain out of your face and jaw."),
                  "neck": (0, "Stress settles in the neck first."),
                  "shoulders": (2, "Warm stones loosen shoulders that sit up by your ears."),
                  "upperback": (2, "Heat works deep into the upper back."),
                  "lowerback": (0, "A full massage eases a tired lower back."),
                  "hips": (0, "Long days sitting lock up the hips."),
                  "legs": (3, "Heavy legs after a long week."),
                  "feet": (3, "Tired feet get their own treatment.")},
    },
    # ── care + booking
    "dental clinic": {
        "theme": "care", "hook": "booking", "noun": "appointment",
        "headline": "Book your cleaning in under a minute.",
        "sub": "Family dentistry in {city}. Pick a visit, see open times, and you're booked.",
        "cta": "Book an appointment",
        "services": [
            _s("Cleaning and checkup", "Exam, cleaning and polish.", 60, 180),
            _s("New patient exam", "Full exam, X-rays and a care plan.", 60, 220),
            _s("Teeth whitening", "In-office whitening, one visit.", 90, 399),
            _s("Emergency visit", "Toothache, chips and swelling. Same-day when we can.", 30, 95),
        ],
    },
    "optometrist": {
        "theme": "care", "hook": "booking", "noun": "eye exam",
        "headline": "Eye exams, booked in a minute.",
        "sub": "Optometry in {city}. Choose your exam and pick a time that works.",
        "cta": "Book an eye exam",
        "services": [
            _s("Comprehensive eye exam", "Vision, eye health and a new prescription.", 45, 125),
            _s("Children's eye exam", "OHIP covers yearly exams for kids under 20.", 30, 0),
            _s("Contact lens fitting", "Fitting, trial lenses and a follow-up.", 30, 85),
            _s("Frames consultation", "Find frames that fit your face and prescription.", 30, 0),
        ],
    },
    "psychologist": {"theme": "care", "hook": "booking", "noun": "session",
        "headline": "Taking the first step can be simple.",
        "sub": "Therapy in {city} and online. Book a free 15-minute call to see if we're a good fit.",
        "cta": "Book a free call",
        "services": [_s("Free consultation call", "15 minutes to talk about what you need.", 15, 0),
                     _s("Individual therapy", "In person or online.", 50, 200),
                     _s("Couples therapy", "For partners who want to communicate better.", 75, 260)]},
    "naturopath": {"theme": "care", "hook": "booking", "noun": "visit",
        "headline": "Care that looks at the whole picture.",
        "sub": "Naturopathic medicine in {city}. Book a first visit or a free meet-and-greet.",
        "cta": "Book a visit",
        "services": [_s("Free meet-and-greet", "15 minutes to ask questions.", 15, 0),
                     _s("First visit", "Full health history and your plan.", 75, 190),
                     _s("Follow-up visit", "Review progress and adjust the plan.", 30, 95)]},
    "dietitian": {"theme": "care", "hook": "booking", "noun": "session",
        "headline": "Eating well, made specific to you.",
        "sub": "Registered dietitian in {city} and online. Book your first session in a minute.",
        "cta": "Book a session",
        "services": [_s("First session", "Your goals, habits and a plan you can follow.", 60, 150),
                     _s("Follow-up session", "Check in and adjust.", 30, 80)]},
    "speech therapist": {"theme": "care", "hook": "booking", "noun": "session",
        "headline": "Clearer words, more confidence.",
        "sub": "Speech therapy for kids and adults in {city}. Book an assessment in a minute.",
        "cta": "Book an assessment",
        "services": [_s("Assessment", "Find out where to start.", 60, 220),
                     _s("Therapy session", "One-on-one, in person or online.", 45, 140)]},
    # ── trades + estimate
    "landscaping": {
        "theme": "trades", "hook": "estimate", "noun": "visit",
        "headline": "Price your yard in ten seconds.",
        "sub": "Lawn care, cleanups and garden work in {city}. Pick a job, slide the size, and see your price before anyone visits.",
        "cta": "Get my estimate",
        "services": [
            _s("Weekly lawn care", "Mow, trim and edge, every week of the season.", 45, 45),
            _s("Fall cleanup", "Leaves, beds cut back and gutters cleared.", 180, 295),
            _s("Garden bed refresh", "Weed, edge and fresh mulch.", 240, 380),
            _s("Sod installation", "New lawn, laid and rolled.", 480, 1200),
        ],
        "jobs": [
            {"name": "Fall cleanup", "unit": "sq ft of yard", "min": 1000, "max": 12000, "step": 250, "def": 4000, "base": 120, "rate": 0.045},
            {"name": "Lawn mowing (per visit)", "unit": "sq ft of lawn", "min": 1000, "max": 15000, "step": 250, "def": 5000, "base": 30, "rate": 0.004},
            {"name": "Mulch and garden beds", "unit": "sq ft of beds", "min": 50, "max": 1500, "step": 25, "def": 300, "base": 90, "rate": 1.6},
            {"name": "New sod", "unit": "sq ft", "min": 100, "max": 5000, "step": 50, "def": 800, "base": 250, "rate": 2.1},
        ],
    },
    "cleaning service": {
        "theme": "trades", "hook": "estimate", "noun": "cleaning",
        "headline": "See your cleaning price now.",
        "sub": "Home and office cleaning in {city}. Pick the clean, set the size, and book a time. No calls back and forth.",
        "cta": "Get my price",
        "services": [
            _s("Regular home cleaning", "Kitchen, bathrooms, floors and dusting.", 180, 140),
            _s("Deep cleaning", "Inside appliances, baseboards and every corner.", 300, 290),
            _s("Move-out cleaning", "Get your deposit back.", 300, 320),
            _s("Office cleaning", "After hours, weekly or nightly.", 120, 120),
        ],
        "jobs": [
            {"name": "Regular cleaning", "unit": "bedrooms", "min": 1, "max": 6, "step": 1, "def": 2, "base": 90, "rate": 30},
            {"name": "Deep cleaning", "unit": "bedrooms", "min": 1, "max": 6, "step": 1, "def": 3, "base": 170, "rate": 55},
            {"name": "Move-out cleaning", "unit": "bedrooms", "min": 1, "max": 6, "step": 1, "def": 2, "base": 200, "rate": 60},
            {"name": "Office cleaning", "unit": "sq ft", "min": 500, "max": 10000, "step": 250, "def": 2000, "base": 60, "rate": 0.05},
        ],
    },
    "electrician": {
        "theme": "trades", "hook": "estimate", "noun": "visit",
        "headline": "Electrical work, priced before we start.",
        "sub": "Licensed electricians in {city}. Pick the job and see a price range now, then book a visit.",
        "cta": "Get my estimate",
        "services": [
            _s("Pot lights", "Supply and install, patching included.", 240, 600),
            _s("Panel upgrade", "100 to 200 amp, permit included.", 480, 2800),
            _s("EV charger install", "Level 2 charger in your garage or driveway.", 300, 1100),
            _s("Troubleshooting", "Dead outlets, tripping breakers, flickering lights.", 60, 140),
        ],
        "jobs": [
            {"name": "Pot lights", "unit": "lights", "min": 2, "max": 30, "step": 1, "def": 8, "base": 150, "rate": 95},
            {"name": "EV charger install", "unit": "metres from panel", "min": 1, "max": 30, "step": 1, "def": 8, "base": 850, "rate": 28},
            {"name": "New outlets or switches", "unit": "outlets", "min": 1, "max": 20, "step": 1, "def": 4, "base": 110, "rate": 65},
            {"name": "Panel upgrade to 200 A", "unit": "circuits", "min": 10, "max": 40, "step": 1, "def": 24, "base": 2200, "rate": 22},
        ],
    },
    "painting contractor": {
        "theme": "trades", "hook": "estimate", "noun": "estimate",
        "headline": "Pick the rooms. See the price.",
        "sub": "Interior and exterior painting in {city}. Get a price range in seconds, then book a free colour visit.",
        "cta": "Get my estimate",
        "services": [
            _s("Interior room", "Walls, two coats, furniture moved and covered.", 360, 450),
            _s("Kitchen cabinets", "Sanded, primed and sprayed.", 1440, 3200),
            _s("Exterior painting", "Siding, trim and doors.", 2400, 4500),
            _s("Deck staining", "Washed, prepped and stained.", 480, 850),
        ],
        "jobs": [
            {"name": "Interior rooms", "unit": "rooms", "min": 1, "max": 15, "step": 1, "def": 3, "base": 150, "rate": 380},
            {"name": "Kitchen cabinets", "unit": "doors and drawers", "min": 10, "max": 60, "step": 1, "def": 28, "base": 600, "rate": 95},
            {"name": "Exterior siding", "unit": "sq ft", "min": 500, "max": 4000, "step": 100, "def": 1800, "base": 600, "rate": 2.4},
            {"name": "Deck staining", "unit": "sq ft", "min": 100, "max": 1000, "step": 25, "def": 300, "base": 200, "rate": 2.2},
        ],
    },
    "plumber": {
        "theme": "trades", "hook": "estimate", "noun": "visit",
        "headline": "Leak? See the price, book a plumber.",
        "sub": "Plumbing repairs and installs in {city}. Get a price range now. Emergencies go to the front of the line.",
        "cta": "Get my estimate",
        "services": [
            _s("Leak repair", "Pipes, taps and toilets.", 60, 180),
            _s("Water heater replacement", "Remove the old one, install the new one.", 240, 1800),
            _s("Drain cleaning", "Kitchen, bathroom and main drains.", 60, 220),
            _s("Fixture install", "Taps, toilets, sinks and showers.", 120, 260),
        ],
        "jobs": [
            {"name": "Leak or repair", "unit": "fixtures", "min": 1, "max": 6, "step": 1, "def": 1, "base": 140, "rate": 70},
            {"name": "Drain cleaning", "unit": "drains", "min": 1, "max": 5, "step": 1, "def": 1, "base": 180, "rate": 80},
            {"name": "Water heater", "unit": "gallons", "min": 30, "max": 75, "step": 5, "def": 50, "base": 1100, "rate": 14},
            {"name": "Bathroom fixtures", "unit": "fixtures", "min": 1, "max": 8, "step": 1, "def": 3, "base": 150, "rate": 160},
        ],
    },
    "auto repair": {
        "theme": "trades", "hook": "estimate", "noun": "appointment",
        "headline": "Know the cost before you drive in.",
        "sub": "Honest car repair in {city}. Pick the job, choose your car, see a price range and book a bay.",
        "cta": "Get my estimate",
        "services": [
            _s("Oil change", "Synthetic oil, filter and a 20-point check.", 30, 89),
            _s("Brake pads and rotors", "Per axle, parts and labour.", 90, 420),
            _s("Winter tire swap", "Swap, balance and torque.", 45, 80),
            _s("Diagnostics", "Check engine light, noises and warning lights.", 60, 120),
        ],
        "jobs": [
            {"name": "Brakes (pads and rotors)", "unit": "axles", "min": 1, "max": 2, "step": 1, "def": 1, "base": 60, "rate": 360},
            {"name": "Tire swap", "unit": "tires", "min": 4, "max": 8, "step": 4, "def": 4, "base": 20, "rate": 15},
            {"name": "Oil change", "unit": "litres", "min": 4, "max": 8, "step": 1, "def": 5, "base": 49, "rate": 9},
            {"name": "Diagnostics", "unit": "hours", "min": 1, "max": 3, "step": 1, "def": 1, "base": 0, "rate": 120},
        ],
    },
    # ── food + order
    "restaurant": {
        "theme": "food", "hook": "order", "noun": "order",
        "headline": "Order ahead. Skip the wait.",
        "sub": "Pickup from {name} in {city}. Choose your dishes and we'll have them hot when you walk in.",
        "cta": "Start an order",
        "services": [],
        "menu": {
            "Starters": [("Crispy calamari", "Lemon, garlic aioli", 14), ("Soup of the day", "Ask us what's on today", 8), ("Garden salad", "House vinaigrette", 11, "v")],
            "Mains": [("Grilled chicken plate", "Rice, salad, garlic sauce", 21), ("Braised short rib", "Mash, seasonal greens", 29), ("Mushroom risotto", "Parmesan, herbs", 22, "v"), ("Steak frites", "8 oz striploin, peppercorn sauce", 32)],
            "Sides": [("Fries", "Sea salt", 6, "v"), ("Seasonal vegetables", "Roasted", 7, "v")],
            "Drinks": [("Fresh lemonade", "", 5, "v"), ("Soft drinks", "", 3, "v")],
        },
        "popular": [["Mains", 0], ["Mains", 1], ["Starters", 0]],
    },
    "cafe": {
        "theme": "food", "hook": "order", "noun": "order",
        "headline": "Your coffee, ready when you are.",
        "sub": "Order ahead at {name} in {city} and skip the line.",
        "cta": "Order ahead", "services": [],
        "menu": {
            "Coffee": [("Latte", "Double shot, steamed milk", 5.5), ("Americano", "", 4), ("Cappuccino", "", 5), ("Oat flat white", "", 6)],
            "Bakery": [("Butter croissant", "Baked this morning", 4, "v"), ("Banana bread", "", 4.5, "v"), ("Cookie", "Chocolate chunk", 3.5, "v")],
            "Lunch": [("Grilled cheese", "Sourdough, aged cheddar", 11, "v"), ("Turkey sandwich", "Pesto, tomato", 13)],
        },
        "popular": [["Coffee", 0], ["Bakery", 0], ["Lunch", 0]],
    },
    "bakery": {
        "theme": "food", "hook": "order", "noun": "order",
        "headline": "Fresh bread, set aside for you.",
        "sub": "Reserve today's bake at {name} in {city} and pick it up warm.",
        "cta": "Reserve today's bake", "services": [],
        "menu": {
            "Bread": [("Country sourdough", "Naturally leavened", 9, "v"), ("Baguette", "", 4.5, "v"), ("Seeded rye", "", 9.5, "v")],
            "Pastry": [("Croissant", "", 4, "v"), ("Pain au chocolat", "", 4.5, "v"), ("Cinnamon bun", "", 5, "v")],
            "Cakes": [("Celebration cake (8 in.)", "Order 48 hours ahead", 55, "v"), ("Lemon tart", "", 6.5, "v")],
        },
        "popular": [["Bread", 0], ["Pastry", 0], ["Pastry", 2]],
    },
    "pizza": {
        "theme": "food", "hook": "order", "noun": "order",
        "headline": "Hot pizza, ready in 20 minutes.",
        "sub": "Order for pickup from {name} in {city}.",
        "cta": "Order a pizza", "services": [],
        "menu": {
            "Pizzas": [("Margherita", "Tomato, mozzarella, basil", 17, "v"), ("Pepperoni", "Double pepperoni", 19), ("Veggie", "Peppers, mushrooms, olives, onion", 19, "v"), ("Meat lovers", "Pepperoni, sausage, bacon", 23)],
            "Sides": [("Garlic bread", "", 7, "v"), ("Wings (1 lb)", "Hot, BBQ or honey garlic", 15), ("Caesar salad", "", 10)],
            "Drinks": [("Pop (2 L)", "", 4.5, "v")],
        },
        "popular": [["Pizzas", 1], ["Pizzas", 0], ["Sides", 1]],
    },
    # ── barber / salon + booking
    "barbershop": {
        "theme": "barber", "hook": "booking", "noun": "cut",
        "headline": "Pick your cut. Grab your chair.",
        "sub": "{name} in {city}. See today's open times and book in three taps.",
        "cta": "Book a cut",
        "services": [
            _s("Haircut", "Scissor or clipper cut, styled.", 30, 35),
            _s("Skin fade", "Fade to the skin, sharp line-up.", 40, 40),
            _s("Cut and beard", "Haircut plus beard shape and hot towel.", 45, 50),
            _s("Beard trim", "Shape, line-up and hot towel.", 20, 22),
            _s("Kids' cut", "Under 12.", 25, 25),
        ],
        "staff": ["First available", "Marco", "Dee", "Sam"],
    },
    "tattoo shop": {
        "theme": "barber", "hook": "booking", "noun": "consult",
        "headline": "Bring the idea. We'll draw it up.",
        "sub": "Custom tattoos in {city}. Book a free consult to talk design, size and price.",
        "cta": "Book a consult",
        "services": [_s("Free consult", "Talk design, placement and price.", 20, 0),
                     _s("Small tattoo", "Up to about 3 inches.", 60, 150),
                     _s("Half-day session", "Larger custom pieces.", 240, 500)]},
    "hair salon": {
        "theme": "salon", "hook": "booking", "noun": "appointment",
        "headline": "Your next appointment, booked in three taps.",
        "sub": "Cuts, colour and styling at {name} in {city}.",
        "cta": "Book an appointment",
        "services": [_s("Women's cut and style", "Wash, cut and blow-dry.", 60, 75),
                     _s("Men's cut", "Wash, cut and style.", 30, 40),
                     _s("Full colour", "Root to tip, one colour.", 120, 140),
                     _s("Balayage", "Hand-painted highlights.", 180, 240),
                     _s("Blow-dry", "Wash and style.", 45, 50)],
        "staff": ["First available", "Lina", "Priya", "Jo"]},
    "nail salon": {
        "theme": "salon", "hook": "booking", "noun": "appointment",
        "headline": "Your next set, booked in three taps.",
        "sub": "Manicures, pedicures and gel at {name} in {city}. See open times and book.",
        "cta": "Book an appointment",
        "services": [
            _s("Gel manicure", "Shape, cuticle care and gel colour.", 45, 45),
            _s("Classic manicure", "Shape, cuticle care and polish.", 30, 30),
            _s("Spa pedicure", "Soak, scrub, massage and polish.", 50, 50),
            _s("Gel extensions", "Full set, any shape.", 90, 75),
            _s("Nail art", "Per nail, from simple to detailed.", 15, 5),
        ],
        "staff": ["First available", "Anna", "Mai", "Tina"],
    },
    "eyebrow threading": {"theme": "salon", "hook": "booking", "noun": "appointment",
        "headline": "Clean brows in fifteen minutes.",
        "sub": "Threading, tinting and lamination at {name} in {city}.",
        "cta": "Book now",
        "services": [_s("Eyebrow threading", "Shape and clean-up.", 15, 15),
                     _s("Brow tint", "Fuller-looking brows.", 15, 20),
                     _s("Brow lamination", "Brushed-up, set brows.", 45, 70),
                     _s("Full face threading", "", 30, 40)]},
    "makeup artist": {"theme": "salon", "hook": "booking", "noun": "booking",
        "headline": "Look like yourself, on your best day.",
        "sub": "Makeup for weddings, events and photos in {city}.",
        "cta": "Book a trial",
        "services": [_s("Makeup trial", "Try your look before the day.", 60, 90),
                     _s("Event makeup", "Lashes included.", 60, 120),
                     _s("Bridal makeup", "Trial and wedding day.", 120, 350)]},
    # ── pro
    "mortgage broker": {
        "theme": "pro", "hook": "mortgage", "noun": "call",
        "headline": "See your payment. Then let us beat the rate.",
        "sub": "Mortgage broker in {city}. Try the numbers, then book a free call and we'll shop dozens of lenders for you.",
        "cta": "Book a free call",
        "services": [_s("Pre-approval", "Know your budget before you shop.", 30, 0),
                     _s("Renewal review", "Don't just sign the bank's renewal letter.", 30, 0),
                     _s("Refinance", "Lower payments or pull out equity.", 30, 0),
                     _s("First-time buyers", "Down payment, programs and closing costs explained.", 45, 0)],
    },
    "real estate agent": {
        "theme": "pro", "hook": "mortgage", "noun": "call",
        "headline": "What can you afford in {city}?",
        "sub": "Buying or selling in {city}? Try the payment calculator, then book a free call with {name}.",
        "cta": "Book a free call",
        "services": [_s("Buyer consultation", "What you can afford and where to look.", 30, 0),
                     _s("Free home evaluation", "What your home would sell for today.", 45, 0),
                     _s("Selling strategy", "Pricing, staging and timing.", 45, 0)],
    },
    "accountant": {
        "theme": "pro", "hook": "taxday", "noun": "appointment",
        "headline": "Tax season, handled.",
        "sub": "Personal and small business tax in {city}. See what to bring, then book your appointment.",
        "cta": "Book my tax appointment",
        "services": [_s("Personal tax return", "Single filer, slips and credits.", 45, 120),
                     _s("Couple or family return", "Both returns, optimized together.", 60, 200),
                     _s("Self-employed return", "Income, expenses and HST.", 60, 300),
                     _s("Small business bookkeeping", "Monthly books and HST filing.", 60, 250)],
    },
    "law firm": {
        "theme": "pro", "hook": "intake", "noun": "consultation",
        "headline": "Tell us what happened. We'll call you back.",
        "sub": "{name} in {city}. Answer three quick questions and book a free 15-minute call with a lawyer.",
        "cta": "Start my free consultation",
        "services": [_s("Family law", "Separation, custody and support.", 30, 0),
                     _s("Real estate", "Buying, selling and refinancing.", 30, 0),
                     _s("Wills and estates", "Wills, powers of attorney and probate.", 30, 0),
                     _s("Employment law", "Dismissal, severance and workplace issues.", 30, 0)],
        "matters": ["Family or separation", "Buying or selling a home", "A will or an estate", "My job or a dismissal", "A business matter", "Something else"],
    },
    "insurance broker": {"theme": "pro", "hook": "intake", "noun": "quote",
        "headline": "Better coverage, one short form away.",
        "sub": "Independent insurance broker in {city}. Tell us what you need and we'll compare insurers for you.",
        "cta": "Start my quote",
        "services": [_s("Home insurance", "", 20, 0), _s("Auto insurance", "", 20, 0), _s("Business insurance", "", 30, 0)],
        "matters": ["Home or condo", "Car", "Home and car together", "My business", "Life insurance", "Something else"]},
    "financial advisor": {"theme": "pro", "hook": "intake", "noun": "call",
        "headline": "A clear plan for your money.",
        "sub": "Financial planning in {city}. Three quick questions, then a free call.",
        "cta": "Book a free call",
        "services": [_s("Retirement planning", "", 45, 0), _s("RRSP and TFSA strategy", "", 30, 0), _s("Education savings", "", 30, 0)],
        "matters": ["Retirement", "Investing", "Saving for a home", "Saving for kids' education", "Something else"]},
    "immigration consultant": {"theme": "pro", "hook": "intake", "noun": "consultation",
        "headline": "Your next step to Canada, made clear.",
        "sub": "Licensed immigration consultant in {city}. Three quick questions and we'll call you.",
        "cta": "Book a consultation",
        "services": [_s("Permanent residence", "", 45, 0), _s("Study and work permits", "", 30, 0), _s("Family sponsorship", "", 45, 0)],
        "matters": ["Permanent residence", "Study permit", "Work permit", "Sponsoring family", "Citizenship", "Something else"]},
    "notary": {"theme": "pro", "hook": "booking", "noun": "appointment",
        "headline": "Documents signed and stamped today.",
        "sub": "Notary services in {city}. Pick a time and bring your ID.",
        "cta": "Book an appointment",
        "services": [_s("Notarize a document", "Per document.", 15, 40), _s("Affidavit", "", 20, 60), _s("Certified copies", "Per copy.", 10, 20)]},
    "travel agency": {"theme": "pro", "hook": "intake", "noun": "call",
        "headline": "Tell us the dream. We'll plan the trip.",
        "sub": "Travel planning in {city}. Three quick questions and an agent will call you.",
        "cta": "Plan my trip",
        "services": [_s("Vacation packages", "", 30, 0), _s("Cruises", "", 30, 0), _s("Group travel", "", 45, 0)],
        "matters": ["Beach holiday", "Europe", "A cruise", "A family trip", "Something else"]},
    "private investigator": {"theme": "pro", "hook": "intake", "noun": "consultation",
        "headline": "Confidential help, starting with one call.",
        "sub": "Licensed investigators in {city}. Tell us a little and we'll call you back.",
        "cta": "Request a call",
        "services": [_s("Background checks", "", 30, 0), _s("Surveillance", "", 30, 0), _s("Locating people", "", 30, 0)],
        "matters": ["A background check", "Surveillance", "Finding someone", "A workplace matter", "Something else"]},
    # ── gym + quiz / timetable
    "personal trainer": {
        "theme": "gym", "hook": "quiz", "noun": "session",
        "headline": "Find your program in three questions.",
        "sub": "Personal training in {city}. Answer three questions, see your plan, and book a free first session.",
        "cta": "Find my program",
        "services": [_s("1-on-1 training", "Coached sessions built around your goal.", 60, 80),
                     _s("Partner training", "Train with a friend, split the cost.", 60, 110),
                     _s("Online coaching", "Weekly plan, check-ins and form reviews.", 0, 150),
                     _s("Free first session", "Assessment and a real workout.", 60, 0)],
        "quiz": {
            "questions": [
                {"q": "What's your main goal?", "options": ["Lose fat", "Build muscle", "Get stronger", "Move without pain"]},
                {"q": "How many days a week can you train?", "options": ["2 days", "3 days", "4 or more"]},
                {"q": "How long have you been training?", "options": ["Just starting", "Under a year", "Over a year"]},
            ],
            "results": {
                "Lose fat": ("Lean and strong", "Strength training plus conditioning, with simple eating habits you can keep."),
                "Build muscle": ("Size and shape", "Progressive muscle-building sessions with a clear plan for every week."),
                "Get stronger": ("Strength foundations", "Squat, hinge, press and pull, coached until your numbers climb."),
                "Move without pain": ("Move well again", "Mobility and strength work that keeps your back, hips and knees happy."),
            },
            "price": 80, "unit": "session",
        },
    },
    "martial arts": {"theme": "gym", "hook": "timetable", "noun": "class",
        "headline": "Your first class is free. Pick one.",
        "sub": "Martial arts for kids and adults in {city}. See this week's classes and save your spot.",
        "cta": "See this week's classes",
        "services": [_s("Kids' classes", "Ages 5 to 12.", 45, 0), _s("Adult classes", "All levels.", 60, 0), _s("Private lessons", "", 60, 70)],
        "classes": ["Kids beginners", "Adult fundamentals", "Sparring", "Open mat"]},
    # ── kids + quiz / timetable
    "daycare": {
        "theme": "kids", "hook": "quiz", "noun": "tour",
        "headline": "Check for a spot, then come and visit.",
        "sub": "Child care in {city}. Tell us your child's age and the days you need, and book a tour.",
        "cta": "Check availability",
        "services": [_s("Full-day care", "7 am to 6 pm, meals included.", 0, 0), _s("Part-time care", "2 or 3 days a week.", 0, 0), _s("Before and after school", "For school-age kids.", 0, 0)],
        "quiz": {
            "questions": [
                {"q": "How old is your child?", "options": ["Under 18 months", "18 months to 2½", "2½ to 4", "4 to 12"]},
                {"q": "How many days a week?", "options": ["2 days", "3 days", "5 days"]},
                {"q": "When do you need care?", "options": ["This month", "Next month", "Later this year"]},
            ],
            "results": {
                "Under 18 months": ("Infant room", "Small groups, a calm space and lots of one-on-one time."),
                "18 months to 2½": ("Toddler room", "Play-based days, outdoor time and a simple routine."),
                "2½ to 4": ("Preschool room", "Early literacy, numbers and getting ready for school."),
                "4 to 12": ("Before and after school", "Homework help, games and outdoor play."),
            },
            "mode": "availability", "noun": "tour",
        },
    },
    "tutoring": {
        "theme": "kids", "hook": "quiz", "noun": "session",
        "headline": "Find the right tutoring plan in three questions.",
        "sub": "Tutoring in {city} and online. Get a plan for your child and book a free trial session.",
        "cta": "Find a plan",
        "services": [_s("Math", "Grades 1 to 12.", 60, 55), _s("English and writing", "Reading, essays and grammar.", 60, 55), _s("Science", "Biology, chemistry, physics.", 60, 60), _s("Test prep", "EQAO, SAT and exams.", 60, 65)],
        "quiz": {
            "questions": [
                {"q": "Which subject?", "options": ["Math", "English", "Science", "French"]},
                {"q": "Which grade?", "options": ["Grades 1–5", "Grades 6–8", "Grades 9–12"]},
                {"q": "What's the goal?", "options": ["Catch up", "Get ahead", "Ace a test"]},
            ],
            "results": {
                "Math": ("Math confidence plan", "Weekly sessions that fill the gaps, then build speed."),
                "English": ("Reading and writing plan", "Reading, writing and grammar practice that sticks."),
                "Science": ("Science plan", "Concepts explained simply, then practised with real questions."),
                "French": ("French plan", "Speaking, reading and grammar for French and immersion students."),
            },
            "price": 55, "unit": "session",
        },
    },
    "driving school": {
        "theme": "kids", "hook": "quiz", "noun": "lesson",
        "headline": "From learner to licence. Find your package.",
        "sub": "MTO-approved driving lessons in {city}. Three questions, then book your first lesson.",
        "cta": "Find my package",
        "services": [_s("Beginner course", "Classroom plus in-car lessons.", 0, 695), _s("Road test prep", "Lessons on the test route.", 60, 65), _s("Car for road test", "Warm-up lesson and our car.", 90, 150)],
        "quiz": {
            "questions": [
                {"q": "Where are you now?", "options": ["Just got my G1", "Booked my G2 test", "Booked my G test"]},
                {"q": "How much driving have you done?", "options": ["None yet", "A few hours", "Lots"]},
                {"q": "How soon is your test?", "options": ["Not booked yet", "In a month", "In two weeks"]},
            ],
            "results": {
                "Just got my G1": ("Full beginner course", "Classroom, 10 hours in the car, and a shorter wait for your G2 test."),
                "Booked my G2 test": ("G2 road test prep", "Practice on the actual test routes, plus our car on test day."),
                "Booked my G test": ("G highway prep", "Highway driving, merging and lane changes until they feel easy."),
            },
            "price": 65, "unit": "lesson",
        },
    },
    "music school": {"theme": "kids", "hook": "timetable", "noun": "lesson",
        "headline": "Try a lesson this week.",
        "sub": "Music lessons for all ages in {city}. Pick a class and save a spot.",
        "cta": "See this week's lessons",
        "services": [_s("Piano lessons", "", 30, 35), _s("Guitar lessons", "", 30, 35), _s("Voice lessons", "", 30, 40)],
        "classes": ["Piano", "Guitar", "Voice", "Kids' music"]},
    "dance studio": {"theme": "kids", "hook": "timetable", "noun": "class",
        "headline": "Find your class. Save your spot.",
        "sub": "Dance for kids and adults in {city}. See this week's classes and try one free.",
        "cta": "See this week's classes",
        "services": [_s("Kids' dance", "", 45, 0), _s("Hip hop", "", 60, 0), _s("Ballet", "", 60, 0)],
        "classes": ["Ballet", "Hip hop", "Jazz", "Kids' combo"]},
    "yoga studio": {"theme": "care", "hook": "timetable", "noun": "class",
        "headline": "Roll out your mat this week.",
        "sub": "Yoga in {city}. Pick a class and save your spot. Your first class is free.",
        "cta": "See this week's classes",
        "services": [_s("Drop-in class", "", 60, 22), _s("10-class pass", "", 60, 190), _s("Monthly unlimited", "", 60, 150)],
        "classes": ["Gentle flow", "Vinyasa", "Yin", "Hot flow"]},
    # ── pets
    "veterinarian": {
        "theme": "pets", "hook": "booking", "noun": "visit",
        "headline": "Book your pet's visit in a minute.",
        "sub": "Veterinary care in {city}. Choose your pet, pick a time, and we'll see you soon.",
        "cta": "Book a visit",
        "pets": True,
        "services": [_s("Wellness exam", "Nose-to-tail checkup.", 30, 95),
                     _s("Vaccines", "Core vaccines and boosters.", 20, 75),
                     _s("Sick visit", "Vomiting, limping, skin and ears.", 30, 110),
                     _s("Dental cleaning", "Under anesthesia, with X-rays.", 120, 650),
                     _s("New puppy or kitten", "First exam and vaccine plan.", 40, 120)],
    },
    "pet grooming": {"theme": "pets", "hook": "booking", "noun": "groom", "pets": True,
        "headline": "A fresh groom, booked in a minute.",
        "sub": "Dog and cat grooming in {city}. Choose your pet, pick a time.",
        "cta": "Book a groom",
        "services": [_s("Full groom", "Bath, haircut, nails and ears.", 120, 85),
                     _s("Bath and tidy", "Bath, brush, nails.", 60, 55),
                     _s("Nail trim", "", 15, 18)]},
    "dog training": {"theme": "pets", "hook": "quiz", "noun": "session",
        "headline": "Better walks start with three questions.",
        "sub": "Positive dog training in {city}. Get a plan for your dog and book a first session.",
        "cta": "Find my plan",
        "services": [_s("Puppy class", "6 weeks.", 60, 240), _s("Private training", "", 60, 95), _s("Leash manners", "", 60, 95)],
        "quiz": {
            "questions": [
                {"q": "How old is your dog?", "options": ["Puppy", "Under 2 years", "Adult"]},
                {"q": "What's the biggest problem?", "options": ["Pulling on the leash", "Jumping on people", "Not coming back", "Barking"]},
                {"q": "Group or private?", "options": ["Group class", "Private sessions"]},
            ],
            "results": {
                "Puppy": ("Puppy foundations", "Sit, stay, come and calm greetings, while your puppy is learning fastest."),
                "Under 2 years": ("Teen dog reset", "Leash manners and reliable recall for dogs testing the rules."),
                "Adult": ("Adult dog plan", "Fix one habit at a time with short daily practice."),
            },
            "price": 95, "unit": "session",
        }},
    # ── florist
    "florist": {
        "theme": "florist", "hook": "bouquet", "noun": "order",
        "headline": "Build a bouquet. We'll deliver it.",
        "sub": "Fresh flowers from {name} in {city}. Pick your stems, choose the wrap, and send it today.",
        "cta": "Build a bouquet",
        "services": [_s("Same-day bouquet", "Designer's choice, delivered today.", 0, 65),
                     _s("Sympathy flowers", "Arrangements and wreaths.", 0, 95),
                     _s("Weekly flowers", "For offices and restaurants.", 0, 55),
                     _s("Wedding consultation", "Bouquets, centrepieces and arches.", 45, 0)],
    },
    # ── shop
    "alterations tailor": {"theme": "shop", "hook": "booking", "noun": "fitting",
        "headline": "Bring it in. We'll make it fit.",
        "sub": "Alterations and tailoring in {city}. Book a fitting and skip the wait.",
        "cta": "Book a fitting",
        "services": [_s("Hem pants or jeans", "", 15, 18), _s("Take in a suit", "", 30, 65), _s("Dress alterations", "", 30, 45), _s("Zipper replacement", "", 15, 25)]},
    "photography studio": {"theme": "shop", "hook": "booking", "noun": "session",
        "headline": "Pick a session. We'll make the photos.",
        "sub": "Portraits, families and headshots in {city}.",
        "cta": "Book a session",
        "services": [_s("Headshots", "15 edited photos.", 30, 175), _s("Family session", "40 edited photos.", 60, 325), _s("Event coverage", "Per hour.", 60, 200)]},
    "jewellery store": {"theme": "shop", "hook": "booking", "noun": "appointment",
        "headline": "Rings, repairs and custom pieces.",
        "sub": "Fine jewellery in {city}. Book a private appointment.",
        "cta": "Book an appointment",
        "services": [_s("Engagement ring consultation", "", 45, 0), _s("Ring resizing", "", 15, 45), _s("Watch battery", "", 10, 15), _s("Custom design", "", 60, 0)]},
    "printing shop": {"theme": "shop", "hook": "estimate", "noun": "order",
        "headline": "Price your print job now.",
        "sub": "Business cards, flyers and signs in {city}. Get a price and send your file.",
        "cta": "Get my price",
        "services": [_s("Business cards", "500, double-sided.", 0, 60), _s("Flyers", "1,000, full colour.", 0, 180), _s("Banners", "Per square foot.", 0, 12)],
        "jobs": [{"name": "Business cards", "unit": "cards", "min": 250, "max": 5000, "step": 250, "def": 500, "base": 25, "rate": 0.07},
                 {"name": "Flyers", "unit": "flyers", "min": 100, "max": 10000, "step": 100, "def": 1000, "base": 40, "rate": 0.14},
                 {"name": "Vinyl banner", "unit": "sq ft", "min": 6, "max": 200, "step": 2, "def": 24, "base": 20, "rate": 9}]},
    "trophy shop": {"theme": "shop", "hook": "estimate", "noun": "order",
        "headline": "Price your awards in seconds.",
        "sub": "Trophies, medals and engraving in {city}.",
        "cta": "Get my price",
        "services": [_s("Medals", "With ribbon and engraving.", 0, 8), _s("Trophies", "From small to tall.", 0, 25), _s("Plaques", "Engraved.", 0, 45)],
        "jobs": [{"name": "Medals", "unit": "medals", "min": 10, "max": 300, "step": 5, "def": 40, "base": 20, "rate": 6.5},
                 {"name": "Trophies", "unit": "trophies", "min": 1, "max": 100, "step": 1, "def": 12, "base": 20, "rate": 22},
                 {"name": "Plaques", "unit": "plaques", "min": 1, "max": 50, "step": 1, "def": 5, "base": 15, "rate": 42}]},
}

# Trades that only exist in the old config get the generic estimate setup
_TRADE_GENERIC = {
    "roofing contractor": ("Roof replacement", "squares (100 sq ft)", 10, 40, 1, 20, 1500, 520),
    "hvac contractor": ("Furnace or AC install", "sq ft of home", 800, 4000, 100, 1800, 3200, 0.9),
    "locksmith": ("Rekey locks", "locks", 1, 10, 1, 3, 60, 35),
    "pest control": ("Pest treatment", "sq ft of home", 500, 4000, 100, 1500, 150, 0.06),
    "carpet cleaning": ("Carpet cleaning", "rooms", 1, 10, 1, 3, 60, 45),
    "window cleaning": ("Window cleaning", "windows", 5, 60, 1, 20, 60, 8),
    "snow removal": ("Driveway clearing (season)", "car lengths", 2, 8, 1, 3, 250, 90),
    "fence contractor": ("New fence", "linear feet", 20, 300, 5, 100, 400, 48),
    "moving company": ("Local move", "bedrooms", 1, 5, 1, 2, 300, 260),
}
for _cat, (_job, _unit, _mn, _mx, _st, _df, _base, _rate) in _TRADE_GENERIC.items():
    CATEGORIES[_cat] = {
        "theme": "trades", "hook": "estimate", "noun": "visit",
        "headline": "See the price before we show up.",
        "sub": "{name} in {city}. Pick the job, set the size and get a price range now.",
        "cta": "Get my estimate",
        "services": [_s(_job, "Quote confirmed on site.", 0, None), _s("Free estimate visit", "We measure and confirm the price.", 30, 0)],
        "jobs": [{"name": _job, "unit": _unit, "min": _mn, "max": _mx, "step": _st, "def": _df, "base": _base, "rate": _rate}],
    }

DEFAULT = {
    "theme": "shop", "hook": "booking", "noun": "appointment",
    "headline": "Book with us in under a minute.",
    "sub": "{name} in {city}. Pick a service, choose a time and you're booked.",
    "cta": "Book now",
    "services": [_s("Consultation", "Tell us what you need.", 30, 0), _s("Standard service", "", 60, None), _s("Follow-up", "", 30, None)],
}

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

ESTIMATE_URGENCY = [["Flexible", 0.92], ["Within a week", 1.0], ["Urgent (48 h)", 1.35]]

ABOUT = {
    "care": "{name} is a {kind} in {city}. We listen first, explain what's going on in plain words, and treat you like a person, not a file.",
    "trades": "{name} serves {city} and the rest of Ottawa. We show up when we say we will, quote before we start, and clean up before we leave.",
    "food": "{name} has been feeding {city} with food made the way we like to eat it. Order ahead and it's ready when you walk in.",
    "barber": "{name} is a neighbourhood barbershop in {city}. Good cuts, good conversation, and no long waits when you book ahead.",
    "salon": "{name} is a {kind} in {city}. Take an hour for yourself. We'll take care of the rest.",
    "pro": "{name} works with people and businesses in {city} and across Ottawa. Straight answers, clear fees and a call back when we say.",
    "gym": "{name} helps people in {city} get stronger, move better and stick with it. Every plan starts where you are today.",
    "kids": "{name} works with families in {city}. Small groups, patient people and regular updates for parents.",
    "pets": "{name} cares for pets in {city} like they're our own. Calm visits, clear prices and time for your questions.",
    "florist": "{name} makes flowers by hand in {city}, for birthdays, apologies, thank-yous and every day in between.",
    "shop": "{name} serves customers in {city} and across Ottawa, with careful work and a fair price.",
}


def display_name(name):
    """Name as people say it: drop SEO tails after ' | ' and fix ALL-CAPS names.
    'THE CHIC NAIL LOUNGE | Ottawa's Luxury Beauty Club' -> 'The Chic Nail Lounge'."""
    import string
    n = (name or "").strip()
    head = re.split(r"\s+\|\s+", n)[0].strip()
    if len(head) >= 3:
        n = head
    letters = [c for c in n if c.isalpha()]
    if len(letters) > 4 and all(c.isupper() for c in letters):
        n = string.capwords(n.lower())
    return n


def city_from_address(address, default="Ottawa"):
    """'1459 Ogilvie Rd Unit 3, Gloucester, ON K1J 7P3, Canada' -> 'Gloucester'."""
    parts = [p.strip() for p in (address or "").split(",") if p.strip()]
    for i, p in enumerate(parts):
        if re.match(r"^(ON|Ontario|QC|Québec|Quebec)\b", p) and i > 0:
            return parts[i - 1]
    return default


def street_from_address(address):
    parts = [p.strip() for p in (address or "").split(",") if p.strip()]
    return parts[0] if parts else ""


def config_for(category):
    return CATEGORIES.get((category or "").strip().lower(), DEFAULT)


def build_site(lead, slug, offer):
    """Everything the page needs, as one dict (serialized into the page as JSON)."""
    full = lead.get("business_name", "").strip()
    name = display_name(full)
    category = (lead.get("category") or "").strip().lower()
    cfg = config_for(category)
    theme = cfg["theme"]
    # Leads without an address (worldwide job posts, portfolio examples) get no city at all.
    city = lead.get("city") or (city_from_address(lead.get("address", "")) if lead.get("address") else "")

    def fill(s):
        if not city:
            s = s.replace(" in {city}", "").replace("{city}", "your area")
        return s.replace("{city}", city).replace("{name}", name)

    hours = [{"label": lbl, "days": d, "open": o, "close": c} for lbl, d, o, c in HOURS[theme]]
    site = {
        "v": 2,
        "name": name, "fullName": full, "slug": slug, "category": category or "business",
        "theme": theme, "hook": cfg["hook"], "noun": cfg.get("noun", "appointment"),
        "city": city,
        "address": (lead.get("address") or "").replace(", Canada", ""),
        "street": street_from_address(lead.get("address", "")),
        "phone": lead.get("phone", ""),
        "phoneRaw": re.sub(r"[^0-9+]", "", lead.get("phone", "")),
        "website": lead.get("website_url", ""),
        "headline": fill(cfg["headline"]),
        "sub": fill(cfg["sub"]),
        "cta": cfg["cta"],
        "primary": PRIMARY.get(category),
        "services": cfg.get("services", []),
        "hours": hours,
        "faq": [{"q": q, "a": a} for q, a in FAQ[theme]],
        "about": fill(ABOUT[theme].replace("{kind}", category or "business")),
        "gift": {"amounts": [25, 50, 100, 150]},
        "offer": offer,
    }
    for key in ("zones", "jobs", "menu", "popular", "staff", "matters", "quiz", "classes", "pets"):
        if key in cfg:
            site[key] = cfg[key]
    if cfg["hook"] == "estimate":
        site["urgency"] = ESTIMATE_URGENCY
    if cfg["hook"] == "order":
        site["menu"] = {k: [{"name": it[0], "desc": it[1], "price": it[2], "veg": len(it) > 3} for it in v]
                        for k, v in cfg["menu"].items()}
    return site


def fonts_url(theme):
    return f"https://fonts.googleapis.com/css2?{THEMES[theme]['fonts']}&display=swap"


def site_json(site):
    """JSON safe to drop inside <script type=application/json>."""
    return json.dumps(site, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
