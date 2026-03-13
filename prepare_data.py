"""
Script to prepare data from DeepFashion dataset
Converts dataset into CSV files needed by the Flask app
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path

# Set random seed for reproducibility
np.random.seed(42)

# Paths
DATASET_PATH = "datasets"
ANNO_COARSE = os.path.join(DATASET_PATH, "Anno_coarse")
OUTPUT_DIR = "."

# Category mapping
CATEGORIES = {
    1: "Anorak", 2: "Blazer", 3: "Blouse", 4: "Bomber", 5: "Button-Down",
    6: "Cardigan", 7: "Flannel", 8: "Halter", 9: "Henley", 10: "Hoodie",
    11: "Jacket", 12: "Jersey", 13: "Parka", 14: "Peacoat", 15: "Poncho",
    16: "Sweater", 17: "Tank", 18: "Tee", 19: "Top", 20: "Turtleneck",
    21: "Capris", 22: "Chinos", 23: "Culottes", 24: "Cutoffs", 25: "Gauchos",
    26: "Jeans", 27: "Jeggings", 28: "Jodhpurs", 29: "Joggers", 30: "Leggings",
    31: "Sarong", 32: "Shorts", 33: "Skirt", 34: "Sweatpants", 35: "Sweatshorts",
    36: "Trunks", 37: "Caftan", 38: "Cape", 39: "Coat", 40: "Coverup",
    41: "Dress", 42: "Jumpsuit", 43: "Kaftan", 44: "Kimono", 45: "Nightdress",
    46: "Onesie", 47: "Robe", 48: "Romper", 49: "Shirtdress", 50: "Sundress"
}

def read_image_list(filepath):
    """Read image list from text file"""
    images = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if i == 0:  # Skip count
                continue
            if i == 1:  # Skip header
                continue
            if line and line.startswith("img/"):
                # Extract just the filename
                parts = line.split()
                if parts:
                    images.append(parts[0])
    return images

def read_category_labels(filepath):
    """Read category labels"""
    labels = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i == 0:  # Skip count line
                continue
            if i == 1:  # Skip header
                continue
            parts = line.strip().split()
            if len(parts) >= 2:
                filename = parts[0]
                try:
                    category_id = int(parts[1])
                    labels[filename] = category_id
                except:
                    pass
    return labels

print("Loading dataset information...")

try:
    # Read training images
    print("Reading image list...")
    train_images = read_image_list(os.path.join(ANNO_COARSE, "list_bbox.txt"))
    train_images = [img for img in train_images if img.startswith("img/")][:3000]  # Use subset
    print(f"Found {len(train_images)} images")
    
    # Read category labels
    print("Reading category labels...")
    category_labels = read_category_labels(os.path.join(ANNO_COARSE, "list_category_img.txt"))
    print(f"Loaded {len(category_labels)} category labels")
except Exception as e:
    print(f"Error loading dataset: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Extract unique products (grouped by product folder)
products_info = {}
missing_labels = 0
for img_path in train_images:
    if img_path in category_labels:
        product_name = img_path.split("/")[1] if "/" in img_path else "Unknown"
        category_id = category_labels[img_path]
        
        if product_name not in products_info:
            products_info[product_name] = {
                'category_id': category_id,
                'images': []
            }
        products_info[product_name]['images'].append(img_path)
    else:
        missing_labels += 1

if missing_labels > 0:
    print(f"Warning: {missing_labels} images missing category labels, skipped")

print(f"Found {len(products_info)} unique products")

# Create products dataframe
products_data = []
product_id_map = {}

for idx, (product_name, info) in enumerate(products_info.items(), 1):
    category_id = info['category_id']
    category_name = CATEGORIES.get(category_id, "Unknown")
    
    product_id_map[product_name] = idx
    
    products_data.append({
        'product_id': idx,
        'category': category_name,
        'name': product_name.replace('_', ' '),
        'description': f"{category_name}: {product_name.replace('_', ' ')}",
        'price': np.random.uniform(20, 200),
        'rating': np.random.uniform(3.5, 5.0)
    })

products_df = pd.DataFrame(products_data)
print(f"Created {len(products_df)} products")

# Create product_images mapping
product_images_data = []
for idx, (product_name, info) in enumerate(products_info.items(), 1):
    for img_path in info['images']:
        product_images_data.append({
            'product_id': idx,
            'image_path': img_path
        })

product_images_df = pd.DataFrame(product_images_data)
print(f"Created {len(product_images_df)} image mappings")

# Create users dataframe
num_users = 500
users_data = []
for user_id in range(1, num_users + 1):
    users_data.append({
        'user_id': user_id,
        'username': f'user_{user_id}',
        'email': f'user{user_id}@example.com',
        'signup_date': f'2023-{np.random.randint(1,13):02d}-{np.random.randint(1,28):02d}'
    })

users_df = pd.DataFrame(users_data)
print(f"Created {len(users_df)} users")

# Create purchases dataframe
num_purchases = 2000
purchases_data = []
for _ in range(num_purchases):
    purchases_data.append({
        'user_id': np.random.randint(1, num_users + 1),
        'product_id': np.random.randint(1, len(products_df) + 1),
        'purchase_date': f'2024-{np.random.randint(1,13):02d}-{np.random.randint(1,28):02d}',
        'quantity': np.random.randint(1, 3),
        'amount': np.random.uniform(20, 500)
    })

purchases_df = pd.DataFrame(purchases_data)
purchases_df = purchases_df.drop_duplicates(subset=['user_id', 'product_id'], keep='first')
print(f"Created {len(purchases_df)} purchases")

# Create browsing history dataframe
num_browses = 5000
browsing_data = []
for _ in range(num_browses):
    browsing_data.append({
        'user_id': np.random.randint(1, num_users + 1),
        'product_id': np.random.randint(1, len(products_df) + 1),
        'browse_date': f'2024-{np.random.randint(1,13):02d}-{np.random.randint(1,28):02d}',
        'duration_seconds': np.random.randint(10, 300)
    })

browsing_df = pd.DataFrame(browsing_data)
browsing_df = browsing_df.drop_duplicates(subset=['user_id', 'product_id', 'browse_date'], keep='first')
print(f"Created {len(browsing_df)} browsing records")

# Save to CSV
print("\nSaving CSV files...")
users_df.to_csv(os.path.join(OUTPUT_DIR, 'users_expanded.csv'), index=False)
products_df.to_csv(os.path.join(OUTPUT_DIR, 'products_expanded.csv'), index=False)
product_images_df.to_csv(os.path.join(OUTPUT_DIR, 'product_images_expanded.csv'), index=False)
purchases_df.to_csv(os.path.join(OUTPUT_DIR, 'purchases_expanded.csv'), index=False)
browsing_df.to_csv(os.path.join(OUTPUT_DIR, 'browsing_history_expanded.csv'), index=False)

print("✓ users_expanded.csv")
print("✓ products_expanded.csv")
print("✓ product_images_expanded.csv")
print("✓ purchases_expanded.csv")
print("✓ browsing_history_expanded.csv")

print("\n✅ Data preparation complete!")
print(f"\nSummary:")
print(f"  - {len(users_df)} users")
print(f"  - {len(products_df)} products")
print(f"  - {len(product_images_df)} product-image mappings")
print(f"  - {len(purchases_df)} purchase records")
print(f"  - {len(browsing_df)} browsing history records")
