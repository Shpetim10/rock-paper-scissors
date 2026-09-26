from PIL import Image, ImageEnhance, ImageOps, ImageFilter
import os
import random

INPUT_DIR = "rock-paper-scissors-dataset-main/datasets"
OUTPUT_DIR = "augmented_dataset_v2"
CLASSES = ["rock", "paper", "scissors"]


def augment_image(image):
    # 1. Horizontal flip (50% chance)
    if random.random() < 0.5:
        image = ImageOps.mirror(image)

    # 2. Rotation: -25 to +25 degrees
    angle = random.uniform(-25, 25)
    image = image.rotate(
        angle,
        resample=Image.Resampling.BICUBIC
    )

    # 3. Brightness: 70% to 130%
    brightness = random.uniform(0.70, 1.30)
    image = ImageEnhance.Brightness(image).enhance(brightness)

    # 4. Contrast: 75% to 125%
    contrast = random.uniform(0.75, 1.25)
    image = ImageEnhance.Contrast(image).enhance(contrast)

    # 5. Random crop / zoom: 80% to 100%
    width, height = image.size
    crop_ratio = random.uniform(0.80, 1.0)

    crop_width = int(width * crop_ratio)
    crop_height = int(height * crop_ratio)

    left = random.randint(0, width - crop_width)
    top = random.randint(0, height - crop_height)

    image = image.crop(
        (left, top, left + crop_width, top + crop_height)
    )

    # Resize back to original dimensions
    image = image.resize(
        (width, height),
        Image.Resampling.LANCZOS
    )

    # 6. Slight Gaussian blur (30% chance)
    if random.random() < 0.30:
        blur_radius = random.uniform(0.5, 1.5)
        image = image.filter(
            ImageFilter.GaussianBlur(radius=blur_radius)
        )

    return image


# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

total_original = 0
total_augmented = 0

for class_name in CLASSES:

    input_class_dir = os.path.join(INPUT_DIR, class_name)
    output_class_dir = os.path.join(OUTPUT_DIR, class_name)

    os.makedirs(output_class_dir, exist_ok=True)

    if not os.path.exists(input_class_dir):
        print(f"WARNING: Could not find {input_class_dir}")
        continue

    for filename in os.listdir(input_class_dir):

        input_path = os.path.join(input_class_dir, filename)

        if not filename.lower().endswith(
            (".jpg", ".jpeg", ".png", ".bmp", ".webp")
        ):
            continue

        try:
            image = Image.open(input_path).convert("RGB")

            original_name = os.path.splitext(filename)[0]

            # Save original image
            original_path = os.path.join(
                output_class_dir,
                original_name + "_original.jpg"
            )

            image.save(original_path, quality=95)
            total_original += 1

            # Create augmented image
            augmented_image = augment_image(image)

            augmented_path = os.path.join(
                output_class_dir,
                original_name + "_augmented.jpg"
            )

            augmented_image.save(
                augmented_path,
                quality=95
            )

            total_augmented += 1

        except Exception as e:
            print(f"Error processing {input_path}: {e}")


print()
print("===================================")
print("AUGMENTATION V2 COMPLETE")
print("===================================")
print(f"Original images copied: {total_original}")
print(f"Augmented images created: {total_augmented}")
print(f"Total images: {total_original + total_augmented}")
print()
print("Transformations:")
print("- Horizontal flip: 50% probability")
print("- Rotation: -25 to +25 degrees")
print("- Brightness: 0.70 to 1.30")
print("- Contrast: 0.75 to 1.25")
print("- Crop/zoom: 80% to 100%")
print("- Gaussian blur: 30% probability")
print()
print("Dataset saved to:")
print(os.path.abspath(OUTPUT_DIR))
