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
