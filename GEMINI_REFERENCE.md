# DATASET QUICK REFERENCE FOR GEMINI

Copy and paste this section directly into Gemini to describe your data structure without uploading files.

---

## DATASET SCHEMA & STRUCTURE

### Main Data Tables (CSV Files):

**1. users_expanded.csv** (1,000 users)
```
Columns: user_id (INT), username (STRING), email (STRING), signup_date (DATE)
Sample: 1,user_1,user1@example.com,2023-12-19
Size: 43.67 KB
```

**2. products_expanded.csv** (5,621 products)
```
Columns: product_id (INT), category (STRING), name (STRING), description (STRING), price (FLOAT), rating (FLOAT)
Sample: 1,Blazer,Sheer Pleated-Front Blouse,Blazer: Sheer Pleated-Front Blouse,87.42,4.93
Size: 601.88 KB
Categories: 50 types (Blazer, Tank, Tee, Dress, Sweater, Jacket, etc.)
Price range: $20-$200 | Rating: 0.0-5.0 stars
```

**3. product_images_expanded.csv** (289,222 images)
```
Columns: product_id (INT), image_path (STRING)
Sample: 1,img/Sheer_Pleated-Front_Blouse/img_00000001.jpg
Size: 14,675.87 KB
Avg: ~51 images per product
Format: JPG, 300px long side (aspect ratio preserved)
```

**4. purchases_expanded.csv** (83,707 transactions)
```
Columns: user_id (INT), product_id (INT), purchase_date (DATE), quantity (INT), amount (FLOAT)
Sample: 950,1374,2024-11-06,1,58.44
Size: 3,362.01 KB
Date range: 2024-01-01 to 2024-12-31
Quantity: 1-2 items per transaction
```

**5. browsing_history_expanded.csv** (281,020 view records)
```
Columns: user_id (INT), product_id (INT), browse_date (DATE), duration_seconds (INT)
Sample: 777,1820,2024-10-03,47
Size: 6,692.52 KB
Date range: 2024-01-01 to 2024-12-31
Duration: 10-300 seconds
```

### Annotation Files (DeepFashion Dataset):

**ANNO_coarse/** - Large scale annotations

- **list_category_cloth.txt**: 50 fashion categories list
  - Format: category_name (STRING) | category_type (INT)
  
- **list_category_img.txt**: 289,222 image-category mappings
  - Format: image_path | category_label (INT, references category_name)
  
- **list_attr_cloth.txt**: 1,000 fashion attributes
  - Format: attribute_name (STRING) | attribute_type (INT)
  - Examples: floral, graphic, striped, embroidered, pleated, long_sleeve, maxi_length, etc.
  
- **list_attr_img.txt**: 289,222 image-attribute vectors
  - Format: image_path | vector(1000 values: -1=absent, 1=present)
  - Each image has 1000-dimensional binary attribute vector
  
- **list_bbox.txt**: Bounding boxes for clothes in images
  - Format: image_path | x1 (INT) y1 (INT) x2 (INT) y2 (INT)
  - Coordinates in pixels (0-300 range)
  - x1,y1 = top-left corner | x2,y2 = bottom-right corner
  
- **list_landmarks.txt**: Fashion landmark points (8 max per image)
  - Format: image_path | clothes_type (INT) | variation_type (INT) | [8x (visibility INT, x INT, y INT)]
  - visibility: 0=hidden/occluded, 1=visible
  
- **Eval/list_eval_partition.txt**: Train/Val/Test split
  - Format: image_path | evaluation_status (train/val/test)
  - 289,222 images total

**ANNO_fine/** - Fine-grained subset
- Similar structure to ANNO_coarse but:
  - Only 26 attributes (not 1000)
  - Only ~20,000 images (not 289,222)
  - More detailed attribute annotations
  - Additional files: train_attr.txt, test_attr.txt, val_attr.txt, etc.

### Filtered Data Folder:
**filtered/** contains cleaned versions:
- products_filtered.csv (73.89 KB) - subset/cleaned
- purchases_filtered.csv (582.51 KB) - valid transactions only
- browsing_filtered.csv (792.69 KB) - valid browsing sessions only

---

## DATA RELATIONSHIPS

```
User Journey:
user_id [users] ---(purchases)--> product_id [products] ---(images)--> image_path [ANNO]
         |                              |
         +--(browsing_history)----------+

Annotation Hierarchy:
image_path [list_eval_partition] → train/val/test
image_path [list_category_img] → category_label → [list_category_cloth] → category_name
image_path [list_attr_img] → vector[1000] → [list_attr_cloth] → attribute_names
image_path [list_bbox] → bounding_box_coordinates
image_path [list_landmarks] → [8 landmark points with visibility & coords]
```

---

## KEY STATISTICS

| Metric | Value |
|--------|-------|
| Users | 1,000 |
| Products | 5,621 |
| Product Categories | 50 |
| Total Images | 289,222 |
| Avg Images/Product | ~51 |
| Coarse Attributes | 1,000 |
| Fine Attributes | 26 |
| Purchase Records | 83,707 |
| Browse Records | 281,020 |
| Date Range | 2024 full year + signup 2023 |
| Price Range | $20 - $200 |
| Ratings | 0.0 - 5.0 stars |

---

## DATA CHARACTERISTICS

1. **E-Commerce Data**: Real user interactions (purchases & browsing)
2. **Fashion Images**: JPG format, resized to 300px long side, aspect ratio preserved
3. **Rich Annotations**: Multiple levels (category, attributes, spatial - bbox/landmarks)
4. **Train/Val/Test**: Pre-split evaluation set in Eval/ folder
5. **Attribute Encoding**: Binary vectors (-1: unknown/absent, 1: present)
6. **Missing Data**: -1 commonly used for missing/unknown values
7. **Multi-modal**: Combines user behavior data + fashion image features

---

## COPY-PASTE TEMPLATE FOR GEMINI

I have an e-commerce fashion recommendation dataset with the following structure:

**User & Transaction Data:**
- 1,000 users
- 5,621 fashion products across 50 categories
- 83,707 purchase transactions
- 281,020 browsing history records
- All from year 2024 (user signup from mid-2023)

**Product Data:**
- Each product has: product_id, category, name, description, price, rating
- Average 51 images per product (289,222 total images)

**Image Annotations (DeepFashion):**
- 1,000 coarse-grained attributes + 26 fine-grained attributes
- Binary attribute vectors per image (-1: unknown, 1: present)
- Bounding boxes (x1, y1, x2, y2 pixel coords) for clothes regions
- Landmarks: Up to 8 fashion-specific points with visibility flags
- Category labels for each image
- Train/Val/Test split pre-assigned

**Data Files:** (All in /datasets/)
- users_expanded.csv (user_id, username, email, signup_date)
- products_expanded.csv (product_id, category, name, description, price, rating)
- product_images_expanded.csv (product_id, image_path)
- purchases_expanded.csv (user_id, product_id, purchase_date, quantity, amount)
- browsing_history_expanded.csv (user_id, product_id, browse_date, duration_seconds)
- ANNO_coarse/ & ANNO_fine/ - Deep Learning annotations
- filtered/ - Cleaned/subset versions of main tables

Can you help me [your task] with this data structure?
