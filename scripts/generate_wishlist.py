import pandas as pd
import random

# ---- CONFIG ----
CAT_CSV = "./data/giving_tree_data.csv"
WISHLIST_CSV = "./data/Catio Wishlist.csv"
OUTPUT_CSV = "./data/giving_tree_data_wishlist.csv"

# ---- LOAD CSVs ----
df = pd.read_csv(CAT_CSV)
wishlist_df = pd.read_csv(WISHLIST_CSV)

# ---- BUILD FORMATTED ITEMS ----
# Format: "Item ($Price)"
wishlist_df["Formatted"] = wishlist_df.apply(
    lambda row: f"{row['Item']} (${row['Price']})", axis=1
)

WISHLIST_ITEMS = wishlist_df["Formatted"].tolist()

# ---- RANDOM PICK FUNCTION ----
def random_wishlist():
    items = random.sample(WISHLIST_ITEMS, random.randint(2, 3))
    return ", ".join(items)

# ---- ASSIGN TO EACH CAT ----
df["wishlist"] = df["wishlist"].apply(
    lambda x: random_wishlist() if pd.isna(x) or str(x).strip() == "" else x
)

# ---- SAVE CSV ----
df.to_csv(OUTPUT_CSV, index=False)

print(f"Updated CSV saved to {OUTPUT_CSV}")
