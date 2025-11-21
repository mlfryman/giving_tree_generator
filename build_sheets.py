import os
from math import ceil
from PIL import Image

# -----------------------------
# CONFIG
# -----------------------------

CARDS_FOLDER = "giving_tree_output"
SHEET_PDF_NAME = "giving_tree_sheets.pdf"

# US Letter 8.5x11 at 300 DPI, landscape
PAGE_WIDTH = 3300   # pixels (11 inches * 300)
PAGE_HEIGHT = 2550  # pixels (8.5 inches * 300)

CARDS_PER_PAGE = 3
MARGIN_X = 150      # left/right outer margin in px
MARGIN_Y = 150      # top/bottom margin in px

# -----------------------------
# HELPER
# -----------------------------

def chunk(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

# -----------------------------
# MAIN
# -----------------------------

def build_sheets():
    # Grab all PNG cards
    files = [
        f for f in os.listdir(CARDS_FOLDER)
        if f.lower().endswith(".png")
    ]
    if not files:
        print("No PNG files found in", CARDS_FOLDER)
        return

    # Sort for consistent order
    files.sort()

    # Load one card to get original size
    sample_path = os.path.join(CARDS_FOLDER, files[0])
    with Image.open(sample_path) as im:
        card_w0, card_h0 = im.size

    pages = []

    # Pre-calc scale so 3 cards fit across and 1 row fits vertically
    available_width = PAGE_WIDTH - 2 * MARGIN_X
    slot_width = available_width // CARDS_PER_PAGE
    available_height = PAGE_HEIGHT - 2 * MARGIN_Y

    scale = min(
        slot_width / card_w0,
        available_height / card_h0
    )

    card_w = int(card_w0 * scale)
    card_h = int(card_h0 * scale)

    print(f"Original card size: {card_w0}x{card_h0}")
    print(f"Scaled card size:   {card_w}x{card_h}")
    print(f"Cards per page: {CARDS_PER_PAGE}")

    # Build pages
    for group in chunk(files, CARDS_PER_PAGE):
        page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")

        for i, filename in enumerate(group):
            card_path = os.path.join(CARDS_FOLDER, filename)
            with Image.open(card_path) as card_img:
                card = card_img.convert("RGB").resize((card_w, card_h), Image.LANCZOS)

            # Horizontal slot center
            x_slot_start = MARGIN_X + i * slot_width
            x_center = x_slot_start + slot_width // 2

            x0 = x_center - card_w // 2
            y0 = (PAGE_HEIGHT - card_h) // 2  # vertically centered

            page.paste(card, (x0, y0))

        pages.append(page)

    # Save as multi-page PDF
    if pages:
        first, rest = pages[0], pages[1:]
        first.save(
            SHEET_PDF_NAME,
            "PDF",
            resolution=300,
            save_all=True,
            append_images=rest
        )
        print(f"Saved multi-page PDF: {SHEET_PDF_NAME}")
    else:
        print("No pages created.")

if __name__ == "__main__":
    build_sheets()
