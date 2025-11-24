import csv
import math
import os
import zipfile
from io import BytesIO
from typing import Dict, Tuple, Optional, List, TypedDict
from PIL import Image, ImageDraw, ImageFont
import textwrap

# -----------------------------
# CONFIGURATION
# -----------------------------

CSV_PATH = r"./data/giving_tree_data_wishlist.csv"
TEMPLATE_PATH = r"./assets/giving_tree_template.png"
PLACEHOLDER_PATH = r"./assets/placeholder.jpg"
OUTPUT_DIR = r"./output/"
PHOTO_ZIP_DIR = r"./data/cats"
NUM_OUTPUT_ZIPS = 3

PHOTO_BOX = (382, 510, 642, 770)  # 260x260 centered

NAME_POS = (335, 855)
AGE_POS = (335, 975)
WISHLIST_START_POS = (115, 1167)
WISHLIST_LINE_HEIGHT = 52

# Fonts
FONT_NAME = ImageFont.truetype(r"./assets/Arial.ttf", 75)
FONT_AGE = ImageFont.truetype(r"./assets/Arial.ttf", 55)
FONT_WISHLIST = ImageFont.truetype(r"./assets/Arial.ttf", 40)


# -----------------------------
# TYPES
# -----------------------------

class CatRow(TypedDict):
    """Strongly typed representation of a single CSV cat record.

    Keys:
        name (str): Cat's name
        age (str): Age string formatted externally
        photo (str): photo filename
        wishlist (List[str]): comma-split wishlist
    """
    name: str
    age: str
    photo: str
    wishlist: List[str]


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------

def build_photo_index() -> Dict[str, Tuple[str, str]]:
    """Scan all ZIP files in PHOTO_ZIP_DIR and collect a mapping of photo filenames
    to a tuple indicating which ZIP and internal ZIP file path the photo resides in.

    Returns:
        Dict[str, Tuple[str, str]]:
            A mapping where:
                key   = filename only (e.g., "cat1.jpg")
                value = (absolute zip path, internal zip member path)
    """
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
    """Load a photo either from ZIP or disk, fall back to placeholder if missing.

    Args:
        photo_name (str): Photo filename.
        index (Dict[str, Tuple[str, str]]): lookup map.

    Returns:
        Optional[Image.Image]:
            RGB Pillow image if found,
            placeholder otherwise,
            None only if placeholder fails.
    """
    
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


def paste_cat_photo(base_img: Image.Image, photo_name: str, photo_index: Dict[str, Tuple[str, str]]) -> Optional[Image.Image]:
    """Paste resized cat photo on base template.

    Args:
        base_img (Image.Image): image to paste into
        photo_name (str): filename from CSV
        photo_index: lookup map

    Returns:
        Optional[Image.Image]: modified base image
    """
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


def chunk_cats(cats: List[CatRow], num_archives: int) -> List[List[CatRow]]:
    """Divide cats list into N equal chunks.

    Args:
        cats: list of CatRow
        num_archives: desired chunk count

    Returns:
        list of sublists
    """
    if not cats:
        return []
    chunk_size = max(1, math.ceil(len(cats) / num_archives))
    return [cats[i:i + chunk_size] for i in range(0, len(cats), chunk_size)]


def cleanup_jpegs(photo_zip_dir: str) -> None:
    """Remove .jpg/jpeg files after ZIP export.

    Args:
        photo_zip_dir: dir to clean

    Returns:
        None
    """
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


def write_tag_archives(
    cats: List[CatRow],
    photo_index: Dict[str, Tuple[str, str]],
    num_archives: int = NUM_OUTPUT_ZIPS
) -> None:
    """Render all tags to PNG buffers and write to multiple archives.

    Args:
        cats: list of CatRow
        photo_index: lookup dict
        num_archives: how many zips

    Returns:
        None
    """

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

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
                img = render_tag(cat, photo_index)
                if img is None:
                    continue
                with BytesIO() as buf:
                    img.save(buf, format="PNG")
                    zipf.writestr(f"{cat['name']}.png", buf.getvalue())

        print(f"Wrote {len(chunk)} tags to {zip_path}")

    cleanup_jpegs("./output/")


def draw_text_box(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: Tuple[int, int, int, int],
    font: ImageFont.FreeTypeFont,
    min_font_size: int = 24,
    line_spacing: float = 1.1,
    fill: str = "black",
) -> None:
    """Draw text into a rectangle and shrink automatically to fit."""

    left, top, right, bottom = box
    max_width = right - left
    max_height = bottom - top
    text = text.strip()
    current_size = font.size

    while current_size >= min_font_size:
        test_font = ImageFont.truetype(font.path, current_size)
        words = text.split()
        lines = []
        current_line = ""

        for w in words:
            test_line = (current_line + " " + w).strip()
            if test_font.getlength(test_line) <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = w
        if current_line:
            lines.append(current_line)

        line_height = int(test_font.size * line_spacing)
        total_height = line_height * len(lines)

        if total_height <= max_height:
            y = top
            for line in lines:
                draw.text((left, y), line, font=test_font, fill=fill)
                y += line_height
            return

        current_size -= 2

    draw.text((left, top), text, font=font, fill=fill)


def render_tag(cat: CatRow, photo_index: Dict[str, Tuple[str, str]]) -> Image.Image:
    """Build one full tag.

    Args:
        cat: a structured CatRow
        photo_index: lookup

    Returns:
        completed tag image
    """
    base = Image.open(TEMPLATE_PATH).convert("RGB")
    draw = ImageDraw.Draw(base)

    paste_cat_photo(base, cat["photo"], photo_index)

    draw.text(NAME_POS, f"{cat['name']}", fill="black", font=FONT_NAME)
    draw.text(AGE_POS, f"{cat['age']}", fill="black", font=FONT_AGE)

    wishlist_text = ", ".join(cat["wishlist"])

    draw_text_box(
        draw,
        wishlist_text,
        box=(115, 1150, 950, 2000),
        font=FONT_WISHLIST,
        min_font_size=34,
        line_spacing=1.20,
    )

    return base


# -----------------------------
# READ CSV + PROCESS DATA
# -----------------------------

def load_cats_from_csv(csv_path: str) -> List[CatRow]:
    """Load CSV and convert into CatRow objects.

    Args:
        csv_path: CSV source

    Returns:
        list of CatRow
    """
    cats: List[CatRow] = []

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


if __name__ == "__main__":
    cats = load_cats_from_csv(CSV_PATH)
    photo_index = build_photo_index()
    write_tag_archives(cats, photo_index, NUM_OUTPUT_ZIPS)
