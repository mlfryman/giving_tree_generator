import csv
import math
import os
import zipfile
from io import BytesIO
from typing import Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import textwrap

# -----------------------------
# CONFIGURATION
# -----------------------------

CSV_PATH = "./data/giving_tree_data_wishlist.csv"
TEMPLATE_PATH = "./assets/giving_tree_template.png"
PLACEHOLDER_PATH = "./assets/placeholder.jpg"
OUTPUT_DIR = "./output/"
PHOTO_ZIP_DIR = "./data/cats"
NUM_OUTPUT_ZIPS = 3

PHOTO_BOX = (382, 510, 642, 770)  # 260x260 centered

NAME_POS = (335, 863)
AGE_POS = (335, 985)
WISHLIST_START_POS = (115, 1167)
WISHLIST_LINE_HEIGHT = 70

# Fonts
FONT_NAME = ImageFont.truetype("./assets/Arial.ttf", 75)
FONT_AGE = ImageFont.truetype("./assets/Arial.ttf", 55) 
FONT_WISHLIST = ImageFont.truetype("./assets/Arial.ttf", 40)
 
# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def build_photo_index() -> Dict[str, Tuple[str, str]]:
    """Create a map of photo filename -> (zip_path, inner_path)."""
    index: Dict[str, Tuple[str, str]] = {}

    if not os.path.isdir(PHOTO_ZIP_DIR):
        print(f"Warning: photo zip dir {PHOTO_ZIP_DIR} does not exist.")
        return index

    for entry in os.listdir(PHOTO_ZIP_DIR):
        if not entry.lower().endswith(".zip"):
            continue

        zip_path = os.path.join(PHOTO_ZIP_DIR, entry)
        try:
            with zipfile.ZipFile(zip_path) as zf:
                for info in zf.infolist():
                    if info.is_dir():
                        continue
                    name = os.path.basename(info.filename)
                    if not name.lower().endswith((".jpg", ".jpeg", ".png")):
                        continue
                    if name not in index:
                        index[name] = (zip_path, info.filename)
        except Exception as e:
            print(f"Warning: could not read {zip_path}: {e}")

    return index

def load_photo(photo_name: str, index: Dict[str, Tuple[str, str]]) -> Optional[Image.Image]:
    """Load a photo from zip or disk. If missing, return placeholder."""
    
    # Try ZIP
    if photo_name in index:
        zip_path, inner_path = index[photo_name]
        try:
            with zipfile.ZipFile(zip_path) as zf:
                with zf.open(inner_path) as f:
                    img = Image.open(f).convert("RGB")
                    img.load()
                    return img
        except Exception as e:
            print(f"Error opening {photo_name} from ZIP {zip_path}: {e}")

    # Try disk
    disk_path = os.path.join(PHOTO_ZIP_DIR, photo_name)
    if os.path.exists(disk_path):
        try:
            img = Image.open(disk_path).convert("RGB")
            img.load()
            return img
        except Exception as e:
            print(f"Error opening photo on disk {disk_path}: {e}")

    # Fallback to placeholder
    print(f"Photo not found: {photo_name} — using placeholder.")
    try:
        ph = Image.open(PLACEHOLDER_PATH).convert("RGB")
        ph.load()
        return ph
    except Exception as e:
        print(f"ERROR: Could not load placeholder image {PLACEHOLDER_PATH}: {e}")
        return None

def paste_cat_photo(base_img, photo_name, photo_index):
    cat_img = load_photo(photo_name, photo_index)
    if cat_img is None:
        return None
    try:
        w = PHOTO_BOX[2] - PHOTO_BOX[0]
        h = PHOTO_BOX[3] - PHOTO_BOX[1]
        cat_img = cat_img.resize((w, h), Image.LANCZOS)
        base_img.paste(cat_img, (PHOTO_BOX[0], PHOTO_BOX[1]))
    except Exception as e:
        print(f"Error processing photo {photo_name}: {e}. Skipping photo.")
    return base_img

def add_wrapped_text(draw, start_pos, text, font, line_height):
    lines = textwrap.wrap(text, width=40)
    x, y = start_pos
    for line in lines:
        draw.text((x, y), line, font=font, fill="black")
        y += line_height

def chunk_cats(cats, num_archives):
    if not cats:
        return []
    chunk_size = max(1, math.ceil(len(cats) / num_archives))
    return [cats[i : i + chunk_size] for i in range(0, len(cats), chunk_size)]

def cleanup_jpegs_in_output():
    """Remove JPEGs in the output directory after zipping."""
    if not os.path.isdir(OUTPUT_DIR):
        return
    removed = 0
    for fname in os.listdir(OUTPUT_DIR):
        if fname.lower().endswith((".jpg", ".jpeg")):
            try:
                os.remove(os.path.join(OUTPUT_DIR, fname))
                removed += 1
            except Exception as e:
                print(f"Warning: could not delete {fname}: {e}")
    if removed:
        print(f"Removed {removed} JPEGs from {OUTPUT_DIR}")

def cleanup_jpegs(photo_zip_dir):
    """Remove JPEGs in the cats directory after zipping tags."""
    if not os.path.isdir(photo_zip_dir):
        return
    removed = 0
    for fname in os.listdir(photo_zip_dir):
        if fname.lower().endswith((".jpg", ".jpeg")):
            try:
                os.remove(os.path.join(photo_zip_dir, fname))
                removed += 1
            except Exception as e:
                print(f"Warning: could not delete {fname}: {e}")
    if removed:
        print(f"Removed {removed} JPEGs from {photo_zip_dir}")

def write_tag_archives(cats, photo_index, num_archives=NUM_OUTPUT_ZIPS):
    """Render all tags and write them into multiple zip files without saving loose PNGs."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # No skipping — every cat gets a tag (placeholder if no photo)
    valid_cats = cats

    chunks = chunk_cats(valid_cats, num_archives)
    if not chunks:
        print("No cats found to generate.")
        return

    for idx, chunk in enumerate(chunks, start=1):
        zip_name = f"giving_tree_tags_part{idx}.zip"
        zip_path = os.path.join(OUTPUT_DIR, zip_name)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for cat in chunk:
                img = render_card(cat, photo_index)
                if img is None:
                    continue
                with BytesIO() as buf:
                    img.save(buf, format="PNG")
                    zipf.writestr(f"{cat['name']}.png", buf.getvalue())
        print(f"Wrote {len(chunk)} tags to {zip_path}")

    # Delete jpeg files so only zip files are remaining
    cleanup_jpegs("./output/")


# -----------------------------
# MAIN GENERATION FUNCTION
# -----------------------------

def render_card(cat, photo_index) -> Image.Image:
    """Render a single tag as a Pillow Image."""
    base = Image.open(TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(base)

    # Photo (always present — placeholder used if missing)
    base = paste_cat_photo(base, cat["photo"], photo_index)

    # Name & Age
    draw.text(NAME_POS, f"{cat['name']}", fill="black", font=FONT_NAME)
    draw.text(AGE_POS, f"{cat['age']}", fill="black", font=FONT_AGE)

    # Wishlist
    wishlist_text = ", ".join(cat["wishlist"])
    add_wrapped_text(draw, WISHLIST_START_POS, wishlist_text, FONT_WISHLIST,
                     WISHLIST_LINE_HEIGHT)

    return base


# -----------------------------
# READ CSV + PROCESS DATA
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
                "photo": row["photo"],
                "wishlist": wishlist_items
            })

        print(f"Generated: {row}")
    return cats


cats = load_cats_from_csv(CSV_PATH)
photo_index = build_photo_index()

write_tag_archives(cats, photo_index, NUM_OUTPUT_ZIPS)
