import math
import os
import zipfile
from PIL import Image

# Path to your folder containing zip files
input_folder = r"./Catio Cats"
output_folder = r"./cats"

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

def bundle_output_images(num_archives=3):
    """Bundle converted images into a handful of zip files to keep sizes smaller."""
    images = sorted(
        [
            f
            for f in os.listdir(output_folder)
            if f.lower().endswith(".jpeg") and not f.lower().endswith(".zip")
        ]
    )

    if not images:
        print("No images to zip.")
        return

    chunk_size = math.ceil(len(images) / num_archives)
    for idx in range(num_archives):
        chunk = images[idx * chunk_size : (idx + 1) * chunk_size]
       
        if not chunk:
            continue
        zip_name = f"cats_part{idx + 1}.zip"
        zip_path = os.path.join(output_folder, zip_name)
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for img_name in chunk:
                zf.write(os.path.join(output_folder, img_name), arcname=img_name)
        
        print(f"Created {zip_path} with {len(chunk)} images.")

# Loop through all zip archives in the folder
for archive_name in os.listdir(input_folder):
    archive_path = os.path.join(input_folder, archive_name)

    # Skip anything that isn't a zip file
    if os.path.isdir(archive_path) or not archive_name.lower().endswith(".zip"):
        continue

    archive_base = os.path.splitext(archive_name)[0]

    try:
        with zipfile.ZipFile(archive_path) as zf:
            for info in zf.infolist():
                # Skip directories inside the archive
                if info.is_dir():
                    continue

                # Build output path first to skip work when already converted
                inner_name = os.path.splitext(os.path.basename(info.filename))[0]
                output_name = f"{archive_base}_{inner_name}.jpeg"
                output_path = os.path.join(output_folder, output_name)

                if os.path.exists(output_path):
                    print(f"DUPLICATE Skipping {archive_name}:{info.filename},o                                                                                         already exists in ./cats as {output_name}")
                    continue

                try:
                    with zf.open(info) as file:
                        with Image.open(file) as img:
                            # Convert to RGB if needed (for formats like GIF, PNG with transparency)
                            if img.mode in ("RGBA", "P"):
                                img = img.convert("RGB")

                            # Save as JPEG
                            img.save(output_path, "JPEG")
                            print(f"Converted {archive_name}:{info.filename} -> {output_name}")
                except Exception as e:
                    print(f"Skipping {archive_name}:{info.filename}, error: {e}")
    except Exception as e:
        print(f"Skipping archive {archive_name}, error: {e}")

print("All images are JPEGs now!")

# Bundle the finished images into zip files to keep file sizes smaller for GitHub
bundle_output_images()
