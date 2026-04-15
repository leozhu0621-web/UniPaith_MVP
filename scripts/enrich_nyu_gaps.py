"""
Fill remaining NYU program gaps: 4 missing descriptions + 20 missing images.
Run after the enrich endpoint department-matching fix is deployed.

Usage: /Users/leozhu/Desktop/工作/Platform/UniPaith_MVP/unipaith-backend/.venv/bin/python scripts/enrich_nyu_gaps.py
"""
import asyncio
import json
import os
import sys

import httpx

API = os.environ.get("UNIPAITH_API_URL", "https://api.unipaith.co/api/v1")


async def get_admin_token() -> str:
    email = os.environ.get("UNIPAITH_ADMIN_EMAIL")
    password = os.environ.get("UNIPAITH_ADMIN_PASSWORD")
    if not email or not password:
        raise RuntimeError(
            "Set UNIPAITH_ADMIN_EMAIL and UNIPAITH_ADMIN_PASSWORD env vars"
        )
    async with httpx.AsyncClient(timeout=15) as c:
        resp = await c.post(f"{API}/auth/login", json={
            "email": email, "password": password,
        })
        return resp.json()["access_token"]


# --- Descriptions for the 4 duplicate-name programs ---

DESCRIPTIONS = [
    {
        "program_name": "Computer Science",
        "institution_name": "New York University",
        "department": "College of Arts & Science",
        "description_text": (
            "The Department of Computer Science, housed within the Courant Institute of "
            "Mathematical Sciences, trains students in foundational computer science principles "
            "alongside practical software development. The program covers both theory and "
            "applications of computing, combining practical programming experience with "
            "techniques for analyzing problems and designing computer algorithms.\n\n"
            "[Source: NYU Bulletin (bulletins.nyu.edu/undergraduate/arts-science/programs/computer-science-ba/)]"
        ),
    },
    {
        "program_name": "Computer Science",
        "institution_name": "New York University",
        "department": "Tandon School of Engineering",
        "description_text": (
            "The Computer Science BS program at Tandon covers a rigorous combination of "
            "fundamental computer science subjects \u2014 including object-oriented programming, "
            "computer architecture, and operating systems \u2014 and hands-on applications in "
            "critical domains. The program emphasizes research opportunities in specialized "
            "areas such as cybersecurity, big data, and game development.\n\n"
            "[Source: NYU Tandon (engineering.nyu.edu/academics/programs/computer-science-bs)]"
        ),
    },
    {
        "program_name": "Economics",
        "institution_name": "New York University",
        "department": "College of Arts & Science",
        "description_text": (
            "The Department of Economics prepares students to understand individual and group "
            "decision-making, the structure of markets and economies, and the relationship "
            "between regions within the global economy. Students gain exposure to both economic "
            "theory and practical applications, with opportunities to conduct independent "
            "research alongside distinguished faculty.\n\n"
            "[Source: NYU Bulletin (bulletins.nyu.edu/undergraduate/arts-science/programs/economics-ba/)]"
        ),
    },
    {
        "program_name": "Economics",
        "institution_name": "New York University",
        "department": "Stern School of Business",
        "description_text": (
            "The Economics program at Stern integrates economic theory with business applications "
            "across undergraduate, MBA, and PhD tracks. Faculty research spans industrial "
            "organization, macroeconomics, economic history, applied microeconomics, health "
            "economics, and behavioral economics, with students able to pursue concentrations "
            "in Business Economics or Econometrics & Quantitative Economics.\n\n"
            "[Source: NYU Stern (stern.nyu.edu/experience-stern/about/departments-centers-initiatives/"
            "academic-departments/economics)]"
        ),
    },
]

# --- Images for the 20 programs missing them ---
# Strategy:
#   - Tandon programs: department-specific images from engineering.nyu.edu (scrapable)
#   - Stern programs: Stern homepage carousel images (scrapable)
#   - CAS programs: NYU campus photos (already on app.unipaith.co)

# Tandon department images (all from engineering.nyu.edu)
TANDON_CS_IMG = "https://engineering.nyu.edu/sites/default/files/styles/content_header_default_1x/public/2018-03/orange-motherboard.jpg"
TANDON_ECE_IMG = "https://engineering.nyu.edu/sites/default/files/styles/cinema_medium_default_1x/public/2023-11/23-ECE_NYU_Tandon_0800_0.jpeg"
TANDON_MAE_IMG = "https://engineering.nyu.edu/sites/default/files/styles/content_header_default_1x/public/2025-12/071A7630.jpg"
TANDON_TMI_IMG = "https://engineering.nyu.edu/sites/default/files/styles/content_header_default_1x/public/2021-11/2019_ResearchExpo_146.jpeg"

# Stern homepage images
STERN_IMG_1 = "https://www.stern.nyu.edu/sites/default/files/styles/965w_x_564h/public/2026-01/stern_nyu_ad_convocation_homepage_1920_x_1280.jpg.webp?itok=5PWr06Ft"
STERN_IMG_2 = "https://www.stern.nyu.edu/sites/default/files/styles/965w_x_564h/public/2025-09/stern_business_spring_2025_homepage.png.webp?itok=sazQAaCh"

# NYU campus images (already on app.unipaith.co — no S3 download needed)
NYU_CAMPUS_1 = "https://app.unipaith.co/school-images/nyu-campus-1.jpg"
NYU_CAMPUS_2 = "https://app.unipaith.co/school-images/nyu-campus-2.jpg"
NYU_CAMPUS_3 = "https://app.unipaith.co/school-images/nyu-campus-3.jpg"

# Map each missing-image program to its best image source
PROGRAM_IMAGES = {
    # Stern programs → Stern images (need S3 download)
    ("Accounting", "Stern School of Business"): STERN_IMG_1,
    ("Business", "Stern School of Business"): STERN_IMG_2,
    ("Finance", "Stern School of Business"): STERN_IMG_1,
    ("Information Systems", "Stern School of Business"): STERN_IMG_2,
    ("Management", "Stern School of Business"): STERN_IMG_1,
    ("Economics", "Stern School of Business"): STERN_IMG_2,
    # Tandon programs → department images (need S3 download)
    ("Computer Science", "Tandon School of Engineering"): TANDON_CS_IMG,
    ("Electrical Engineering", "Tandon School of Engineering"): TANDON_ECE_IMG,
    ("Mechanical Engineering", "Tandon School of Engineering"): TANDON_MAE_IMG,
    ("Technology Management", "Tandon School of Engineering"): TANDON_TMI_IMG,
    # CAS programs → NYU campus photos (already on app.unipaith.co)
    ("Anthropology", "College of Arts & Science"): NYU_CAMPUS_1,
    ("Biology", "College of Arts & Science"): NYU_CAMPUS_2,
    ("Chemistry", "College of Arts & Science"): NYU_CAMPUS_3,
    ("Computer Science", "College of Arts & Science"): NYU_CAMPUS_1,
    ("Data Science", "College of Arts & Science"): NYU_CAMPUS_2,
    ("Economics", "College of Arts & Science"): NYU_CAMPUS_3,
    ("English", "College of Arts & Science"): NYU_CAMPUS_1,
    ("Environmental Studies", "College of Arts & Science"): NYU_CAMPUS_2,
    ("History", "College of Arts & Science"): NYU_CAMPUS_3,
    ("Linguistics", "College of Arts & Science"): NYU_CAMPUS_1,
}


async def main():
    token = await get_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=60, headers=headers) as c:
        # === Step 1: Download external images to S3 ===
        # Only download images that aren't already on app.unipaith.co
        external_urls = list({
            url for url in PROGRAM_IMAGES.values()
            if not url.startswith("https://app.unipaith.co/")
        })

        url_map = {}
        if external_urls:
            print(f"Step 1: Downloading {len(external_urls)} images to S3...")
            resp = await c.post(f"{API}/internal/download-images", json={
                "urls": external_urls, "prefix": "catalog/nyu",
            })
            img_data = resp.json()
            print(f"  Uploaded: {img_data['uploaded']}/{img_data['total']}")

            for r in img_data.get("results", []):
                if r.get("status") == "ok":
                    url_map[r["url"]] = r["s3_url"]
                    print(f"    OK: ...{r['url'][-50:]} -> {r['s3_url'][:60]}...")
                else:
                    print(f"    FAIL: {r['url'][:60]}... ({r.get('status')}: {r.get('error', r.get('code', '?'))})")
        else:
            print("Step 1: No external images to download (all on app.unipaith.co)")

        # === Step 2: Enrich descriptions (4 duplicate-name programs) ===
        print(f"\nStep 2: Enriching {len(DESCRIPTIONS)} programs with descriptions...")
        resp = await c.post(f"{API}/internal/enrich", json={
            "programs": DESCRIPTIONS,
        })
        desc_result = resp.json()
        print(f"  Result: {desc_result}")

        # === Step 3: Enrich images (20 programs) ===
        print(f"\nStep 3: Enriching {len(PROGRAM_IMAGES)} programs with images...")
        image_enrichments = []
        for (prog_name, dept), orig_url in PROGRAM_IMAGES.items():
            # Use S3 URL if downloaded, otherwise use the original (app.unipaith.co)
            final_url = url_map.get(orig_url, orig_url)
            image_enrichments.append({
                "program_name": prog_name,
                "institution_name": "New York University",
                "department": dept,
                "media_urls": [final_url],
            })

        # Batch in groups of 10
        for i in range(0, len(image_enrichments), 10):
            batch = image_enrichments[i:i + 10]
            resp = await c.post(f"{API}/internal/enrich", json={
                "programs": batch,
            })
            result = resp.json()
            print(f"  Batch {i // 10 + 1}: {result}")

        # === Step 4: Verify ===
        print("\nStep 4: Verifying...")
        resp = await c.get(f"{API}/programs", params={
            "institution_id": "c884adad-21b5-4dc3-b304-bfe1efcfc057",
            "page_size": 100,
        })
        data = resp.json()
        items = data.get("items", [])
        no_desc = [p for p in items if not p.get("description_text")]
        no_img = [p for p in items if not p.get("media_urls")]
        print(f"  Total programs: {len(items)}")
        print(f"  With description: {len(items) - len(no_desc)}/{len(items)}")
        print(f"  With images: {len(items) - len(no_img)}/{len(items)}")

        if no_desc:
            print(f"\n  Still missing descriptions:")
            for p in no_desc:
                print(f"    - {p['program_name']} [{p.get('department', 'no dept')}]")

        if no_img:
            print(f"\n  Still missing images:")
            for p in no_img:
                print(f"    - {p['program_name']} [{p.get('department', 'no dept')}]")

        if not no_desc and not no_img:
            print("\n  === ALL 61 PROGRAMS COMPLETE ===")


if __name__ == "__main__":
    asyncio.run(main())
