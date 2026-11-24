import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import re
import time
import urllib3
urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
}

def normalize_name(name: str) -> str:
    if not name:
        return ""
    # remove legal prefixes/suffixes, punctuation, and common terms
    cleaned = re.sub(r"\b(pvt|ltd|limited|private|llp|foundation|society|inc|technologies|solutions|accelerator|program)\b", "", name.lower())
    return re.sub(r"[^a-z0-9]", "", cleaned).strip()

def clean_text(text) -> str:
    if text is None:
        return ""
    if isinstance(text, list):
        return ", ".join(filter(bool, [clean_text(i) for i in text]))
    if isinstance(text, dict):
        return ", ".join(filter(bool, [f"{k}: {v}" for k, v in text.items()]))
    return re.sub(r"\s+", " ", str(text)).strip()

# ---------------------------------------------------------
# SOURCE 1: MeitY Startup Hub (MSH Accelerators API)
# ---------------------------------------------------------
def scrape_meity_accelerators() -> list[dict]:
    url = "https://api.meity.gov.in/accelerators/list"
    print(f"[MeitY Startup Hub] Fetching accelerators from {url}...")
    records = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25, verify=False)
        if resp.status_code == 200:
            data = resp.json()
            results = data.get("results", [])
            for item in results:
                name = clean_text(item.get("name", ""))
                if not name:
                    continue
                website = clean_text(item.get("website_url", ""))
                city = clean_text(item.get("city", ""))
                state = clean_text(item.get("state", ""))
                desc = clean_text(item.get("full_description", ""))
                domain = clean_text(item.get("domain", ""))
                sector = clean_text(item.get("sector", ""))

                focus = " | ".join(filter(bool, [domain, sector])) or "ICT / Emerging Technologies / Deep Tech"

                location_parts = [p for p in [city, state] if p]
                location = ", ".join(location_parts)

                records.append({
                    "name": name,
                    "category": "Accelerator",
                    "type": "Govt-backed / MeitY Deep-Tech Hub",
                    "city": city,
                    "state": state,
                    "location": location,
                    "sector_or_stage": focus,
                    "description": desc[:300] if desc else "MeitY Startup Hub recognized technology accelerator.",
                    "website": website,
                    "email": clean_text(item.get("email", "")),
                    "source_authority": "MeitY Startup Hub (MSH)",
                    "source_url": "https://msh.meity.gov.in"
                })
        print(f"  -> Successfully extracted {len(records)} accelerators from MeitY Startup Hub.")
    except Exception as e:
        print(f"  -> Error fetching MeitY accelerators: {e}")
    return records

# ---------------------------------------------------------
# SOURCE 2: StartupGrantsIndia (Aggregated Ecosystem Accelerators)
# ---------------------------------------------------------
def scrape_ecosystem_accelerators(max_pages: int = 25) -> list[dict]:
    records = []
    base_url = "https://www.startupgrantsindia.com"
    seen_slugs = set()

    for page_num in range(1, max_pages + 1):
        url = f"{base_url}/incubators/accelerators-in-india" if page_num == 1 else f"{base_url}/incubators/accelerators-in-india/page/{page_num}"
        print(f"[StartupGrantsIndia] Scraping directory page {page_num}: {url}...")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20, verify=False)
            if resp.status_code != 200:
                print(f"  -> Page {page_num} returned status {resp.status_code}. Stopping pagination.")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            # All provider cards point to /providers/<slug>
            provider_links = soup.find_all("a", href=re.compile(r"^/providers/[a-z0-9-]+$"))

            if not provider_links:
                print(f"  -> No more provider cards on page {page_num}.")
                break

            page_added = 0
            for link in provider_links:
                href = link.get("href")
                if not href or href in seen_slugs:
                    continue
                seen_slugs.add(href)

                card_text = link.get_text(separator="\n", strip=True)
                lines = [l.strip() for l in card_text.split("\n") if l.strip()]

                if not lines:
                    continue

                name = lines[0]
                # parse location and description
                location = ""
                city = ""
                state = ""
                stats_or_stage = ""
                desc = ""

                for line in lines[1:]:
                    if "," in line and not location:
                        location = line
                        parts = [p.strip() for p in line.split(",")]
                        city = parts[0]
                        state = parts[1] if len(parts) > 1 else ""
                    elif ("startups" in line.lower() or "cohort" in line.lower() or "month" in line.lower() or "stage" in line.lower() or "+" in line) and not stats_or_stage:
                        stats_or_stage = line
                    elif len(line) > 25 and not desc:
                        desc = line

                records.append({
                    "name": clean_text(name),
                    "category": "Accelerator",
                    "type": "Private / VC / Ecosystem Accelerator",
                    "city": clean_text(city),
                    "state": clean_text(state),
                    "location": clean_text(location),
                    "sector_or_stage": clean_text(stats_or_stage) or "Early / Growth Stage Startup Acceleration",
                    "description": clean_text(desc) or f"Startup accelerator program listed on Startup Grants India.",
                    "website": f"{base_url}{href}",
                    "email": "",
                    "source_authority": "StartupGrantsIndia Directory",
                    "source_url": url,
                    "provider_slug": href
                })
                page_added += 1

            print(f"  -> Extracted {page_added} accelerators from page {page_num} (Total so far: {len(records)})")
            if page_added == 0:
                break

            time.sleep(0.5)  # Politeness interval
        except Exception as e:
            print(f"  -> Error scraping page {page_num}: {e}")
            break

    print(f"  -> Total ecosystem accelerators extracted: {len(records)}")
    return records

# ---------------------------------------------------------
# SOURCE 3: Top Tier National & VC Accelerators Seed Data
# (Ensuring flagship institutional & top VC cohorts are present)
# ---------------------------------------------------------
def get_flagship_accelerators() -> list[dict]:
    flagships = [
        {
            "name": "Surge (Peak XV Partners)",
            "category": "Accelerator",
            "type": "VC-backed Accelerator",
            "city": "Bengaluru",
            "state": "Karnataka",
            "location": "Bengaluru, Karnataka",
            "sector_or_stage": "Pre-seed & Seed | Tech, Fintech, AI, SaaS, Consumer",
            "description": "Rapid scale-up program for early-stage startups in India and Southeast Asia offering up to $3M seed capital, company-building workshops, and global mentor access.",
            "website": "https://www.surgeahead.com",
            "email": "surge@peakxv.com",
            "source_authority": "Ecosystem Registry",
            "source_url": "https://www.surgeahead.com"
        },
        {
            "name": "Accel Atoms",
            "category": "Accelerator",
            "type": "VC-backed Accelerator",
            "city": "Bengaluru",
            "state": "Karnataka",
            "location": "Bengaluru, Karnataka",
            "sector_or_stage": "Pre-seed | AI & Emerging Tech, Industry 5.0",
            "description": "Accel's pre-seed accelerator program providing up to $500k in non-dilutive/uncapped funding, 1:1 mentorship from Accel partners, and $5M+ in perks.",
            "website": "https://atoms.accel.com",
            "email": "atoms@accel.com",
            "source_authority": "Ecosystem Registry",
            "source_url": "https://atoms.accel.com"
        },
        {
            "name": "100X.VC",
            "category": "Accelerator",
            "type": "VC-backed Accelerator",
            "city": "Mumbai",
            "state": "Maharashtra",
            "location": "Mumbai, Maharashtra",
            "sector_or_stage": "Class 01-12 Cohorts | Sector Agnostic Seed",
            "description": "India's first venture fund to invest in early-stage startups using iSAFE (India Simple Agreement for Future Equity) notes, conducting cohort masterclasses and VC pitch days.",
            "website": "https://www.100x.vc",
            "email": "pitch@100x.vc",
            "source_authority": "Ecosystem Registry",
            "source_url": "https://www.100x.vc"
        },
        {
            "name": "Antler India",
            "category": "Accelerator",
            "type": "VC-backed Accelerator / Day 0 Co-founder",
            "city": "Bengaluru",
            "state": "Karnataka",
            "location": "Bengaluru, Karnataka",
            "sector_or_stage": "Pre-seed / Day Zero | AI, Web3, Fintech, Climate",
            "description": "Global early-stage VC providing pre-seed funding, co-founder matching, and hands-on cohort acceleration for exceptional founders.",
            "website": "https://www.antler.co/location/india",
            "email": "india@antler.co",
            "source_authority": "Ecosystem Registry",
            "source_url": "https://www.antler.co/location/india"
        },
        {
            "name": "Google for Startups Accelerator India",
            "category": "Accelerator",
            "type": "Corporate Tech Accelerator",
            "city": "Bengaluru",
            "state": "Karnataka",
            "location": "Bengaluru, Karnataka",
            "sector_or_stage": "3-Month Cohort | AI/ML, Cloud, Deep Tech",
            "description": "Three-month equity-free accelerator program for Indian startups using AI/ML, offering Google mentorship, product credits, and design sprints.",
            "website": "https://startup.google.com/accelerator/india/",
            "email": "startups-india@google.com",
            "source_authority": "Ecosystem Registry",
            "source_url": "https://startup.google.com/accelerator/india/"
        },
        {
            "name": "Microsoft for Startups Pegasus",
            "category": "Accelerator",
            "type": "Corporate Tech Accelerator",
            "city": "Bengaluru",
            "state": "Karnataka",
            "location": "Bengaluru, Karnataka",
            "sector_or_stage": "Enterprise B2B, AI, SaaS",
            "description": "Program connecting growth-stage B2B startups with enterprise customers, Azure credits, and dedicated Microsoft technical architecture advisors.",
            "website": "https://www.microsoft.com/en-us/startups",
            "email": "msstartupsindia@microsoft.com",
            "source_authority": "Ecosystem Registry",
            "source_url": "https://www.microsoft.com/en-us/startups"
        },
        {
            "name": "T-Hub (Lab32 & T-Angel)",
            "category": "Accelerator",
            "type": "State / Ecosystem Innovation Hub",
            "city": "Hyderabad",
            "state": "Telangana",
            "location": "Hyderabad, Telangana",
            "sector_or_stage": "Market Readiness & Investment Acceleration",
            "description": "World's largest innovation campus running Lab32 seed accelerator and T-Angel investment cohort, connecting startups with marquee corporate partners and VCs.",
            "website": "https://t-hub.co",
            "email": "programs@t-hub.co",
            "source_authority": "Govt of Telangana / Ecosystem Hub",
            "source_url": "https://t-hub.co"
        },
        {
            "name": "CIIE.CO / IIMA Ventures",
            "category": "Accelerator",
            "type": "Academic & Seed Innovation Platform",
            "city": "Ahmedabad",
            "state": "Gujarat",
            "location": "Ahmedabad, Gujarat",
            "sector_or_stage": "Deeptech, Climate, Inclusive Tech",
            "description": "The Innovation Continuum founded at IIM Ahmedabad, running accelerators, Bharat Inclusion Seed Fund, and INFUSE climate ventures.",
            "website": "https://iimaventures.com",
            "email": "ciie@iima.ac.in",
            "source_authority": "IIM Ahmedabad / DPIIT",
            "source_url": "https://iimaventures.com"
        },
        {
            "name": "SINE IIT Bombay (Accelerate program)",
            "category": "Accelerator",
            "type": "Academic Tech Accelerator",
            "city": "Mumbai",
            "state": "Maharashtra",
            "location": "Mumbai, Maharashtra",
            "sector_or_stage": "Deeptech, Semiconductors, Defense Tech",
            "description": "Society for Innovation and Development at IIT Bombay, supporting deep-tech and hardware startups with dedicated accelerator tracks.",
            "website": "https://sineiitb.org",
            "email": "sine@sineiitb.org",
            "source_authority": "IIT Bombay / DST NIDHI",
            "source_url": "https://sineiitb.org"
        },
        {
            "name": "NSRCEL IIM Bangalore (Launchpad & Velocity)",
            "category": "Accelerator",
            "type": "Academic Business Accelerator",
            "city": "Bengaluru",
            "state": "Karnataka",
            "location": "Bengaluru, Karnataka",
            "sector_or_stage": "Early Stage to Growth | Women Founders, Mobility, Health",
            "description": "IIM Bangalore's flagship entrepreneurship centre running Velocity 3-month growth accelerator and specialized sector cohorts.",
            "website": "https://nsrcel.org",
            "email": "info@nsrcel.org",
            "source_authority": "IIM Bangalore / AIM NITI Aayog",
            "source_url": "https://nsrcel.org"
        }
    ]
    return flagships

# ---------------------------------------------------------
# MASTER PIPELINE EXECUTION & DEDUPLICATION
# ---------------------------------------------------------
def run_phase1_pipeline():
    print("==================================================")
    print("STARTING PHASE 1: ACCELERATOR MASTER EXTRACTOR")
    print("==================================================")

    # 1. Scrape MeitY Startup Hub Accelerators
    msh_data = scrape_meity_accelerators()

    # 2. Scrape Ecosystem Accelerators Directory
    eco_data = scrape_ecosystem_accelerators(max_pages=25)

    # 3. Flagship Top-Tier Accelerators
    flagship_data = get_flagship_accelerators()

    # Combine all records
    all_records = flagship_data + msh_data + eco_data
    df = pd.DataFrame(all_records)

    print(f"\nRaw total records gathered: {len(df)}")
    if df.empty:
        print("No records extracted.")
        return

    # Add normalized key for deduplication
    df["norm_key"] = df["name"].apply(normalize_name)

    # Priority ranking for deduplication: flagships first, then richer websites/emails
    df["has_email"] = df["email"].apply(lambda x: 1 if x and "@" in str(x) else 0)
    df["has_website"] = df["website"].apply(lambda x: 1 if x and "http" in str(x) else 0)

    # Sort so best records stay on top
    df = df.sort_values(by=["has_email", "has_website"], ascending=[False, False])
    df = df.drop_duplicates(subset=["norm_key"], keep="first")
    df = df.drop(columns=["norm_key", "has_email", "has_website"])

    # If provider_slug is present, clean it up
    if "provider_slug" in df.columns:
        df = df.drop(columns=["provider_slug"])

    # Sort alphabetically by Name
    df = df.sort_values(by="name").reset_index(drop=True)

    # Ensure all expected columns are nicely arranged
    cols = [
        "name", "category", "type", "city", "state", "location",
        "sector_or_stage", "description", "website", "email",
        "source_authority", "source_url"
    ]
    df = df[[c for c in cols if c in df.columns]]

    csv_path = "india_accelerators_master.csv"
    xlsx_path = "india_accelerators_master.xlsx"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_excel(xlsx_path, index=False, engine="openpyxl")

    print("\n==================================================")
    print(f"SUCCESS: Saved {len(df)} unique accelerators to:")
    print(f" - {csv_path}")
    print(f" - {xlsx_path}")
    print("==================================================")

    # Print summary statistics
    print("\n--- Summary by Source Authority ---")
    print(df["source_authority"].value_counts())

    print("\n--- Summary by Type ---")
    print(df["type"].value_counts())

    print("\n--- Top States ---")
    print(df["state"].replace("", "Unspecified").value_counts().head(10))

if __name__ == "__main__":
    run_phase1_pipeline()
