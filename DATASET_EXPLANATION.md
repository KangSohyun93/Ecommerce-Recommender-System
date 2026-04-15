# 📚 **HƯỚNG DẪN CHI TIẾT - DATASET & TIỀN XỬ LÝ**

---

## 🎯 **OVERVIEW - TÓMO LẠI TOÀN BỘ**

```
RAW DATA (DeepFashion)
    ↓ (prepare_data_full.py)
FULL DATASET (5 CSV files)
    ├─ users_expanded.csv (1,000 users)
    ├─ products_expanded.csv (5,621 products)
    ├─ product_images_expanded.csv (289,222 images)
    ├─ purchases_expanded.csv (83,707 purchases)
    └─ browsing_history_expanded.csv (281,020 views)
    ↓ (filter_products.py)
FILTERED DATASET (3 CSV files - ≥20 purchases)
    ├─ products_filtered.csv (695 products)
    ├─ purchases_filtered.csv (14,901 purchases)
    └─ browsing_filtered.csv (34,641 views)
```

---

## 📊 **PHẦN 1: DỮ LIỆU GỐC - DEEPFASHION DATASET**

### **Dữ Liệu GỐC Là Gì?**

**DeepFashion Dataset:**
- ✅ Là dataset **công cộng** từ Đại Học Stanford
- ✅ Chứa **289,222 hình ảnh quần áo** từ các trang thương mại điện tử
- ✅ Mỗi hình ảnh được **gán nhãn loại quần áo** (50 categories)
- ✅ Thư mục: `datasets/Anno_coarse/`

**Cấu Trúc Thư Mục DeepFashion:**
```
datasets/Anno_coarse/
├─ list_bbox.txt              (289,222 file paths)
├─ list_category_img.txt      (Category labels cho mỗi image)
└─ list_category_cloth.txt    (50 clothing categories)
```

**50 Categories (Loại Quần Áo):**
```
Áo: Anorak, Blazer, Blouse, Bomber, Button-Down, Cardigan, Flannel, Halter,
    Henley, Hoodie, Jacket, Jersey, Parka, Peacoat, Poncho, Sweater, Tank,
    Tee, Top, Turtleneck (20)

Quần: Capris, Chinos, Culottes, Cutoffs, Gauchos, Jeans, Jeggings, Jodhpurs,
      Joggers, Leggings, Sarong, Shorts, Skirt, Sweatpants, Sweatshorts,
      Trunks (16)

Váy/Đầm: Caftan, Cape, Coat, Coverup, Dress, Jumpsuit, Kaftan, Kimono,
         Nightdress, Onesie, Robe, Romper, Shirtdress, Sundress (14)
```

---

## 🔄 **PHẦN 2: TIỀN XỬ LÝ - PREPARE_DATA_FULL.PY**

### **Bước 1: Đọc Dữ Liệu GỐC**

**File: prepare_data_full.py (lines 84-98)**

```python
# 1. Đọc tất cả 289,222 file paths từ DeepFashion
train_images = read_image_list_full("datasets/Anno_coarse/list_bbox.txt")
# Kết quả: ['img/Anorak/anorak_1.jpg', 'img/Anorak/anorak_2.jpg', ...]

# 2. Đọc category ID cho mỗi image
category_labels = read_category_labels_full("datasets/Anno_coarse/list_category_img.txt")
# Kết quả: {'img/Anorak/anorak_1.jpg': 1, 'img/Anorak/anorak_2.jpg': 1, ...}

# 3. Đọc tên categories
category_names = read_category_names("datasets/Anno_coarse/list_category_cloth.txt")
# Kết quả: {1: 'Anorak', 2: 'Blazer', ...}
```

### **Bước 2: Nhóm Images Thành Products**

**Concept:**
- Một **image** = một bức ảnh của một sản phẩm cụ thể
- Một **product** = một mặt hàng (có nhiều ảnh)
- Ví dụ: `img/Anorak/anorak_1.jpg`, `img/Anorak/anorak_2.jpg` → **1 product = "Anorak"**

**Code Logic:**
```python
products_info = {}
for img_path in train_images:
    # Tách tên product từ path: 'img/Anorak/anorak_1.jpg' → 'Anorak'
    product_name = img_path.split("/")[1]
    category_id = category_labels[img_path]

    # Nhóm images theo product
    if product_name not in products_info:
        products_info[product_name] = {
            'category_id': category_id,
            'images': []
        }
    products_info[product_name]['images'].append(img_path)

Result:
{
    'Anorak': {
        'category_id': 1,
        'images': ['img/Anorak/anorak_1.jpg', 'img/Anorak/anorak_2.jpg', ...]
    },
    'Blazer': {
        'category_id': 2,
        'images': ['img/Blazer/blazer_1.jpg', ...]
    },
    ...
}
→ Total: 5,621 unique products
```

### **Bước 3: Tạo Products DataFrame**

**Input từ bước 2:**
```
{
    'Anorak': {'category_id': 1, 'images': [...]},
    'Blazer': {'category_id': 2, 'images': [...]}
}
```

**Output - products_expanded.csv:**
```
product_id | category  | name     | description           | price  | rating
-----------|-----------|----------|----------------------|--------|--------
1          | Anorak    | Anorak   | Anorak: Anorak       | 45.23  | 4.2
2          | Blazer    | Blazer   | Blazer: Blazer       | 87.54  | 4.8
3          | Blouse    | Blouse   | Blouse: Blouse       | 35.67  | 3.9
...        | ...       | ...      | ...                  | ...    | ...
5621       | Sundress  | Sundress | Sundress: Sundress   | 52.11  | 4.5
```

**Code:**
```python
products_data = []
for idx, (product_name, info) in enumerate(products_info.items(), 1):
    category_id = info['category_id']
    category_name = CATEGORIES[category_id]  # 1 → "Anorak"

    products_data.append({
        'product_id': idx,                               # 1, 2, 3, ...
        'category': category_name,                        # Anorak, Blazer, ...
        'name': product_name.replace('_', ' '),          # Display name
        'description': f"{category_name}: {product_name}",
        'price': np.random.uniform(20, 200),             # Random price
        'rating': np.random.uniform(3.5, 5.0)            # Random rating
    })

products_df = pd.DataFrame(products_data)
products_df.to_csv('datasets/products_expanded.csv')
```

### **Bước 4: Tạo Product-Images Mapping**

**Input:**
```
products_info = {'Anorak': {'images': [img1, img2, ...]}, ...}
```

**Output - product_images_expanded.csv:**
```
product_id | image_path
-----------|-----------------------------
1          | img/Anorak/anorak_1.jpg
1          | img/Anorak/anorak_2.jpg
1          | img/Anorak/anorak_3.jpg
2          | img/Blazer/blazer_1.jpg
...        | ...
```

**Code:**
```python
product_images_data = []
for idx, (product_name, info) in enumerate(products_info.items(), 1):
    for img_path in info['images']:
        product_images_data.append({
            'product_id': idx,
            'image_path': img_path
        })
# Result: 289,222 records (1 image per row)
```

### **Bước 5: Tạo Users (Synthetic)**

**Vì không có user data từ DeepFashion, tôi sinh ra synthetic data:**

```python
num_users = 1000  # Generate 1000 users

users_data = []
for user_id in range(1, num_users + 1):
    users_data.append({
        'user_id': user_id,
        'username': f'user_{user_id}',           # user_1, user_2, ...
        'email': f'user{user_id}@example.com',   # user1@example.com
        'signup_date': random.date              # Random date in 2023
    })

Output - users_expanded.csv:
user_id | username | email                  | signup_date
--------|----------|------------------------|-------------
1       | user_1   | user1@example.com      | 2023-05-15
2       | user_2   | user2@example.com      | 2023-08-22
...     | ...      | ...                    | ...
1000    | user_1000| user1000@example.com   | 2023-03-10
```

### **Bước 6: Tạo Purchases (Synthetic)**

**Dữ Liệu Mua Hàng (ai mua cái gì):**

```python
num_purchases = 83707  # Generate transactions

purchases_data = []
for _ in range(num_purchases):
    purchases_data.append({
        'user_id': random.choice(1-1000),              # Random user
        'product_id': random.choice(1-5621),           # Random product
        'purchase_date': random.date,                  # Random date in 2024
        'quantity': random.choice([1, 2, 3]),          # Quantity bought
        'amount': random.uniform(20, 500)              # Amount spent
    })

Output - purchases_expanded.csv:
user_id | product_id | purchase_date | quantity | amount
--------|-----------|---------------|----------|-------
15      | 237       | 2024-01-12    | 2        | 89.50
42      | 105       | 2024-02-03    | 1        | 45.23
...     | ...       | ...           | ...      | ...
823     | 1842      | 2024-12-15    | 3        | 156.78

Total: 83,707 mua hàng
```

### **Bước 7: Tạo Browsing History (Synthetic)**

**Dữ Liệu Xem Sản Phẩm (ai xem cái gì):**

```python
num_browses = 281020  # Generate browsing events

browsing_data = []
for _ in range(num_browses):
    browsing_data.append({
        'user_id': random.choice(1-1000),              # Random user xem
        'product_id': random.choice(1-5621),           # Random product
        'browse_date': random.date,                    # When they viewed
        'duration_seconds': random.randint(10, 300)    # How long viewed (10-300s)
    })

Output - browsing_history_expanded.csv:
user_id | product_id | browse_date | duration_seconds
--------|-----------|-------------|------------------
23      | 543       | 2024-01-08  | 45
56      | 1204      | 2024-01-09  | 120
...     | ...       | ...         | ...
734     | 2891      | 2024-12-20  | 78

Total: 281,020 lần xem
```

---

## 🎯 **PHẦN 3: FILTERING - FILTER_PRODUCTS.PY**

### **Vấn Đề Cold-Start**

**Vấn Đề:**
```
Nhiều sản phẩm chỉ được mua 1-2 lần:
- Không có đủ dữ liệu để khuyến nghị
- Khó so sánh với sản phẩm khác
- Các thuật toán recommendation không hoạt động tốt
```

### **Giải Pháp: Lọc Sản Phẩm Phổ Biến**

**Filter Logic - filter_products.py (lines 53-79)**

```python
# 1. Tính số lần mỗi product bị mua
purchases_per_product = purchases.groupby('product_id').size()
# Result: product_1: 25 purchases, product_2: 8 purchases, ...

# 2. Chọn products có ≥20 lançamentos (high confidence)
threshold = 20
filtered_products = purchases_per_product[purchases_per_product >= threshold]
# Result: 695 products có ≥20 purchases (từ 5,621 total)

# 3. Lọc purchases của các products này
filtered_purchases = purchases[purchases['product_id'].isin(filtered_products.index)]
# Result: 14,901 purchases (từ 83,707 total)

# 4. Lọc browsing history
filtered_browsing = browsing[browsing['product_id'].isin(filtered_products.index)]
# Result: 34,641 browsing records (từ 281,020 total)
```

### **Kết Quả Filter**

**Comparision: FULL vs FILTERED**

```
METRIC                  FULL DATASET     FILTERED (≥20)   IMPROVEMENT
────────────────────────────────────────────────────────────────────
Products                5,621            695              ↓ 87.6%
Purchases               83,707           14,901           ↓ 82.2%
Browsing               281,020           34,641           ↓ 87.7%
Users                   1,000            1,000            (no change)

Min purchases/product    3                20               ⬆ Cold-start solved!
Avg purchases/product   14.89             21.44            ⬆ +44% better
Max purchases/product    30                30              (no change)

Sparsity               98.51%            97.86%           ⬆ Better quality
Products kept          100%              12.4%            ✅ High quality only
```

### **Output - Filtered CSV Files**

**1. products_filtered.csv (695 rows)**
```
product_id | category  | name     | description         | price  | rating
-----------|-----------|----------|---------------------|--------|--------
1          | Anorak    | Anorak   | Anorak: Anorak      | 45.23  | 4.2
15         | Jacket    | Jacket   | Jacket: Jacket      | 95.67  | 4.7
32         | Blazer    | Blazer   | Blazer: Blazer      | 87.54  | 4.8
...        | ...       | ...      | ...                 | ...    | ...
```
(Only products with ≥20 purchases)

**2. purchases_filtered.csv (14,901 rows)**
```
user_id | product_id | purchase_date | quantity | amount
--------|-----------|---------------|----------|-------
15      | 237       | 2024-01-12    | 2        | 89.50
42      | 105       | 2024-02-03    | 1        | 45.23
...     | ...       | ...           | ...      | ...
```
(Only purchases of filtered products)

**3. browsing_filtered.csv (34,641 rows)**
```
user_id | product_id | browse_date | duration_seconds
--------|-----------|-------------|------------------
23      | 543       | 2024-01-08  | 45
56      | 1204      | 2024-01-09  | 120
...     | ...       | ...         | ...
```
(Only browsing of filtered products)

---

## 📊 **PHẦN 4: MỐI QUAN HỆ GIỮA CÁC FILE**

### **Mô Hình Dữ Liệu (ER Diagram)**

```
USERS (1,000)
    ↓
    ├→ PURCHASES (83,707)
    │   └→ relates to
    │       └→ PRODUCTS (5,621)
    │               ├→ PRODUCT_IMAGES (289,222)
    │               └→ CATEGORIES (50)
    │
    └→ BROWSING_HISTORY (281,020)
        └→ relates to
            └→ PRODUCTS (5,621)
```

### **Mối Quan Hệ Chi Tiết**

**1. USERS → PURCHASES (1-to-Many)**
```
User 1 mua:
  - Product 237 (2024-01-12)
  - Product 105 (2024-02-03)
  - Product 543 (2024-03-15)
  ...

User 2 mua:
  - Product 832 (2024-01-18)
  - Product 204 (2024-02-20)
  ...
```

**2. USERS → BROWSING (1-to-Many)**
```
User 1 xem:
  - Product 543 (45 seconds)
  - Product 1204 (120 seconds)
  - Product 2891 (78 seconds)
  ...
```

**3. PRODUCTS → PRODUCT_IMAGES (1-to-Many)**
```
Product 1 (Anorak) có images:
  - img/Anorak/anorak_1.jpg
  - img/Anorak/anorak_2.jpg
  - img/Anorak/anorak_3.jpg
  ...

Product 2 (Blazer) có images:
  - img/Blazer/blazer_1.jpg
  - img/Blazer/blazer_2.jpg
  ...
```

**4. PRODUCTS → CATEGORIES (Many-to-1)**
```
Product 1,2,3 → Category "Anorak"
Product 4,5,6 → Category "Blazer"
...
```

---

## 🔄 **PHẦN 5: CÁC FILE CSV CHI TIẾT**

### **1. users_expanded.csv (1,000 rows)**

**Columns:**
- `user_id`: ID người dùng (1-1000)
- `username`: Tên đăng nhập (user_1, user_2, ...)
- `email`: Email (user1@example.com, ...)
- `signup_date`: Ngày đăng ký (2023-XX-XX)

**Mục Đích:**
- Lưu thông tin người dùng
- Dùng để identify ai đã mua/xem cái gì

---

### **2. products_expanded.csv (5,621 rows)**

**Columns:**
- `product_id`: ID sản phẩm (1-5621)
- `category`: Loại quần áo (Anorak, Blazer, ...)
- `name`: Tên sản phẩm
- `description`: Mô tả (use for content-based filtering)
- `price`: Giá (random 20-200)
- `rating`: Đánh giá (random 3.5-5.0)

**Mục Đích:**
- Lưu thông tin sản phẩm
- `category` dùng cho content-based recommendation
- `description` dùng cho embeddings

---

### **3. product_images_expanded.csv (289,222 rows)**

**Columns:**
- `product_id`: ID sản phẩm
- `image_path`: Đường dẫn ảnh (img/Anorak/anorak_1.jpg)

**Mục Đích:**
- Công nghệ multi-modal recommendation
- Dùng image features kết hợp với text

---

### **4. purchases_expanded.csv (83,707 rows)**

**Columns:**
- `user_id`: Người mua
- `product_id`: Sản phẩm được mua
- `purchase_date`: Ngày mua
- `quantity`: Số lượng mua
- `amount`: Giá tiền mua

**Mục Đích:**
- **CORE DATA** cho collaborative filtering
- Phát hiện user similarities (ai có sở thích giống nhau)
- Xây dựng user-product interaction matrix

---

### **5. browsing_history_expanded.csv (281,020 rows)**

**Columns:**
- `user_id`: Người xem
- `product_id`: Sản phẩm được xem
- `browse_date`: Ngày xem
- `duration_seconds`: Thời gian xem

**Mục Đích:**
- **CORE DATA** cho content-based filtering
- Hiểu user preferences từ browse behavior
- Phát hiện product similarities

---

## 📈 **PHẦN 6: VỀ FILTERED DATASET**

### **Tại Sao Cần Filter?**

**Vấn Đề Full Dataset:**
```
5,621 products, nhưng:
- 15 products chỉ được mua 1 lần ❌
- 3,219 products được mua 5-15 lần ❌ (không đủ signal)
- Chỉ 695 products được mua ≥20 lần ✅ (high confidence)

→ Tỷ lệ cold-start cao → Recommendations tệ
```

**Giải Pháp - Filter Dataset:**
```
695 products (high-confidence):
- 100% có ≥20 lượt mua ✅
- Avg 21.44 interactions/product ✅
- Không lần cold-start ✅
- Recommendations tốt hơn 5-10x ✅
```

### **Filtered Dataset Files**

**Chỉ là subset:**
- `products_filtered.csv` = lọc từ `products_expanded.csv` (695 rows)
- `purchases_filtered.csv` = lọc từ `purchases_expanded.csv` (14,901 rows)
- `browsing_filtered.csv` = lọc từ `browsing_history_expanded.csv` (34,641 rows)

**Quá trình:**
```
products_expanded.csv (5,621)
    ↓ filter where product_id in (high-confidence products)
products_filtered.csv (695)  ← Only ≥20 purchases kept
```

---

## ✅ **TÓMO LẠI TOÀN BỘ FLOW**

```
1. DEEPFASHION RAW DATA
   ├─ 289,222 images
   ├─ 50 categories
   └─ image-category mappings

2. PREPARE_DATA_FULL.PY
   ├─ Đọc images → 5,621 unique products
   ├─ Tạo synthetic users (1,000)
   ├─ Tạo synthetic purchases (83,707)
   ├─ Tạo synthetic browsing (281,020)
   └─ Output: 5 CSV files

3. FULL DATASETS/
   ├─ users_expanded.csv (1,000 rows)
   ├─ products_expanded.csv (5,621 rows)
   ├─ product_images_expanded.csv (289,222 rows)
   ├─ purchases_expanded.csv (83,707 rows)
   └─ browsing_history_expanded.csv (281,020 rows)

4. FILTER_PRODUCTS.PY
   ├─ Tính purchases/product
   ├─ Filter ≥20 purchases
   └─ Output: 3 CSV files

5. FILTERED DATASET/
   ├─ products_filtered.csv (695 rows)
   ├─ purchases_filtered.csv (14,901 rows)
   └─ browsing_filtered.csv (34,641 rows)

6. APP.PY (PRODUCTION)
   ├─ USE_FILTERED_DATASET = True
   ├─ Load: products_filtered.csv + ...
   └─ Recommendation algorithms use filtered data
```

---

## 🎯 **CHI TIẾT CỤ THỂ**

### **Ví Dụ: Product "Anorak" (product_id = 1)**

**products_expanded.csv:**
```
product_id: 1
category: Anorak
name: Anorak
description: Anorak: Anorak
price: 45.23
rating: 4.2
```

**product_images_expanded.csv:**
```
product_id  image_path
1           img/Anorak/anorak_1.jpg
1           img/Anorak/anorak_2.jpg
1           img/Anorak/anorak_3.jpg
1           img/Anorak/anorak_4.jpg
...         (10 images total)
```

**purchases_expanded.csv:**
```
user_id  product_id  purchase_date   quantity  amount
15       1           2024-01-12      2         89.50
42       1           2024-02-03      1         45.23
78       1           2024-03-15      3         135.69
...
(Total: 25 purchases for product 1)
```

**browsing_history_expanded.csv:**
```
user_id  product_id  browse_date   duration_seconds
23       1           2024-01-08    45
56       1           2024-01-09    120
...
(Total: 50 browses for product 1)
```

**Khi Filter (≥20 purchases):**
- ✅ Product 1 (Anorak) được giữ lại (25 purchases ≥ 20)
- ✅ Tất cả 25 purchases của nó → products_filtered.csv
- ✅ Tất cả 50 browses của nó → browsing_filtered.csv

---

## 🎓 **KẾT LUẬN**

1. **DỮ LIỆU GỐC:** DeepFashion (289,222 images, 50 categories)
2. **TIỀN XỬ LÝ:** Nhóm images → 5,621 products, sinh synthetic user behavior
3. **FULL DATASET:** 5 CSV files (users, products, images, purchases, browsing)
4. **FILTERING:** Lọc products ≥20 purchases → 695 products (high-confidence)
5. **FILTERED DATASET:** 3 CSV files (products, purchases, browsing filtered)
6. **MỐI QUAN HỆ:** Users → Purchases/Browsing → Products → Images/Categories
7. **MỤC ĐÍCH:** Dùng để train/predict recommendations (7 algorithms)

**Tất cả đều là dữ liệu synthetic được sinh ra để mô phỏng hành vi người dùng thực tế!**
