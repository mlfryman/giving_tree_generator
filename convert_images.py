import os
from PIL import Image

# Path to your folder
input_folder = r"./Catio Cats"
output_folder = r"./cats"

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Loop through all files in the folder
for filename in os.listdir(input_folder):
    file_path = os.path.join(input_folder, filename)
    
    # Skip directories
    if os.path.isdir(file_path):
        continue

    try:
        # Open the image
        with Image.open(file_path) as img:
            # Convert to RGB if needed (for formats like GIF, PNG with transparency)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Construct output file path
            base_name = os.path.splitext(filename)[0]
            output_path = os.path.join(output_folder, f"{base_name}.jpeg")
            
            # Save as PNG
            img.save(output_path, "PNG")
            print(f"Converted {filename} -> {base_name}.jpeg")
    except Exception as e:
        print(f"Skipping {filename}, error: {e}")

print("All images are JPEGs now!")
