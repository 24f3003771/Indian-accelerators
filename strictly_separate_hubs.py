import pandas as pd
import os
import re

def normalize_name(name: str) -> str:
    if not name:
        return ""
    cleaned = re.sub(r"\b(pvt|ltd|limited|private|llp|foundation|society|inc|technologies|solutions|incubator|incubation|centre|center|technology|business|tbi|aic|acic)\b", "", name.lower())
    return re.sub(r"[^a-z0-9]", "", cleaned).strip()

def separate_master_lists():
    print("Loading datasets...")
    df_acc_raw = pd.read_csv("india_accelerators_master.csv")
    df_inc_raw = pd.read_csv("india_incubators_master.csv")

    print(f"Initial Accelerators count: {len(df_acc_raw)}")
    print(f"Initial Incubators count: {len(df_inc_raw)}")

    # Define regex for pure incubator keywords
    # If it contains incubator/incubation/tbi/aic/acic/bionest AND does NOT contain accelerator/acceleration/accelerate
    inc_keywords = r"(incubator|incubation|tbi|aic\b|acic\b|bionest|biotechnology incubator)"
    acc_keywords = r"(accelerator|acceleration|accelerate)"

    is_inc_name = df_acc_raw["name"].str.contains(inc_keywords, case=False, regex=True)
    has_acc_word = df_acc_raw["name"].str.contains(acc_keywords, case=False, regex=True)

    # Pure incubators found in the accelerator file
    pure_inc_in_acc = df_acc_raw[is_inc_name & ~has_acc_word].copy()
    print(f"\nIdentified {len(pure_inc_in_acc)} pure incubators mistakenly residing in accelerator list:")
    for n in pure_inc_in_acc["name"].head(10):
        print(f"  - {n}")

    # Pure accelerators to retain
    df_acc_clean = df_acc_raw[~(is_inc_name & ~has_acc_word)].copy()

    # Re-categorize the transferred pure incubators
    pure_inc_in_acc["category"] = "Technology Business Incubator / Academic Incubation Centre"
    if "funding_allocation" not in pure_inc_in_acc.columns:
        pure_inc_in_acc["funding_allocation"] = "Central / State Incubation Grants"

    # Merge transferred incubators into df_inc
    df_inc_combined = pd.concat([df_inc_raw, pure_inc_in_acc], ignore_index=True)

    # Deduplicate Incubators
    df_inc_combined["norm_key"] = df_inc_combined["name"].apply(normalize_name)
    df_inc_combined["has_funding"] = df_inc_combined["funding_allocation"].apply(lambda x: 1 if pd.notna(x) and ("₹" in str(x) or "grant" in str(x).lower()) else 0)
    df_inc_combined["has_email"] = df_inc_combined["email"].apply(lambda x: 1 if pd.notna(x) and "@" in str(x) else 0)
    df_inc_combined["has_website"] = df_inc_combined["website"].apply(lambda x: 1 if pd.notna(x) and "http" in str(x) else 0)

    df_inc_clean = (
        df_inc_combined.sort_values(by=["has_funding", "has_email", "has_website"], ascending=[False, False, False])
                       .drop_duplicates(subset=["norm_key"], keep="first")
                       .drop(columns=["norm_key", "has_funding", "has_email", "has_website"])
                       .sort_values(by="name")
                       .reset_index(drop=True)
    )

    df_acc_clean = df_acc_clean.sort_values(by="name").reset_index(drop=True)

    print("\n--- FINAL COUNTS AFTER STRICT SEPARATION ---")
    print(f"Pure Accelerators: {len(df_acc_clean)}")
    print(f"Pure Incubators:   {len(df_inc_clean)}")

    # Ensure output directories exist
    os.makedirs("Accelerators", exist_ok=True)
    os.makedirs("Incubators", exist_ok=True)

    # Write separate files in dedicated folders
    acc_csv_folder = os.path.join("Accelerators", "india_accelerators_master.csv")
    acc_xlsx_folder = os.path.join("Accelerators", "india_accelerators_master.xlsx")
    inc_csv_folder = os.path.join("Incubators", "india_incubators_master.csv")
    inc_xlsx_folder = os.path.join("Incubators", "india_incubators_master.xlsx")

    df_acc_clean.to_csv(acc_csv_folder, index=False, encoding="utf-8-sig")
    df_acc_clean.to_excel(acc_xlsx_folder, index=False, engine="openpyxl")

    df_inc_clean.to_csv(inc_csv_folder, index=False, encoding="utf-8-sig")
    df_inc_clean.to_excel(inc_xlsx_folder, index=False, engine="openpyxl")

    # Also update the root level files so user's active editor reflects the cleaned lists
    df_acc_clean.to_csv("india_accelerators_master.csv", index=False, encoding="utf-8-sig")
    df_acc_clean.to_excel("india_accelerators_master.xlsx", index=False, engine="openpyxl")

    df_inc_clean.to_csv("india_incubators_master.csv", index=False, encoding="utf-8-sig")
    df_inc_clean.to_excel("india_incubators_master.xlsx", index=False, engine="openpyxl")

    # Remove the combined master file to enforce total separation as requested
    if os.path.exists("india_startup_hubs_complete_master.xlsx"):
        os.remove("india_startup_hubs_complete_master.xlsx")
        print("\nRemoved combined workbook 'india_startup_hubs_complete_master.xlsx' to maintain strict separation.")

    print("\nFiles successfully created and updated:")
    print(f"  [Accelerators Folder] -> {acc_xlsx_folder} & {acc_csv_folder}")
    print(f"  [Incubators Folder]   -> {inc_xlsx_folder} & {inc_csv_folder}")
    print(f"  [Root Directory]      -> india_accelerators_master.xlsx & india_incubators_master.xlsx")

if __name__ == "__main__":
    separate_master_lists()
