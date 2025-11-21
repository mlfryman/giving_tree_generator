import csv
import os
import zipfile
from PIL import Image, ImageDraw, ImageFont
import textwrap

# -----------------------------
# CONFIGURATION
# -----------------------------

CSV_PATH = "giving_tree_data.csv"
TEMPLATE_PATH = "giving_tree_template.png"
OUTPUT_DIR = "giving_tree_output"
ZIP_NAME = "giving_tree_tags.zip"

PHOTO_BOX = (382, 410, 642, 670)  # 260x260 centered

NAME_POS = (260, 880)
AGE_POS = (260, 960)

WISHLIST_START_POS = (150, 1080)
WISHLIST_LINE_HEIGHT = 100

# Fonts — replace with any TTF you prefer
FONT_NAME = ImageFont.truetype("Arial.ttf", 40)
FONT_WISHLIST = ImageFont.truetype("Arial.ttf", 36)

# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def paste_cat_photo(base_img, photo_path):
    if not os.path.exists(photo_path):
        print(f"Warning: Photo not found: {photo_path}. Skipping photo.")
        return base_img  # just return the template without the photo
    try:
        cat_img = Image.open(photo_path).convert("RGB")
        w = PHOTO_BOX[2] - PHOTO_BOX[0]
        h = PHOTO_BOX[3] - PHOTO_BOX[1]
        cat_img = cat_img.resize((w, h), Image.LANCZOS)
        base_img.paste(cat_img, (PHOTO_BOX[0], PHOTO_BOX[1]))
    except Exception as e:
        print(f"Error opening photo {photo_path}: {e}. Skipping photo.")
    return base_img

def add_wrapped_text(draw, start_pos, text, font, line_height):
    lines = textwrap.wrap(text, width=40)
    x, y = start_pos
    for line in lines:
        draw.text((x, y), line, font=font, fill="black")
        y += line_height

def create_zip():
    zip_path = os.path.join(OUTPUT_DIR, ZIP_NAME)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file in os.listdir(OUTPUT_DIR):
            if file.lower().endswith(".png"):
                zipf.write(os.path.join(OUTPUT_DIR, file), file)
    print(f"ZIP created at: {zip_path}")

# -----------------------------
# MAIN GENERATION FUNCTION
# -----------------------------

def generate_card(cat):
    base = Image.open(TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(base)

    # Photo
    photo_path = os.path.join("cats_test", cat["photo"])  # ./cats/filename.png
    base = paste_cat_photo(base, photo_path)

    # Name & Age
    draw.text(NAME_POS, f"{cat['name']}", fill="black", font=FONT_NAME)
    draw.text(AGE_POS, f"{cat['age']}", fill="black", font=FONT_NAME)

    # Wishlist
    wishlist_text = ", ".join(cat["wishlist"])
    add_wrapped_text(draw, WISHLIST_START_POS, wishlist_text, FONT_WISHLIST, WISHLIST_LINE_HEIGHT)

    # Save file
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    out_path = os.path.join(OUTPUT_DIR, f"{cat['name']}.png")
    base.save(out_path)
    print(f"Saved {out_path}")

# -----------------------------
# READ CSV + PROCESS ALL CATS
# -----------------------------

def load_cats_from_csv(csv_path):
    cats = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            wishlist_items = [item.strip() for item in row["wishlist"].split(",")]
            cats.append({
                "name": row["name"],
                "age": row["age"],
                "wishlist": wishlist_items,
                "photo": row["photo"]
            })

        print(f"Generated: {row}")
    return cats

cats = load_cats_from_csv(CSV_PATH)

for cat in cats:
    generate_card(cat)

create_zip()
