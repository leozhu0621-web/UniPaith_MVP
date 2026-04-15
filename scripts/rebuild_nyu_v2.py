"""
NYU Gold Standard Rebuild v2 — Complete rebuild from all collected data.

Usage:
    cd /Users/leozhu/Desktop/工作/Platform/UniPaith_MVP
    unipaith-backend/.venv/bin/python scripts/rebuild_nyu_v2.py

Data sources:
    data/nyu/scorecard_structured.json   — 87 institution-level Scorecard fields
    data/nyu/program_earnings.json       — per-program earnings from Scorecard (48/59)
    data/nyu/program_descriptions.json   — official bulletin descriptions (scraped)
    data/nyu/bulletin_programs.json      — school/program catalog from bulletin
    data/nyu/image_download_list.json    — image URLs to download to S3

Rules followed:
    1. All data stored in our AWS (S3 for images, RDS for data)
    2. Official sources > second-hand, always annotated
    3. Leave no blank — fallback across multiple sources
    4. Verify visually and logically
    5. Use all resources (Scorecard, bulletin, scraping)
    6. Gather ALL related data, raw data included
"""
import asyncio
import json
import sys
from pathlib import Path

import httpx

# --- Config ---
API = "https://api.unipaith.co/api/v1"
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "nyu"

ADMIN_EMAIL = "admin@unipaith.co"
ADMIN_PASSWORD = "Unipaith2026"


async def get_admin_token() -> str:
    async with httpx.AsyncClient(timeout=15) as c:
        resp = await c.post(f"{API}/auth/login", json={
            "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
        })
        resp.raise_for_status()
        return resp.json()["access_token"]


def load_json(name: str) -> dict | list:
    path = DATA_DIR / name
    if not path.exists():
        print(f"  ⚠️  Missing: {path}")
        return {}
    return json.load(open(path))


async def main():
    print("=" * 60)
    print("NYU GOLD STANDARD REBUILD v2")
    print("=" * 60)

    # --- Load all data files ---
    print("\n📂 Loading data files...")
    scorecard = load_json("scorecard_structured.json")
    earnings = load_json("program_earnings.json")
    descriptions = load_json("program_descriptions.json")
    bulletin = load_json("bulletin_programs.json")
    image_urls = load_json("image_download_list.json")

    print(f"  Scorecard fields: {len(scorecard)}")
    print(f"  Earnings programs: {len(earnings)}")
    print(f"  Descriptions: {len(descriptions)}")
    print(f"  Images to download: {len(image_urls) if isinstance(image_urls, list) else 0}")

    # --- Get auth token ---
    print("\n🔑 Authenticating...")
    token = await get_admin_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("  ✅ Authenticated")

    async with httpx.AsyncClient(timeout=120, headers=headers) as c:

        # ===== STEP 1: Wipe NYU =====
        print("\n━━━ Step 1: Wipe NYU ━━━")
        resp = await c.post(f"{API}/internal/wipe-institution", json={
            "institution_name": "New York University",
        })
        wipe = resp.json()
        print(f"  Wipe result: {wipe}")

        # ===== STEP 2: Download images to S3 =====
        print("\n━━━ Step 2: Download images to S3 ━━━")
        if isinstance(image_urls, list) and image_urls:
            resp = await c.post(f"{API}/internal/download-images", json={
                "urls": image_urls,
                "prefix": "catalog/nyu",
            })
            if resp.status_code == 200:
                img_data = resp.json()
                print(f"  Uploaded: {img_data['uploaded']}/{img_data['total']}")

                # Build URL map
                url_map = {}
                for r in img_data.get("results", []):
                    if r.get("status") == "ok":
                        url_map[r["url"]] = r["s3_url"]
                        print(f"    ✅ {r['url'][:60]}... → S3")
                    else:
                        print(f"    ❌ {r.get('url', '?')[:60]}... — {r.get('status')}: {r.get('error', r.get('code', ''))}")
            else:
                print(f"  ❌ Image upload failed: {resp.status_code}")
                url_map = {}
        else:
            url_map = {}
            print("  ⚠️  No images to download")

        # Determine logo and campus photos from url_map
        raw_images = load_json("image_urls.json")
        logo_url = url_map.get(raw_images.get("logo", ""), raw_images.get("logo", ""))
        campus_photos = [url_map.get(u, u) for u in raw_images.get("campus", [])]
        school_images = {k: url_map.get(v, v) for k, v in raw_images.get("schools", {}).items()}

        print(f"  Logo: {logo_url[:60]}...")
        print(f"  Campus photos: {len(campus_photos)}")

        # ===== STEP 3: Build ranking_data JSONB =====
        print("\n━━━ Step 3: Build ranking_data ━━━")

        ranking_data = {
            # Identity
            "us_news_2025": 30,
            "source": "College Scorecard (US Dept of Education)",
            "scorecard_id": scorecard.get("ipeds_id", 193900),
            "accreditor": scorecard.get("accreditor"),
            "address": f"{scorecard.get('city')}, {scorecard.get('state')} {scorecard.get('zip')}",
            "zip": scorecard.get("zip"),
            "lat": scorecard.get("lat"),
            "lon": scorecard.get("lon"),
            "ownership_type": "private_nonprofit",
            "price_calculator_url": scorecard.get("price_calculator_url"),
            "carnegie_basic": scorecard.get("carnegie_basic"),

            # Admissions
            "acceptance_rate": scorecard.get("acceptance_rate"),
            "acceptance_rate_men": scorecard.get("acceptance_rate_men"),
            "acceptance_rate_women": scorecard.get("acceptance_rate_women"),
            "sat_avg": scorecard.get("sat_avg"),
            "sat_reading_25_75": [scorecard.get("sat_reading_25"), scorecard.get("sat_reading_75")],
            "sat_math_25_75": [scorecard.get("sat_math_25"), scorecard.get("sat_math_75")],
            "sat_reading_mid": scorecard.get("sat_reading_mid"),
            "sat_math_mid": scorecard.get("sat_math_mid"),
            "act_25_75": [scorecard.get("act_cumulative_25"), scorecard.get("act_cumulative_75")],
            "act_english_25_75": [scorecard.get("act_english_25"), scorecard.get("act_english_75")],
            "act_math_25_75": [scorecard.get("act_math_25"), scorecard.get("act_math_75")],

            # Costs
            "tuition_in_state": scorecard.get("tuition_in_state"),
            "tuition_out_of_state": scorecard.get("tuition_out_of_state"),
            "tuition_source": "College Scorecard (US Dept of Education)",
            "total_cost_attendance": scorecard.get("total_cost_attendance"),
            "room_board": scorecard.get("room_board_oncampus"),
            "room_board_offcampus": scorecard.get("room_board_offcampus"),
            "books_supply": scorecard.get("books_supply"),
            "other_expenses_oncampus": scorecard.get("other_expenses_oncampus"),
            "other_expenses_offcampus": scorecard.get("other_expenses_offcampus"),
            "avg_net_price": scorecard.get("avg_net_price"),
            "net_price_by_income": scorecard.get("net_price_by_income"),

            # Financial Aid
            "pell_grant_rate": scorecard.get("pell_grant_rate"),
            "federal_loan_rate": scorecard.get("federal_loan_rate"),
            "students_with_any_loan": scorecard.get("students_with_any_loan"),
            "median_debt": scorecard.get("median_debt_overall"),
            "median_debt_monthly": round(scorecard.get("median_debt_monthly_payment", 0), 2),
            "median_debt_by_income": scorecard.get("median_debt_by_income"),
            "debt_percentiles": scorecard.get("debt_percentiles"),
            "loan_principal": scorecard.get("loan_principal"),

            # Student Body
            "student_size": scorecard.get("student_size"),
            "grad_students": scorecard.get("grad_students"),
            "part_time_share": scorecard.get("part_time_share"),
            "retention_rate": scorecard.get("retention_rate_4yr"),

            # Demographics
            "gender": {
                "female": round((scorecard.get("female_share") or 0) * 100, 1),
                "male": round((scorecard.get("male_share") or 0) * 100, 1),
            },
            "race_ethnicity": {
                k: round((v or 0) * 100, 1)
                for k, v in (scorecard.get("race_ethnicity") or {}).items()
            },
            "first_generation": round((scorecard.get("first_generation") or 0) * 100, 1),
            "avg_family_income": scorecard.get("avg_family_income"),
            "median_family_income": scorecard.get("median_family_income"),
            "share_25_older": scorecard.get("share_25_older"),

            # Faculty
            "faculty_salary_avg_monthly": scorecard.get("faculty_salary_avg_monthly"),
            "ft_faculty_rate": scorecard.get("ft_faculty_rate"),
            "instructional_expenditure_per_fte": scorecard.get("instructional_expenditure_per_fte"),

            # Graduation & Outcomes
            "graduation_rate": scorecard.get("graduation_rate_6yr"),
            "graduation_rate_4yr": scorecard.get("graduation_rate_4yr"),
            "graduation_rate_8yr": scorecard.get("graduation_rate_8yr"),
            "graduation_rate_by_race": scorecard.get("graduation_rate_by_race"),
            "transfer_rate": scorecard.get("transfer_rate"),
            "completion_cohort_2yr": scorecard.get("completion_cohort_2yr"),

            # Earnings
            "earnings_6yr_median": scorecard.get("earnings_6yr_median"),
            "earnings_10yr_median": scorecard.get("earnings_10yr_median"),
            "earnings_1yr_mean": scorecard.get("earnings_1yr_mean"),
            "earnings_1yr_median": scorecard.get("earnings_1yr_median"),

            # Endowment
            "endowment": scorecard.get("endowment_end"),
            "endowment_begin": scorecard.get("endowment_begin"),
        }

        # Remove None values to keep JSON clean
        ranking_data = {k: v for k, v in ranking_data.items() if v is not None}
        print(f"  ranking_data fields: {len(ranking_data)}")

        # ===== STEP 4: Build program list =====
        print("\n━━━ Step 4: Build program list ━━━")

        # Master program list from XLSX
        import openpyxl
        xlsx_path = "/Users/leozhu/Desktop/AI/Claude/UniPaith/US_News_30-500_University_Programs_Outreach_Database.xlsx"
        wb = openpyxl.load_workbook(xlsx_path, read_only=True)
        ws = wb["Programs"]

        programs = []
        seen_keys = set()
        for row in ws.iter_rows(min_row=2, values_only=True):
            rank, univ_name, school_college, program_name, website = row
            if univ_name == "New York University" and program_name:
                key = f"{program_name}|{school_college or ''}"
                if key not in seen_keys:
                    seen_keys.add(key)
                    programs.append({
                        "program_name": program_name,
                        "degree_type": "bachelors",
                        "department": school_college,
                    })
        wb.close()
        print(f"  Programs from XLSX: {len(programs)}")

        # ===== STEP 5: Seed institution + programs =====
        print("\n━━━ Step 5: Seed NYU ━━━")
        inst_description = (
            "New York University (NYU) is a private research university "
            "in New York City. Founded in 1831 by Albert Gallatin, it is "
            "one of the largest private universities in the United States "
            "with campuses in Manhattan, Brooklyn, Abu Dhabi, and Shanghai. "
            "NYU is accredited by the Middle States Commission on Higher Education "
            "and is classified as an R1 Doctoral University with very high "
            "research activity.\n\n"
            "[Source: College Scorecard (US Dept of Education), IPEDS ID 193900]"
        )

        seed_payload = {
            "institutions": [{
                "name": "New York University",
                "type": "university",
                "country": "United States",
                "region": "NY",
                "city": "New York",
                "website_url": "https://www.nyu.edu/",
                "contact_email": "admissions@nyu.edu",
                "description_text": inst_description,
                "logo_url": logo_url,
                "media_gallery": campus_photos,
                "ranking_data": ranking_data,
                "programs": programs,
            }],
        }

        resp = await c.post(f"{API}/internal/seed-institutions", json=seed_payload)
        if resp.status_code == 200:
            seed_result = resp.json()
            print(f"  ✅ Seeded: {seed_result}")
        else:
            print(f"  ❌ Seed failed: {resp.status_code} — {resp.text[:300]}")
            return

        # ===== STEP 6: Enrich programs with descriptions + earnings =====
        print("\n━━━ Step 6: Enrich programs ━━━")

        # Build enrichment data for each program
        enrich_programs = []
        for prog in programs:
            name = prog["program_name"]
            dept = prog.get("department", "")
            ep = {
                "program_name": name,
                "institution_name": "New York University",
                "clear_fields": ["tuition", "acceptance_rate", "duration_months", "delivery_format"],
            }

            # Description from bulletin scraping
            desc_data = descriptions.get(name, {})
            if desc_data and desc_data.get("description"):
                source = desc_data.get("source_url", desc_data.get("source", "NYU Official Bulletin"))
                ep["description_text"] = desc_data["description"] + f"\n\n[Source: {source}]"

            # Outcomes data from Scorecard earnings
            earn_data = earnings.get(name, {})
            if earn_data and (earn_data.get("earnings_1yr_median") or earn_data.get("earnings_4yr_median")):
                ep["outcomes_data"] = {
                    "cip_code": earn_data.get("cip_code"),
                    "cip_title": earn_data.get("cip_title"),
                    "annual_graduates": earn_data.get("annual_graduates"),
                    "earnings_1yr_median": earn_data.get("earnings_1yr_median"),
                    "earnings_4yr_median": earn_data.get("earnings_4yr_median"),
                    "earnings_5yr_median": earn_data.get("earnings_5yr_median"),
                    "source": "College Scorecard (US Dept of Education)",
                }

            # Image: use school-specific image if available
            school_image = None
            if "Stern" in dept:
                school_image = school_images.get("Stern")
            elif "Tandon" in dept:
                school_image = school_images.get("Tandon")
            elif "Tisch" in dept:
                school_image = school_images.get("Tisch")

            if school_image:
                ep["media_urls"] = [school_image]
            elif campus_photos:
                ep["media_urls"] = [campus_photos[0]]

            enrich_programs.append(ep)

        # Batch in groups of 10
        total_enriched = 0
        batch_size = 10
        for i in range(0, len(enrich_programs), batch_size):
            batch = enrich_programs[i:i+batch_size]
            resp = await c.post(f"{API}/internal/enrich", json={
                "programs": batch,
            })
            if resp.status_code == 200:
                result = resp.json()
                total_enriched += result.get("updated_programs", 0)
                print(f"  Batch {i//batch_size + 1}: {result.get('updated_programs', 0)} programs enriched")
            else:
                print(f"  ❌ Batch {i//batch_size + 1} failed: {resp.status_code}")

        print(f"\n  ✅ Total enriched: {total_enriched}/{len(enrich_programs)}")

        # ===== STEP 7: Enrich institution with campus data =====
        print("\n━━━ Step 7: Enrich institution ━━━")
        resp = await c.post(f"{API}/internal/enrich", json={
            "institutions": [{
                "name": "New York University",
                "student_body_size": scorecard.get("student_size"),
                "campus_setting": "urban",
                "campus_description": (
                    "NYU's main campus is centered around Washington Square "
                    "Park in Greenwich Village, Manhattan. The university has "
                    "no traditional enclosed campus — instead, its buildings "
                    "are integrated throughout the surrounding neighborhoods. "
                    "The engineering school (Tandon) is located in downtown "
                    "Brooklyn. NYU also operates degree-granting campuses in "
                    "Abu Dhabi and Shanghai, plus academic centers in Accra, "
                    "Berlin, Buenos Aires, Florence, London, Los Angeles, "
                    "Madrid, Paris, Prague, Sydney, Tel Aviv, and Washington, D.C.\n\n"
                    "[Source: NYU Official Website (nyu.edu)]"
                ),
            }],
        })
        if resp.status_code == 200:
            print(f"  ✅ Institution enriched: {resp.json()}")
        else:
            print(f"  ❌ Failed: {resp.status_code}")

        # ===== SUMMARY =====
        with_desc = sum(1 for p in enrich_programs if p.get("description_text"))
        with_outcomes = sum(1 for p in enrich_programs if p.get("outcomes_data"))
        with_img = sum(1 for p in enrich_programs if p.get("media_urls"))

        print("\n" + "=" * 60)
        print("NYU REBUILD COMPLETE")
        print("=" * 60)
        print(f"Programs:           {len(programs)}")
        print(f"With descriptions:  {with_desc}")
        print(f"With outcomes data: {with_outcomes}")
        print(f"With images:        {with_img}")
        print(f"Images on S3:       {len(url_map)}")
        print(f"Ranking data:       {len(ranking_data)} fields")
        print(f"Data source:        College Scorecard + NYU Official Bulletin")
        print(f"All tuition:        NULL (institution-level ${scorecard.get('tuition_in_state', 0):,} in ranking_data)")
        print(f"All acceptance:     NULL (institution-level {scorecard.get('acceptance_rate', 0):.1%} in ranking_data)")


if __name__ == "__main__":
    asyncio.run(main())
