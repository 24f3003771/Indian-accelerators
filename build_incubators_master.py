import requests
from bs4 import BeautifulSoup
import pdfplumber
import pandas as pd
import io
import json
import re
import urllib3
urllib3.disable_warnings()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
}

def clean_text(text) -> str:
    if text is None:
        return ""
    if isinstance(text, list):
        return ", ".join(filter(bool, [clean_text(i) for i in text]))
    if isinstance(text, dict):
        return ", ".join(filter(bool, [f"{k}: {v}" for k, v in text.items()]))
    return re.sub(r"\s+", " ", str(text)).strip()

def normalize_name(name: str) -> str:
    if not name:
        return ""
    cleaned = re.sub(r"\b(pvt|ltd|limited|private|llp|foundation|society|inc|technologies|solutions|incubator|incubation|centre|center|technology|business|tbi|aic|acic)\b", "", name.lower())
    return re.sub(r"[^a-z0-9]", "", cleaned).strip()

# ---------------------------------------------------------
# SOURCE 1: Startup India Seed Fund Scheme (SISFS - DPIIT)
# ---------------------------------------------------------
def scrape_sisfs_incubators() -> list[dict]:
    print("[SISFS - DPIIT] Extracting approved seed-fund incubators...")
    records = []
    try:
        # Load pre-captured or fetch from API
        url = "https://seedfundapi.startupindia.gov.in:3535/api/portfoliofilter"
        resp = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        data = resp.json().get("data", []) if resp.status_code == 200 else []
        if not data:
            with open("sisfs_portfolio_full.json", "r", encoding="utf-8") as f:
                data = json.load(f)

        for item in data:
            name = clean_text(item.get("incubator_name", ""))
            if not name:
                continue
            city = clean_text(item.get("city", ""))
            state = clean_text(item.get("state", ""))
            sectors = clean_text(item.get("sectors", ""))
            desc = clean_text(item.get("description", ""))
            grant_amt = item.get("first_total_approved_amt", 0)

            grant_str = f"₹{grant_amt:,.0f}" if grant_amt else "Approved Seed Fund Disburser"

            records.append({
                "name": name,
                "category": "Govt-Approved Seed Fund Incubator / TBI",
                "type": "DPIIT Seed Fund Scheme (SISFS)",
                "city": city,
                "state": state,
                "location": f"{city}, {state}".strip(", "),
                "sector_or_stage": sectors or "Sector Agnostic / Multidisciplinary Seed",
                "description": desc or "Approved under DPIIT Startup India Seed Fund Scheme to disburse seed capital.",
                "website": "",
                "email": "",
                "funding_allocation": grant_str,
                "source_authority": "Startup India Seed Fund Scheme (DPIIT)",
                "source_url": "https://seedfund.startupindia.gov.in/portfolio"
            })
        print(f"  -> Extracted {len(records)} incubators from SISFS.")
    except Exception as e:
        print(f"  -> Error extracting SISFS: {e}")
    return records

# ---------------------------------------------------------
# SOURCE 2: NITI Aayog – Atal Innovation Mission (AIM)
# ---------------------------------------------------------
def scrape_aim_incubators() -> list[dict]:
    print("[NITI Aayog - AIM] Extracting Atal Incubation Centres (AICs)...")
    url = "https://aim.gov.in/pdf/AIC_List_data.pdf"
    records = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25, verify=False)
        if resp.status_code == 200:
            with pdfplumber.open(io.BytesIO(resp.content)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for t in tables:
                        for row in t:
                            if not row or not row[0] or "s.no" in str(row[0]).lower():
                                continue
                            name = clean_text(row[1]) if len(row) > 1 else ""
                            district = clean_text(row[2]) if len(row) > 2 else ""
                            state = clean_text(row[3]) if len(row) > 3 else ""
                            year = clean_text(row[4]) if len(row) > 4 else ""
                            if name:
                                records.append({
                                    "name": f"AIC - {name}" if not name.startswith("AIC") else name,
                                    "category": "Atal Incubation Centre (AIC)",
                                    "type": "NITI Aayog Atal Innovation Mission",
                                    "city": district,
                                    "state": state,
                                    "location": f"{district}, {state}".strip(", "),
                                    "sector_or_stage": "Grassroots, Tech, Social & Deep Innovation",
                                    "description": f"Established in {year} under NITI Aayog's Atal Innovation Mission with up to ₹10 Cr grant support.",
                                    "website": "https://aim.gov.in",
                                    "email": "",
                                    "funding_allocation": "AIM Grant-in-Aid (up to ₹10 Cr)",
                                    "source_authority": "Atal Innovation Mission (NITI Aayog)",
                                    "source_url": "https://aim.gov.in/selected-atal.php"
                                })
        print(f"  -> Extracted {len(records)} AIC incubators from AIM.")
    except Exception as e:
        print(f"  -> Error extracting AIM AICs: {e}")
    return records

# ---------------------------------------------------------
# SOURCE 3: MeitY Startup Hub (MSH Incubators API)
# ---------------------------------------------------------
def scrape_meity_incubators() -> list[dict]:
    print("[MeitY Startup Hub] Extracting TIDE 2.0 & GENESIS tech incubators...")
    records = []
    base_url = "https://api.meity.gov.in/incubators"
    for page in range(0, 10):
        url = f"{base_url}?page={page}&page_size=100"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20, verify=False)
            if resp.status_code != 200:
                break
            results = resp.json().get("results", [])
            if not results:
                break
            for item in results:
                name = clean_text(item.get("name", ""))
                if not name:
                    continue
                city = clean_text(item.get("city", ""))
                state = clean_text(item.get("state", ""))
                domain = clean_text(item.get("domain", ""))
                sector = clean_text(item.get("sector", ""))
                website = clean_text(item.get("website_url", ""))
                desc = clean_text(item.get("full_description", ""))

                focus = " | ".join(filter(bool, [domain, sector])) or "ICT, Deep Tech & Emerging Technologies"

                records.append({
                    "name": name,
                    "category": "MeitY TIDE 2.0 / GENESIS Technology Incubator",
                    "type": "MeitY Startup Hub (Central Govt)",
                    "city": city,
                    "state": state,
                    "location": f"{city}, {state}".strip(", "),
                    "sector_or_stage": focus,
                    "description": desc[:300] if desc else "Ministry of Electronics & IT (MeitY) recognized incubation centre.",
                    "website": website,
                    "email": clean_text(item.get("email", "")),
                    "funding_allocation": "MeitY TIDE 2.0 / GENESIS Support",
                    "source_authority": "MeitY Startup Hub (MSH)",
                    "source_url": "https://msh.meity.gov.in"
                })
        except Exception as e:
            print(f"  -> Error at MSH page {page}: {e}")
            break
    print(f"  -> Extracted {len(records)} tech incubators from MeitY Startup Hub.")
    return records

# ---------------------------------------------------------
# SOURCE 4: BIRAC BioNEST (Dept. of Biotechnology)
# ---------------------------------------------------------
def scrape_birac_bionest() -> list[dict]:
    print("[BIRAC - BioNEST] Extracting bio-incubators & life-sciences hubs...")
    url = "https://www.birac.nic.in/bionest.php"
    records = []
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find("table")
        if table:
            for row in table.find_all("tr")[1:]:
                cols = [clean_text(c.get_text(strip=True)) for c in row.find_all("td")]
                if len(cols) >= 2:
                    raw_name = cols[1]
                    # Parse location if included in name (e.g. "a-IDEA, NAARM-TBI, Rajendra Nagar, Hyderabad")
                    parts = [p.strip() for p in raw_name.split(",")]
                    name = parts[0]
                    location = ", ".join(parts[1:]) if len(parts) > 1 else ""
                    city = parts[-1] if len(parts) > 1 else ""

                    funded = cols[3] if len(cols) > 3 else "0"
                    total = cols[4] if len(cols) > 4 else "0"
                    space = cols[5] if len(cols) > 5 else ""

                    records.append({
                        "name": raw_name,
                        "category": "Bio-Incubator (BioNEST)",
                        "type": "BIRAC / Dept. of Biotechnology (Govt. of India)",
                        "city": city,
                        "state": "",
                        "location": location,
                        "sector_or_stage": "Biotechnology, MedTech, Life Sciences, Agri-Bio",
                        "description": f"BIRAC BioNEST supported incubator. Space: {space} sq ft | Supported incubatees: {total} (Funded: {funded}).",
                        "website": "https://www.birac.nic.in/bionest.php",
                        "email": "",
                        "funding_allocation": "BIRAC BioNEST Infrastructure & Seed Fund",
                        "source_authority": "BIRAC (Dept. of Biotechnology)",
                        "source_url": url
                    })
        print(f"  -> Extracted {len(records)} BioNEST incubators from BIRAC.")
    except Exception as e:
        print(f"  -> Error extracting BIRAC: {e}")
    return records

# ---------------------------------------------------------
# SOURCE 5: DST – NIDHI Technology Business Incubators (TBIs)
# ---------------------------------------------------------
def scrape_dst_nidhi() -> list[dict]:
    print("[DST - NIDHI] Extracting TBIs, i-TBIs, SSP, and CoEs from DST documents...")
    records = []

    # 1. NIDHI i-TBI
    url_itbi = "https://cdnbbsr.s3waas.gov.in/s312b1e42dc0746f22cf361267de07073f/uploads/2026/01/202601231040288767.pdf"
    try:
        r = requests.get(url_itbi, headers=HEADERS, timeout=20, verify=False)
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                for line in text.split("\n"):
                    if re.match(r"^\d+\s+", line):
                        # Line format: Sr. Host Institute State City Website Thrust Area Email
                        parts = line.split()
                        if len(parts) >= 5:
                            # find email and website
                            email = next((p for p in parts if "@" in p), "")
                            website = next((p for p in parts if "www." in p or "http" in p), "")
                            institute_tokens = [p for p in parts[1:] if p != email and p != website]
                            name = " ".join(institute_tokens[:4])
                            records.append({
                                "name": f"i-TBI {name}",
                                "category": "inclusive Technology Business Incubator (i-TBI)",
                                "type": "DST NIDHI (Dept. of Science & Technology)",
                                "city": institute_tokens[3] if len(institute_tokens) > 3 else "",
                                "state": institute_tokens[2] if len(institute_tokens) > 2 else "",
                                "location": "India",
                                "sector_or_stage": "Deep Tech, Energy, Basic Sciences, Digital Tech",
                                "description": f"DST NIDHI inclusive-TBI hosted at {name}.",
                                "website": f"https://{website}" if website and not website.startswith("http") else website,
                                "email": email,
                                "funding_allocation": "DST NIDHI Grant Support",
                                "source_authority": "Dept. of Science & Technology (DST - NIDHI)",
                                "source_url": "https://nidhi.dst.gov.in"
                            })
        print(f"  -> Extracted {len(records)} i-TBIs from DST.")
    except Exception as e:
        print(f"  -> Error parsing i-TBI PDF: {e}")

    # 2. NIDHI Seed Support Program (SSP) TBIs
    url_ssp = "https://cdnbbsr.s3waas.gov.in/s312b1e42dc0746f22cf361267de07073f/uploads/2025/09/202509091202474316.pdf"
    try:
        r = requests.get(url_ssp, headers=HEADERS, timeout=25, verify=False)
        ssp_count = 0
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for t in tables:
                    for row in t:
                        if row and row[0] and str(row[0]).strip().isdigit():
                            name = clean_text(row[1]) if len(row) > 1 else ""
                            state = clean_text(row[2]) if len(row) > 2 else ""
                            website = clean_text(row[3]) if len(row) > 3 else ""
                            address = clean_text(row[4]) if len(row) > 4 else ""
                            contact = clean_text(row[5]) if len(row) > 5 else ""

                            if name:
                                email_m = re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', contact)
                                records.append({
                                    "name": name,
                                    "category": "NIDHI Seed Support Incubator (TBI)",
                                    "type": "DST NIDHI (Dept. of Science & Technology)",
                                    "city": address.split(",")[-1].strip() if "," in address else "",
                                    "state": state,
                                    "location": f"{address}, {state}".strip(", "),
                                    "sector_or_stage": "Technology Innovation & Early-Stage Seed",
                                    "description": f"DST NIDHI Seed Support Program (SSP) implementing incubator. Address: {address}.",
                                    "website": website,
                                    "email": email_m.group(0) if email_m else "",
                                    "funding_allocation": "DST NIDHI-SSP Seed Support Corpus",
                                    "source_authority": "Dept. of Science & Technology (DST - NIDHI)",
                                    "source_url": "https://nidhi.dst.gov.in"
                                })
                                ssp_count += 1
        print(f"  -> Extracted {ssp_count} NIDHI-SSP incubators from DST.")
    except Exception as e:
        print(f"  -> Error parsing NIDHI-SSP PDF: {e}")

    # 3. NIDHI Centres of Excellence (CoE)
    url_coe = "https://cdnbbsr.s3waas.gov.in/s312b1e42dc0746f22cf361267de07073f/uploads/2024/05/2024050326860867.pdf"
    try:
        r = requests.get(url_coe, headers=HEADERS, timeout=20, verify=False)
        coe_count = 0
        with pdfplumber.open(io.BytesIO(r.content)) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for t in tables:
                    for row in t:
                        if row and row[0] and str(row[0]).strip().isdigit():
                            name = clean_text(row[1]) if len(row) > 1 else ""
                            institute = clean_text(row[2]) if len(row) > 2 else ""
                            address = clean_text(row[3]) if len(row) > 3 else ""
                            city = clean_text(row[4]) if len(row) > 4 else ""
                            state = clean_text(row[5]) if len(row) > 5 else ""
                            email = clean_text(row[6]).replace("[at]", "@").replace("[dot]", ".") if len(row) > 6 else ""

                            if name:
                                records.append({
                                    "name": f"{name} ({institute})" if institute else name,
                                    "category": "NIDHI Centre of Excellence (CoE)",
                                    "type": "DST NIDHI Centre of Excellence",
                                    "city": city,
                                    "state": state,
                                    "location": f"{city}, {state}".strip(", "),
                                    "sector_or_stage": "Deeptech, Advanced Materials, Bio/Hardware R&D",
                                    "description": f"National Centre of Excellence under DST NIDHI hosted at {institute}.",
                                    "website": "",
                                    "email": email,
                                    "funding_allocation": "DST NIDHI CoE Flagship Grant (up to ₹50 Cr)",
                                    "source_authority": "Dept. of Science & Technology (DST - NIDHI)",
                                    "source_url": "https://nidhi.dst.gov.in"
                                })
                                coe_count += 1
        print(f"  -> Extracted {coe_count} NIDHI Centres of Excellence from DST.")
    except Exception as e:
        print(f"  -> Error parsing NIDHI-CoE PDF: {e}")

    return records

# ---------------------------------------------------------
# MASTER INCUBATOR PIPELINE & MULTI-AGENCY DEDUPLICATION
# ---------------------------------------------------------
def run_phase2_pipeline():
    print("==================================================")
    print("STARTING PHASE 2: INCUBATOR MASTER EXTRACTOR")
    print("==================================================")

    sisfs_data = scrape_sisfs_incubators()
    aim_data = scrape_aim_incubators()
    msh_data = scrape_meity_incubators()
    birac_data = scrape_birac_bionest()
    dst_data = scrape_dst_nidhi()

    all_records = sisfs_data + aim_data + msh_data + birac_data + dst_data
    df = pd.DataFrame(all_records)
    print(f"\nRaw total incubator records gathered: {len(df)}")

    # Add normalized key for deduplication
    df["norm_key"] = df["name"].apply(normalize_name)

    # Priority score for richest records
    df["has_email"] = df["email"].apply(lambda x: 1 if x and "@" in str(x) else 0)
    df["has_website"] = df["website"].apply(lambda x: 1 if x and "http" in str(x) else 0)
    df["has_funding"] = df["funding_allocation"].apply(lambda x: 1 if x and "₹" in str(x) or "grant" in str(x).lower() else 0)

    # Sort so best records stay on top
    df = df.sort_values(by=["has_funding", "has_email", "has_website"], ascending=[False, False, False])
    df = df.drop_duplicates(subset=["norm_key"], keep="first")
    df = df.drop(columns=["norm_key", "has_email", "has_website", "has_funding"])

    # Sort alphabetically by Name
    df = df.sort_values(by="name").reset_index(drop=True)

    cols = [
        "name", "category", "type", "city", "state", "location",
        "sector_or_stage", "description", "website", "email",
        "funding_allocation", "source_authority", "source_url"
    ]
    df = df[[c for c in cols if c in df.columns]]

    csv_path = "india_incubators_master.csv"
    xlsx_path = "india_incubators_master.xlsx"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    df.to_excel(xlsx_path, index=False, engine="openpyxl")

    print("\n==================================================")
    print(f"SUCCESS: Saved {len(df)} unique incubators to:")
    print(f" - {csv_path}")
    print(f" - {xlsx_path}")
    print("==================================================")

    print("\n--- Summary by Source Authority ---")
    print(df["source_authority"].value_counts())

    print("\n--- Summary by Category ---")
    print(df["category"].value_counts())

    print("\n--- Top States ---")
    print(df["state"].replace("", "Unspecified").value_counts().head(10))

    # Also build the unified master workbook containing both Accelerators and Incubators
    build_combined_master(df)

def build_combined_master(df_inc: pd.DataFrame):
    acc_path = "india_accelerators_master.csv"
    df_acc = pd.read_csv(acc_path)

    combined_xlsx = "india_startup_hubs_complete_master.xlsx"
    with pd.ExcelWriter(combined_xlsx, engine="openpyxl") as writer:
        df_acc.to_excel(writer, sheet_name="Accelerators", index=False)
        df_inc.to_excel(writer, sheet_name="Incubators", index=False)

        # Overview Sheet
        summary_data = {
            "Metric": [
                "Total Verified Accelerators",
                "Total Verified Incubators",
                "Grand Total Ecosystem Hubs",
                "Central Authorities Covered",
                "Top Accelerator State",
                "Top Incubator State"
            ],
            "Value": [
                len(df_acc),
                len(df_inc),
                len(df_acc) + len(df_inc),
                "DPIIT, NITI Aayog (AIM), MeitY (MSH), DST (NIDHI), DBT (BIRAC), Ecosystem Directories",
                f"{df_acc['state'].value_counts().index[0]} ({df_acc['state'].value_counts().iloc[0]})",
                f"{df_inc['state'].replace('', 'Unspecified').value_counts().index[0]} ({df_inc['state'].replace('', 'Unspecified').value_counts().iloc[0]})"
            ]
        }
        df_summary = pd.DataFrame(summary_data)
        df_summary.to_excel(writer, sheet_name="Executive Summary", index=False)

    print(f"\nUnified Master Workbook generated: {combined_xlsx}")

if __name__ == "__main__":
    run_phase2_pipeline()
