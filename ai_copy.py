import json
import anthropic
from config import ANTHROPIC_API_KEY

FALLBACK_COPY = {
    "barbershop": {
        "tagline": "Ottawa's Favourite Barbershop, Right Here",
        "subheadline": "Sharp cuts and expert fades for Ottawa clients who care about their look."
    },
    "restaurant": {
        "tagline": "Real Flavour, Right in Your Neighbourhood",
        "subheadline": "Fresh, delicious food served with warmth at our Ottawa location."
    },
    "nail salon": {
        "tagline": "Beautiful Nails, Relaxing Experience Every Visit",
        "subheadline": "Ottawa's go-to nail salon for manicures, pedicures, and gel nails."
    },
    "dental clinic": {
        "tagline": "Gentle Dental Care Your Whole Family Will Love",
        "subheadline": "Comprehensive dental services with a caring touch in Ottawa."
    },
    "personal trainer": {
        "tagline": "Reach Your Fitness Goals Faster in Ottawa",
        "subheadline": "Personalized training programs that deliver real results for Ottawa residents."
    },
    "physiotherapy clinic": {
        "tagline": "Move Better, Feel Better, Recover Faster",
        "subheadline": "Evidence-based physiotherapy care tailored to your needs in Ottawa."
    },
    "tutoring": {
        "tagline": "Build Confidence, Improve Grades, Succeed",
        "subheadline": "Personalized tutoring sessions for Ottawa students of all ages."
    },
    "daycare": {
        "tagline": "A Safe, Nurturing Place for Your Child",
        "subheadline": "Loving, professional childcare for Ottawa families — full and part-time."
    },
    "alterations tailor": {
        "tagline": "Perfect Fit, Every Time, Right Here in Ottawa",
        "subheadline": "Expert clothing alterations and tailoring for Ottawa residents."
    },
    "plumber": {
        "tagline": "Fast, Reliable Plumbing When You Need It",
        "subheadline": "Ottawa's trusted plumbing service for homes and businesses."
    },
    "electrician": {
        "tagline": "Safe, Certified Electrical Work Done Right",
        "subheadline": "Licensed Ottawa electricians for residential and commercial projects."
    },
    "driving school": {
        "tagline": "Pass Your Road Test With Confidence",
        "subheadline": "Patient, experienced driving instructors helping Ottawa learners succeed."
    },
    "cleaning service": {
        "tagline": "Spotless Spaces, Stress-Free Living",
        "subheadline": "Reliable residential and commercial cleaning services across Ottawa."
    },
    "landscaping": {
        "tagline": "Transform Your Outdoor Space This Season",
        "subheadline": "Expert lawn care and landscaping for Ottawa homes and businesses."
    },
    "painting contractor": {
        "tagline": "Fresh Paint, Clean Finish, On Time",
        "subheadline": "Interior and exterior painting services trusted by Ottawa homeowners."
    },
    "law firm": {
        "tagline": "Ottawa Legal Counsel You Can Trust",
        "subheadline": "Experienced lawyers fighting for your rights and best interests."
    },
    "accountant": {
        "tagline": "Smart Accounting, Bigger Refunds, Less Stress",
        "subheadline": "Tax preparation, bookkeeping, and business advisory for Ottawa clients."
    },
    "real estate agent": {
        "tagline": "Buy, Sell, and Invest in Ottawa With Confidence",
        "subheadline": "Local market expertise and honest advice at every step."
    },
    "massage therapist": {
        "tagline": "Relief, Relaxation, and Recovery in Ottawa",
        "subheadline": "Registered massage therapists offering personalized treatment for pain and stress."
    },
    "veterinarian": {
        "tagline": "Compassionate Care for Ottawa's Beloved Pets",
        "subheadline": "Full-service veterinary clinic treating your animals like family."
    },
    "optometrist": {
        "tagline": "See Clearly, Live Fully — Ottawa Eye Care",
        "subheadline": "Comprehensive eye exams, designer frames, and contact lens fittings."
    },
    "auto repair": {
        "tagline": "Honest Mechanics Ottawa Drivers Rely On",
        "subheadline": "Quality repairs, transparent pricing, and a team that respects your time."
    },
    "florist": {
        "tagline": "Fresh Flowers, Handcrafted for Every Moment",
        "subheadline": "Custom bouquets, wedding florals, and same-day delivery across Ottawa."
    },
    "chiropractor": {
        "tagline": "Less Pain, More Movement — Starting Today",
        "subheadline": "Ottawa chiropractors specializing in back pain, neck pain, and sports injuries."
    },
    "mortgage broker": {
        "tagline": "Ottawa's Best Mortgage Rate Starts Here",
        "subheadline": "We compare dozens of lenders to get you the lowest rate — for free."
    },
    "insurance broker": {
        "tagline": "Better Coverage, Lower Premiums in Ottawa",
        "subheadline": "Independent brokers who shop the market so you don't have to."
    },
    "financial advisor": {
        "tagline": "Build Wealth and Retire With Confidence",
        "subheadline": "Personalized financial planning for Ottawa families and professionals."
    },
    "immigration consultant": {
        "tagline": "Your Path to Canada Starts Here",
        "subheadline": "Regulated consultants with a strong track record of successful applications."
    },
    "notary": {
        "tagline": "Fast, Professional Notary Services in Ottawa",
        "subheadline": "Notarization, affidavits, and real estate closings — done right."
    },
    "moving company": {
        "tagline": "Stress-Free Moving Done Right in Ottawa",
        "subheadline": "Professional movers who handle your belongings with care, on time."
    },
    "roofing contractor": {
        "tagline": "Ottawa Roofing That Lasts for Decades",
        "subheadline": "Licensed roofers delivering quality repairs and replacements with a warranty."
    },
    "hvac contractor": {
        "tagline": "Ottawa Comfort, Every Season of the Year",
        "subheadline": "Expert furnace, AC, and ventilation services — fast response, fair prices."
    },
    "locksmith": {
        "tagline": "Ottawa's Trusted Locksmith — 24/7 Service",
        "subheadline": "Fast lockout response, rekeying, and smart lock installations across Ottawa."
    },
    "pest control": {
        "tagline": "Pest-Free Guaranteed — Ottawa's Local Experts",
        "subheadline": "Safe, effective treatments for homes and businesses — family and pet friendly."
    },
    "carpet cleaning": {
        "tagline": "Deep Clean Results Ottawa Homeowners Love",
        "subheadline": "Professional steam cleaning for carpets, rugs, and upholstery."
    },
    "window cleaning": {
        "tagline": "Crystal-Clear Windows, Streak-Free Every Time",
        "subheadline": "Residential and commercial window cleaning across Ottawa and area."
    },
    "snow removal": {
        "tagline": "Ottawa Winter? We've Got You Covered",
        "subheadline": "Reliable snow removal with season contracts and 24-hour storm response."
    },
    "fence contractor": {
        "tagline": "Beautiful Fences Built to Last in Ottawa",
        "subheadline": "Wood, vinyl, and composite fencing installed by experienced contractors."
    },
    "acupuncture": {
        "tagline": "Natural Pain Relief and Healing in Ottawa",
        "subheadline": "Traditional acupuncture for chronic pain, anxiety, fertility, and wellness."
    },
    "psychologist": {
        "tagline": "Confidential Therapy for Ottawa Adults and Families",
        "subheadline": "Registered psychologists offering evidence-based care in a safe space."
    },
    "speech therapist": {
        "tagline": "Helping Ottawa Voices Be Heard",
        "subheadline": "Speech-language therapy for children and adults of all ages."
    },
    "dietitian": {
        "tagline": "Eat Better, Feel Better — Ottawa Nutrition",
        "subheadline": "Registered dietitian offering personalized meal plans and health coaching."
    },
    "naturopath": {
        "tagline": "Natural Health Solutions for Ottawa Patients",
        "subheadline": "Naturopathic medicine combining modern diagnostics with holistic care."
    },
    "yoga studio": {
        "tagline": "Find Strength, Balance, and Peace in Ottawa",
        "subheadline": "Yoga classes for every level in a warm, welcoming Ottawa studio."
    },
    "martial arts": {
        "tagline": "Build Confidence and Fitness Through Martial Arts",
        "subheadline": "Classes for kids and adults in karate, jiu-jitsu, and kickboxing."
    },
    "dance studio": {
        "tagline": "Where Ottawa's Dancers Find Their Passion",
        "subheadline": "Ballet, hip-hop, ballroom, and more — classes for all ages and levels."
    },
    "hair salon": {
        "tagline": "Ottawa's Favourite Hair Salon for Any Style",
        "subheadline": "Expert cuts, colour, and treatments — walk out loving your hair."
    },
    "eyebrow threading": {
        "tagline": "Perfect Brows, Every Visit in Ottawa",
        "subheadline": "Fast, precise threading and tinting for flawless eyebrows."
    },
    "tattoo shop": {
        "tagline": "Custom Tattoo Art Made in Ottawa",
        "subheadline": "Experienced artists, sterile studio, and designs as unique as you are."
    },
    "spa": {
        "tagline": "Your Ottawa Escape for Total Mind and Body Renewal",
        "subheadline": "Luxurious facials, body treatments, and relaxation therapies."
    },
    "makeup artist": {
        "tagline": "Ottawa's Premier Makeup Artist for Every Occasion",
        "subheadline": "Bridal, event, and editorial makeup that lasts and photographs beautifully."
    },
    "bakery": {
        "tagline": "Freshly Baked Goodness Every Morning in Ottawa",
        "subheadline": "Handcrafted breads, pastries, and custom cakes made with quality ingredients."
    },
    "catering": {
        "tagline": "Exceptional Food for Ottawa's Most Memorable Events",
        "subheadline": "Custom menus and professional service for weddings, corporate, and private events."
    },
    "cafe": {
        "tagline": "Ottawa's Best Coffee Is Waiting for You",
        "subheadline": "Expertly crafted espresso drinks, specialty coffee, and fresh pastries daily."
    },
    "pizza": {
        "tagline": "Ottawa's Favourite Pizza, Made Fresh Daily",
        "subheadline": "Classic and creative pies baked hot — dine in, takeout, or delivery."
    },
    "food truck": {
        "tagline": "Bold Street Food Hitting Ottawa's Best Spots",
        "subheadline": "Fresh, flavourful, fast — find us at markets, festivals, and events."
    },
    "photography studio": {
        "tagline": "Ottawa Moments Captured to Last a Lifetime",
        "subheadline": "Professional portraits, events, and commercial photography with heart."
    },
    "jewellery store": {
        "tagline": "Fine Jewellery for Ottawa's Most Special Moments",
        "subheadline": "Custom designs, engagement rings, and expert repairs — crafted with care."
    },
    "music school": {
        "tagline": "Discover the Joy of Music in Ottawa",
        "subheadline": "Private and group lessons for all ages, instruments, and skill levels."
    },
    "travel agency": {
        "tagline": "Your Dream Trip Starts at an Ottawa Travel Agent",
        "subheadline": "Custom vacations, cruises, and corporate travel planned with expert care."
    },
    "printing shop": {
        "tagline": "Ottawa Printing That Makes Your Brand Stand Out",
        "subheadline": "Business cards, banners, signage, and custom merchandise — fast turnaround."
    },
    "pet grooming": {
        "tagline": "Ottawa's Gentlest Pet Grooming Studio",
        "subheadline": "Professional grooming for dogs and cats in a calm, caring environment."
    },
    "dog training": {
        "tagline": "Better Behaviour, Happier Dogs in Ottawa",
        "subheadline": "Positive reinforcement training for puppies and adult dogs — real results."
    },
    "private investigator": {
        "tagline": "Discreet, Professional Investigations in Ottawa",
        "subheadline": "Licensed investigators delivering confidential, results-driven services."
    },
    "trophy shop": {
        "tagline": "Custom Awards and Recognition Made in Ottawa",
        "subheadline": "Trophies, plaques, medals, and engraving for sports, business, and events."
    },
}

_DEFAULT_FALLBACK = {
    "tagline": "Professional Services in Ottawa",
    "subheadline": "Quality service delivered with care for Ottawa residents and businesses."
}


def get_ai_copy(business_name: str, category: str) -> dict:
    """Call Claude Haiku to generate tagline + subheadline for a business.
    Falls back to FALLBACK_COPY if the API fails or returns invalid JSON."""
    prompt = (
        f"You are writing copy for a local Ottawa business website demo.\n"
        f"Business name: {business_name}\n"
        f"Category: {category}\n"
        f"City: Ottawa\n\n"
        f"Write a website hero section. Return ONLY valid JSON, nothing else:\n"
        f'{{"tagline": "6-8 word bold headline, no clichés", '
        f'"subheadline": "One sentence describing what they offer in Ottawa"}}'
    )

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=120,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text.strip()
        data = json.loads(text)
        if "tagline" in data and "subheadline" in data:
            return data
    except Exception:
        pass

    return FALLBACK_COPY.get(category, _DEFAULT_FALLBACK)
