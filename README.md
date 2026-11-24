# India Accelerators & Incubators Master Database

An exhaustive, verified, and deduplicated dataset of startup hubs operating across India, categorized into strictly separated **Accelerators** and **Incubators** directories.

---

## 1. What Are Accelerators vs. Incubators?

While the Indian ecosystem frequently overlaps the two terms, they serve fundamentally distinct startup stages:

* **Accelerators:** Fixed-term, cohort-based programs (typically **3 to 6 months**) designed to rapidly scale early-to-growth-stage startups that already possess an MVP or early revenue traction. They provide intensive mentorship, investor demo days, corporate pilot access, and upfront seed/pre-seed capital or convertible notes (e.g., Peak XV Surge, Accel Atoms, 100X.VC, Antler India, Google for Startups Accelerator, Marwari Catalysts, India Accelerator).
* **Incubators:** Open-ended or long-term support hubs (typically **12 to 24+ months**) focused on zero-to-one execution—turning ideas into prototypes. Hosted mostly by academic institutions (IITs, IIMs, NITs, Central Universities) or government missions, they offer physical lab/office space, R&D equipment, and non-dilutive grants (e.g., Startup India Seed Fund Scheme, AIM AICs, DST NIDHI TBIs, BIRAC BioNEST, MeitY TIDE 2.0).

---

## 2. Directory Structure & Datasets

The repository maintains strict separation between Accelerators and Incubators:

```
├── Accelerators/
│   ├── india_accelerators_master.csv      # 685 verified Accelerators (CSV)
│   ├── india_accelerators_master.xlsx     # 685 verified Accelerators (Excel)
│   └── README.md                          # Accelerators schema & details
│
├── Incubators/
│   ├── india_incubators_master.csv        # 1,068 verified Incubators (CSV)
│   ├── india_incubators_master.xlsx       # 1,068 verified Incubators (Excel)
│   └── README.md                          # Incubators schema & details
│
├── build_accelerators_master.py           # Phase 1: Accelerator extraction pipeline
├── build_incubators_master.py             # Phase 2: Incubator extraction pipeline
├── strictly_separate_hubs.py              # Data hygiene & separation pipeline
├── requirements.txt                       # Python dependencies
└── README.md
```

---

## 3. Official Source Registries Covered

| Registry / Authority | Scope & Schemes | Covered Entities |
| :--- | :--- | :--- |
| **Startup India Seed Fund Scheme (SISFS)** | DPIIT ₹945 Cr Seed Fund Scheme | 178+ approved seed fund disbursers |
| **MeitY Startup Hub (MSH)** | TIDE 2.0, GENESIS & Deep-Tech Accelerators | 68 Accelerators + 578 Tech Incubators |
| **DST – NIDHI** | Inclusive-TBIs, NIDHI-SSP, and Centres of Excellence | 101+ TBIs, i-TBIs & CoEs |
| **Atal Innovation Mission (AIM)** | Atal Incubation Centres (AICs) & ACICs | 93 established AICs |
| **BIRAC – BioNEST** | Bio-incubators & life-sciences hubs | 69 BioNEST centres |
| **Ecosystem Registries** | VC-backed, Corporate & Private Accelerators | 600+ Accelerator cohorts nationwide |

---

## 4. Standard Schema

Both datasets share the following standardized schema:

1. `name`: Official organization or program name
2. `category`: Accelerator, TBI, AIC, BioNEST, Seed Fund Incubator, CoE
3. `type`: VC-backed, Corporate, Central Govt / DPIIT, NITI Aayog, MeitY, DST, BIRAC, Academic
4. `city`: City / District
5. `state`: State / UT
6. `location`: Normalized location address
7. `sector_or_stage`: Focus sectors, technology domains, or cohort stages
8. `description`: Concise program/hub summary
9. `website`: Official portal URL
10. `email`: SPOC / contact email (where published)
11. `funding_allocation`: Scheme grant size or seed corpus (for incubators)
12. `source_authority`: Primary certifying ministry or registry
13. `source_url`: Verification and reference source link

---

## 5. Usage & Updates

To re-run the extraction and update the master files:

```bash
pip install -r requirements.txt
python build_accelerators_master.py
python build_incubators_master.py
python strictly_separate_hubs.py
```
