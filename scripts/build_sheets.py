import os
import zipfile
from io import BytesIO
from math import ceil
from PIL import Image

# -----------------------------
# CONFIG
# -----------------------------

ZIPS_FOLDER = "./output"
SHEET_PDF_NAME = "./output/giving_tree_sheets.pdf"

# US Letter 8.5x11 at 300 DPI, landscape
PAGE_WIDTH = 3300   # pixels (11 inches * 300)
PAGE_HEIGHT = 2550  # pixels (8.5 inches * 300)

TAGS_PER_PAGE = 3
MARGIN_X = 150      # left/right margin in px
MARGIN_Y = 150      # top/bottom margin in px

# -----------------------------
# HELPERS
# -----------------------------

def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def load_pngs_from_all_zips(zip_folder):
    """
    Loads PNGs from all ZIPs in a folder.
    Returns a list of (filename, PIL.Image) tuples.
    """
    images = []

    zip_files = [
        f for f in os.listdir(zip_folder)
        if f.lower().endswith(".zip")
    ]

    if not zip_files:
        print("No ZIP files found in", zip_folder)
        return images

    zip_files.sort()

    for zip_name in zip_files:
        zip_path = os.path.join(zip_folder, zip_name)
        print(f"Loading ZIP: {zip_name}")

        with zipfile.ZipFile(zip_path, "r") as z:
            for name in sorted(z.namelist()):
                if name.lower().endswith(".png"):
                    with z.open(name) as f:
                        img_data = f.read()
                        img = Image.open(BytesIO(img_data)).convert("RGB")
                        images.append((f"{zip_name}/{name}", img))

    return images

# -----------------------------
# MAIN
# -----------------------------

def build_sheets():
    tags = load_pngs_from_all_zips(ZIPS_FOLDER)

    if not tags:
        print("No PNG images found inside any ZIP.")
        return

    # Use first tag for size reference
    sample_name, sample_img = tags[0]
    tag_w0, tag_h0 = sample_img.size

    pages = []

    # Scale so 3 fit across
    available_width = PAGE_WIDTH - 2 * MARGIN_X
    slot_width = available_width // TAGS_PER_PAGE
    available_height = PAGE_HEIGHT - 2 * MARGIN_Y

    scale = min(
        slot_width / tag_w0,
        available_height / tag_h0
    )

    tag_w = int(tag_w0 * scale)
    tag_h = int(tag_h0 * scale)

    print(f"Original tag size: {tag_w0}x{tag_h0}")
    print(f"Scaled tag size:   {tag_w}x{tag_h}")
    print(f"Tags per page:     {TAGS_PER_PAGE}")
    print(f"Total tags:        {len(tags)}")

    for group in chunk(tags, TAGS_PER_PAGE):
        page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")

        for i, (name, tag_img) in enumerate(group):
            tag = tag_img.resize((tag_w, tag_h), Image.LANCZOS)

            x_slot_start = MARGIN_X + i * slot_width
            x_center = x_slot_start + slot_width // 2

            x0 = x_center - tag_w // 2
            y0 = (PAGE_HEIGHT - tag_h) // 2

            page.paste(tag, (x0, y0))

        pages.append(page)

    if pages:
        first, rest = pages[0], pages[1:]
        first.save(
            SHEET_PDF_NAME,
            "PDF",
            resolution=300,
            save_all=True,
            append_images=rest
        )
        print(f"Saved PDF: {SHEET_PDF_NAME}")
    else:
        print("No pages created.")


if __name__ == "__main__":
    build_sheets()
