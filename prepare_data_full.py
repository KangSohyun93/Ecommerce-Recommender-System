"""
Script to prepare FULL data from DeepFashion dataset
Generates complete CSV files needed by the Flask app
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Set random seed for reproducibility
np.random.seed(42)

# Paths
DATASET_PATH = "datasets"
ANNO_COARSE = os.path.join(DATASET_PATH, "Anno_coarse")
OUTPUT_DIR = os.path.join(DATASET_PATH)

# ==================== PARSE DEEPFASHION DATASET ====================

def read_image_list_full(filepath):
    """Read ALL images from DeepFashion"""
    images = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            line = line.strip()
            if i == 0:  # Skip count
                continue
            if i == 1:  # Skip header
                continue
            if line and line.startswith("img/"):
                parts = line.split()
                if parts:
                    images.append(parts[0])
    return images

def read_category_labels_full(filepath):
    """Read category labels for all images"""
    labels = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i == 0:  # Skip count
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

def read_category_names(filepath):
    """Read category names"""
    categories = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i == 0:  # Skip count
                continue
            if i == 1:  # Skip header
                continue
            parts = line.strip().split()
            if len(parts) >= 1:
                category_name = parts[0]
                # Category ID is the line number (1-indexed)
                category_id = i  # Line i is category i (since header is line 1)
                categories[category_id] = category_name
    return categories

print("="*80)
print("📦 GENERATING FULL DATASET FROM DEEPFASHION")
print("="*80)

try:
    # Read training images (ALL of them)
    print("\n🔍 Reading image list from DeepFashion...")
    train_images = read_image_list_full(os.path.join(ANNO_COARSE, "list_bbox.txt"))
    print(f"✓ Found {len(train_images):,} total images in DeepFashion")

    # Read category labels
    print("📋 Reading category labels...")
    category_labels = read_category_labels_full(os.path.join(ANNO_COARSE, "list_category_img.txt"))
    print(f"✓ Loaded {len(category_labels):,} category labels")

    # Read category names
    print("📝 Reading category names...")
    category_names = read_category_names(os.path.join(ANNO_COARSE, "list_category_cloth.txt"))
    print(f"✓ Loaded {len(category_names)} categories")

except Exception as e:
    print(f"❌ Error loading dataset: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# ==================== EXTRACT PRODUCTS ====================

print("\n" + "="*80)
print("🛍️  EXTRACTING PRODUCTS FROM IMAGES")
print("="*80)

# Extract unique products (grouped by product folder)
products_info = {}
missing_labels = 0

for img_path in train_images:
    if img_path in category_labels:
        # Extract product name from path: img/Product_Name/img_xxxxx.jpg
        parts = img_path.split("/")
        if len(parts) >= 2:
            product_name = parts[1]
            category_id = category_labels[img_path]

            if product_name not in products_info:
                products_info[product_name] = {
                    'category_id': category_id,
                    'images': []
                }
            products_info[product_name]['images'].append(img_path)
    else:
        missing_labels += 1

print(f"\n✓ Found {len(products_info):,} unique products")
if missing_labels > 0:
    print(f"⚠️  {missing_labels:,} images missing category labels (skipped)")

# ==================== GENERATE CSV FILES ====================

print("\n" + "="*80)
print("📊 GENERATING CSV FILES")
print("="*80)

# Create products dataframe
print("\n1️⃣  Creating products dataframe...")
products_data = []
product_id_map = {}

for idx, (product_name, info) in enumerate(products_info.items(), 1):
    category_id = info['category_id']
    category_name = category_names.get(category_id, "Unknown")

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
print(f"✓ Created {len(products_df):,} products across {products_df['category'].nunique()} categories")

# Create product_images mapping
print("\n2️⃣  Creating product-image mappings...")
product_images_data = []
for idx, (product_name, info) in enumerate(products_info.items(), 1):
    for img_path in info['images']:
        product_images_data.append({
            'product_id': idx,
            'image_path': img_path
        })

product_images_df = pd.DataFrame(product_images_data)
print(f"✓ Created {len(product_images_df):,} image mappings")

# Create users dataframe (realistic number based on dataset size)
print("\n3️⃣  Creating users dataframe...")
num_users = 1000  # Increased from 500
users_data = []
for user_id in range(1, num_users + 1):
    users_data.append({
        'user_id': user_id,
        'username': f'user_{user_id}',
        'email': f'user{user_id}@example.com',
        'signup_date': f'2023-{np.random.randint(1,13):02d}-{np.random.randint(1,28):02d}'
    })

users_df = pd.DataFrame(users_data)
print(f"✓ Created {len(users_df):,} users")

# Create purchases dataframe (more purchases for richer data)
print("\n4️⃣  Creating purchases dataframe (Ground Truth)...")
num_purchases = int(len(products_df) * len(users_df) * 0.015)  # 1.5% density
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
print(f"✓ Created {len(purchases_df):,} purchase records (Ground Truth)")

# Create browsing history dataframe
print("\n5️⃣  Creating browsing history...")
num_browses = int(len(products_df) * len(users_df) * 0.05)  # 5% density
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
print(f"✓ Created {len(browsing_df):,} browsing records")

# ==================== SAVE TO CSV ====================

print("\n" + "="*80)
print("💾 SAVING CSV FILES TO datasets/")
print("="*80)

os.makedirs(OUTPUT_DIR, exist_ok=True)

files_saved = []

print("\nSaving files...")
users_df.to_csv(os.path.join(OUTPUT_DIR, 'users_expanded.csv'), index=False)
files_saved.append(('users_expanded.csv', len(users_df)))
print(f"✓ {len(users_df):,} users")

products_df.to_csv(os.path.join(OUTPUT_DIR, 'products_expanded.csv'), index=False)
files_saved.append(('products_expanded.csv', len(products_df)))
print(f"✓ {len(products_df):,} products")

product_images_df.to_csv(os.path.join(OUTPUT_DIR, 'product_images_expanded.csv'), index=False)
files_saved.append(('product_images_expanded.csv', len(product_images_df)))
print(f"✓ {len(product_images_df):,} product-image mappings")

purchases_df.to_csv(os.path.join(OUTPUT_DIR, 'purchases_expanded.csv'), index=False)
files_saved.append(('purchases_expanded.csv', len(purchases_df)))
print(f"✓ {len(purchases_df):,} purchase records (Ground Truth)")

browsing_df.to_csv(os.path.join(OUTPUT_DIR, 'browsing_history_expanded.csv'), index=False)
files_saved.append(('browsing_history_expanded.csv', len(browsing_df)))
print(f"✓ {len(browsing_df):,} browsing records")

# ==================== SUMMARY ====================

print("\n" + "="*80)
print("✅ DATA GENERATION COMPLETE!")
print("="*80)

print(f"\n📊 SUMMARY:")
print(f"  📂 Location: {os.path.abspath(OUTPUT_DIR)}")
print(f"\n  👥 Users: {len(users_df):,}")
print(f"  🛍️  Products: {len(products_df):,} across {products_df['category'].nunique()} categories")
print(f"  🖼️  Product-Image Mappings: {len(product_images_df):,}")
print(f"  💳 Purchase Records: {len(purchases_df):,} ⭐ (Ground Truth)")
print(f"  👁️  Browsing Records: {len(browsing_df):,}")
print(f"\n  📈 Total Data Rows: {len(users_df) + len(products_df) + len(product_images_df) + len(purchases_df) + len(browsing_df):,}")

# Calculate sparsity
max_possible = len(users_df) * len(products_df)
sparsity = (1 - len(purchases_df) / max_possible) * 100
print(f"\n  📊 Sparsity: {sparsity:.2f}% (lower = more data)")
print(f"     - Max possible user-product pairs: {max_possible:,}")
print(f"     - Actual purchases: {len(purchases_df):,}")

# User statistics
purchases_per_user = purchases_df.groupby('user_id').size()
print(f"\n  👤 Purchase Statistics:")
print(f"     - Avg purchases/user: {purchases_per_user.mean():.2f}")
print(f"     - Median purchases/user: {purchases_per_user.median():.0f}")
print(f"     - Max purchases/user: {purchases_per_user.max()}")
print(f"     - Users with ≥5 purchases: {(purchases_per_user >= 5).sum()}")

print(f"\n" + "="*80)
print("✨ Ready to use! Files saved in: datasets/")
print("="*80 + "\n")
