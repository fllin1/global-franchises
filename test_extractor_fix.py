import asyncio
from src.backend.extractor import extract_profile_from_notes

notes = """
My full name Sebastian Sanchez
Orange County if possible.
Could do LA county (south)
Would like passive, semi-active.
Thinking services or low asset cost up front
(HVAC, plumbing, handyman, electrician,
cleaning, garage car repair, laundromats, car
washes) but I'm open to ideas.
My goal is to build a portfolio.
First one max $150-200K and then build from
there.
"""

async def main():
    profile = await extract_profile_from_notes(notes)
    print(f"Extracted State Code: {profile.state_code}")
    print(f"Extracted Location: {profile.location}")

if __name__ == "__main__":
    asyncio.run(main())


