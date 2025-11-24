# Giving Tree Generator
Generates giving tree tags with spaces for a photo, name, and age

# 🚀 How to Run

### 1. Clone the repository:
```bash
git clone https://github.com/mlfryman/giving_tree_generator.git
cd giving_tree_generator
```

### 2. Create a virtual environment & install dependencies:
```bash
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 3. Run Scripts
```bash
python3 generate_wishlist.py. # Adds randomly selected items from wishlist csv
python3 convert_images.py  # Converts all cat images to .jpeg
python3 generate_tags.py  # Creates giving tree tags
python3 build_sheets.py. # Builds sheets of giving tree tags, with 3 tags per sheet
```

The final output will be the `giving_tree_sheets.pdf` file.
