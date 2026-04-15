# CẤU TRÚC CHI TIẾT DATASETS - E-Commerce Recommender

## 📊 TỔNG QUAN

Workspace chứa dữ liệu từ **DeepFashion Dataset** kết hợp với dữ liệu e-commerce tương tác người dùng (browsing & purchases).

---

## 🗂️ DANH SÁCH CÁC FILE CHÍNH

### I. CÁC FILE CSV CHÍNH (Thư mục gốc /datasets/)

#### 1. **users_expanded.csv** 
- **Kích thước**: 43.67 KB | **Dòng**: 1,001 (gồm header)
- **Số lượng user**: 1,000
- **Cột**:
  ```
  user_id (INT)           : ID người dùng duy nhất (1-1000)
  username (STRING)       : Tên user (user_1, user_2, ...)
  email (STRING)          : Email (user1@example.com, ...)
  signup_date (DATE)      : Ngày đăng ký (YYYY-MM-DD)
  ```
- **Ví dụ dòng**:
  ```
  1,user_1,user1@example.com,2023-12-19
  2,user_2,user2@example.com,2023-12-27
  ```

#### 2. **products_expanded.csv**
- **Kích thước**: 601.88 KB | **Dòng**: 5,622 (gồm header)
- **Số lượng sản phẩm**: 5,621
- **Cột**:
  ```
  product_id (INT)        : ID sản phẩm duy nhất (1-5621)
  category (STRING)       : Loại quần áo (Blazer, Tank, Tee, Dress, ...)
  name (STRING)           : Tên sản phẩm (ví dụ: "Sheer Pleated-Front Blouse")
  description (STRING)    : Mô tả (định dạng: "Category: Name")
  price (FLOAT)           : Giá (từ ~$20 đến ~$200)
  rating (FLOAT)          : Đánh giá sao (0.0-5.0)
  ```
- **Ví dụ dòng**:
  ```
  1,Blazer,Sheer Pleated-Front Blouse,Blazer: Sheer Pleated-Front Blouse,87.41722139252525,4.9260714596148745
  2,Blazer,Sheer Woven Blouse,Blazer: Sheer Woven Blouse,151.75890952605292,4.397987726295555
  ```

#### 3. **product_images_expanded.csv**
- **Kích thước**: 14,675.87 KB | **Dòng**: 289,223 (gồm header)
- **Tổng ảnh**: 289,222
- **Trung bình ảnh/sản phẩm**: ~51-52 ảnh
- **Cột**:
  ```
  product_id (INT)        : ID sản phẩm
  image_path (STRING)     : Đường dẫn ảnh tương đối
                           Định dạng: "img/SanPham_Name/img_XXXXXXXX.jpg"
                           hoặc "img1/..." (backup folder)
  ```
- **Ví dụ**:
  ```
  1,img/Sheer_Pleated-Front_Blouse/img_00000001.jpg
  1,img/Sheer_Pleated-Front_Blouse/img_00000002.jpg
  1,img/Sheer_Pleated-Front_Blouse/img_00000003.jpg
  ```

#### 4. **purchases_expanded.csv**
- **Kích thước**: 3,362.01 KB | **Dòng**: 83,708 (gồm header)
- **Tổng giao dịch mua**: 83,707
- **Cột**:
  ```
  user_id (INT)           : ID người dùng
  product_id (INT)        : ID sản phẩm
  purchase_date (DATE)    : Ngày mua (YYYY-MM-DD)
  quantity (INT)          : Số lượng mua (1-2)
  amount (FLOAT)          : Tổng tiền (giá × số lượng)
  ```
- **Ví dụ**:
  ```
  950,1374,2024-11-06,1,58.44423722251779
  426,1304,2024-03-05,1,162.5575477469199
  ```

#### 5. **browsing_history_expanded.csv**
- **Kích thước**: 6,692.52 KB | **Dòng**: 281,021 (gồm header)
- **Tổng lịch xem**: 281,020
- **Cột**:
  ```
  user_id (INT)           : ID người dùng
  product_id (INT)        : ID sản phẩm xem
  browse_date (DATE)      : Ngày xem (YYYY-MM-DD)
  duration_seconds (INT)  : Thời gian xem (giây, 10-300s)
  ```
- **Ví dụ**:
  ```
  777,1820,2024-10-03,47
  957,2003,2024-03-07,98
  ```

---

### II. DỮ LIỆU ANNOTATION - DEEPFASHION (Chi tiết hình ảnh & thuộc tính)

#### **A. ANNO_COARSE/** (Chú thích cấp cao)

##### 1. `list_category_cloth.txt`
- **Dòng**: 52 (1 header + 1 dòng tổng số + 50 categories)
- **Nội dung**: Danh sách các loại quần áo
- **Định dạng**:
  ```
  50                          [Tổng số loại]
  category_name  category_type
  Anorak         1
  Blazer         1
  Blouse         1
  ...            
  [50 loại khác nhau]
  ```
- **Giải thích**: 
  - Column 1: Tên loại quần áo (text)
  - Column 2: Loại (INT, dùng để mapping)

##### 2. `list_category_img.txt`
- **Dòng**: 289,224 (1 header + 1 dòng tổng số + 289,222 ảnh)
- **Định dạng**:
  ```
  289222                      [Tổng số ảnh]
  image_name  category_label
  img/Sheer_Pleated-Front_Blouse/img_00000001.jpg  3
  img/Sheer_Pleated-Front_Blouse/img_00000002.jpg  4
  ...
  ```
- **Giải thích**: 
  - Column 1: Tên file ảnh đầy đủ
  - Column 2: ID loại quần áo (mapping với list_category_cloth.txt)

##### 3. `list_attr_cloth.txt`
- **Dòng**: 1,002 (1 header + 1 dòng tổng số + 1,000 attributes)
- **Nội dung**: Danh sách thuộc tính (1000 attributes)
- **Định dạng**:
  ```
  1000                           [Tổng số thuộc tính]
  attribute_name   attribute_type
  a-line                    3
  abstract                  1
  animal-print              1
  applique                  1
  ...
  ```
- **Giải thích**: 
  - Column 1: Tên thuộc tính
  - Column 2: Loại thuộc tính (INT, dùng để phân nhóm)

##### 4. `list_attr_img.txt`
- **Dòng**: 289,224 (1 header + 1 dòng tổng số + 289,222 ảnh)
- **Nội dung**: Vector thuộc tính cho mỗi ảnh
- **Định dạng**:
  ```
  289222                          [Tổng số ảnh]
  image_name  attribute_labels
  img/Sheer_Pleated-Front_Blouse/img_00000001.jpg  -1 -1 -1 ... 1 -1 -1 ... -1 1 -1 ...
  img/Sheer_Pleated-Front_Blouse/img_00000002.jpg  -1 -1 -1 ... 1 -1 -1 ... -1 1 -1 ...
  ```
- **Giải thích**:
  - Column 1: Tên file ảnh
  - Column 2: Vector 1000 giá trị khác nhau:
    - `-1` = không có thuộc tính
    - `1`  = có thuộc tính
    - Thứ tự tương ứng với list_attr_cloth.txt

##### 5. `list_bbox.txt`
- **Dòng**: 289,224 (1 header + 1 dòng tổng số + 289,222 ảnh)
- **Nội dung**: Bounding box (vị trí quần áo trong ảnh)
- **Định dạng**:
  ```
  289222
  image_name  x_1  y_1  x_2  y_2
  img/Sheer_Pleated-Front_Blouse/img_00000001.jpg  072 079 232 273
  img/Sheer_Pleated-Front_Blouse/img_00000002.jpg  048 062 214 298
  ```
- **Giải thích**:
  - x_1, y_1: Tọa độ góc trên-trái của hộp
  - x_2, y_2: Tọa độ góc dưới-phải của hộp
  - Đơn vị: pixel
  - Giá trị: 0-300 (ảnh được resize, cạnh dài = 300px)

##### 6. `list_landmarks.txt`
- **Dòng**: 289,224
- **Nội dung**: Các điểm đặc trưng trên quần áo (ví dụ: cổ, tay áo...)
- **Định dạng**:
  ```
  289222
  image_name  clothes_type  variation_type  landmark_visibility_1 landmark_location_x_1 landmark_location_y_1  landmark_visibility_2 landmark_location_x_2 landmark_location_y_2  ... [Tối đa 8 landmarks]
  img/.jpg  1  0  1 146 102  0 173 095  0 094 242  0 205 255  0 136 229  0 177 232
  ```
- **Giải thích**:
  - clothes_type: Loại quần áo (INT)
  - variation_type: Biến thể (INT)
  - Mỗi landmark gồm 3 cột:
    - visibility: 0 (ẩn) hoặc 1 (hiện)
    - x: Tọa độ X
    - y: Tọa độ Y

##### 7. `Eval/list_eval_partition.txt`
- **Dòng**: 289,224 (1 header + 1 dòng tổng số + 289,222 ảnh)
- **Nội dung**: Phân chia train/val/test
- **Định dạng**:
  ```
  289222
  image_name  evaluation_status
  img/Sheer_Pleated-Front_Blouse/img_00000001.jpg  train
  img/Sheer_Pleated-Front_Blouse/img_00000002.jpg  train
  img/Sheer_Pleated-Front_Blouse/img_00000003.jpg  val
  img/Sheer_Pleated-Front_Blouse/img_00000005.jpg  test
  ```
- **Giải thích**:
  - evaluation_status: "train" / "val" / "test"

---

#### **B. ANNO_FINE/** (Chú thích cấp chi tiết - Subset)

Tương tự như ANNO_COARSE nhưng với dữ liệu chi tiết hơn:

- **list_attr_cloth.txt**: 26 thuộc tính thay vì 1000
- **list_attr_img.txt**: Chỉ ~20,000 ảnh (subset) thay vì 289,222
- **list_category_cloth.txt**: 50 loại (GIỐNG với coarse)
- Và các file tương ứng khác (bbox, landmarks, train_test_val files)

---

#### **C. IMG/** & **IMG1/** (Thư mục ảnh)
- **Số lượng**: ~289,222 ảnh (format JPG)
- **Kích thước**: Cạnh dài được chuẩn hóa = 300 pixels
- **Tỷ lệ**: Giữ nguyên tỷ lệ gốc
- **Cấu trúc folder**: `img/Tên_Sản_Phẩm/img_XXXXXXXX.jpg`

---

### III. DỮ LIỆU FILTERED (Dữ liệu đã lọc/làm sạch)

#### **Location**: `/datasets/filtered/`

##### 1. **products_filtered.csv**
- **Kích thước**: 73.89 KB
- **Nội dung**: Phiên bản lọc của products_expanded.csv
- **Cấu trúc**: GIỐNG products_expanded.csv
- **Ghi chú**: Có thể đã loại bỏ các sản phẩm với rating quá thấp hoặc thiếu dữ liệu

##### 2. **purchases_filtered.csv**
- **Kích thước**: 582.51 KB
- **Nội dung**: Phiên bản lọc của purchases_expanded.csv
- **Cấu trúc**: GIỐNG purchases_expanded.csv
- **Ghi chú**: Có thể chỉ chứa những giao dịch hợp lệ/đầy đủ

##### 3. **browsing_filtered.csv**
- **Kích thước**: 792.69 KB
- **Nội dung**: Phiên bản lọc của browsing_history_expanded.csv
- **Cấu trúc**: GIỐNG browsing_history_expanded.csv
- **Ghi chú**: Có thể loại bỏ các phiên duyệt quá ngắn

---

## 📈 THỐNG KÊ DỮ LIỆU

### Quy mô dữ liệu:
```
Users:                  1,000
Products:               5,621
Product Images:         289,222 (ave ~51 images per product)
Purchase Interactions:  83,707 transactions
Browsing Interactions:  281,020 records
Fashion Attributes:     1,000 (coarse) / 26 (fine-grained)
Categories:             50
Landmarks per image:    Up to 8 points
```

### Thời gian dữ liệu:
```
User Signup: Từ tháng 5/2023 - tháng 12/2023
Interactions: Từ tháng 1/2024 - tháng 12/2024
```

---

## 🔗 QUAN HỆ GIỮA CÁC FILE

```
users_expanded.csv
    ↓
    └─→ purchases_expanded.csv (user_id → product_id)
    └─→ browsing_history_expanded.csv (user_id → product_id)

products_expanded.csv
    ↓
    ├─→ product_images_expanded.csv (product_id → image_path)
    │
    └─→ ANNO_coarse/list_category_img.txt (image_path → category_label)
        ├─→ ANNO_coarse/list_category_cloth.txt (category_label → category_name)
        ├─→ ANNO_coarse/list_attr_img.txt (image_path → 1000 attributes)
        ├─→ ANNO_coarse/list_bbox.txt (image_path → x1,y1,x2,y2)
        ├─→ ANNO_coarse/list_landmarks.txt (image_path → landmark coords)
        └─→ Eval/list_eval_partition.txt (image_path → train/val/test)
```

---

## 💾 LƯU Ý QUAN TRỌNG

1. **Kết nối dữ liệu**: 
   - Sử dụng `user_id` để join users ↔ purchases ↔ browsing
   - Sử dụng `product_id` để join products ↔ images
   - Sử dụng `image_path` để join images → annotation files

2. **Giá trị mặc định**:
   - Attribute = -1: Không có thông tin
   - Landmark visibility = 0: Điểm không hiện (bị che khuất hoặc ngoài frame)

3. **Dữ liệu bị thiếu**:
   - Không phải tất cả ảnh đều có đầy đủ landmarks
   - Một số sản phẩm có ít ảnh, một số có rất nhiều

4. **Filtered vs Expanded**:
   - Expanded: Dữ liệu đầy đủ/gốc
   - Filtered: Dữ liệu đã được làm sạch (xóa outliers, đầy đủ cols)

---

## 📝 SCHEMA TẮT GỌN CHO GEMINI

```
### CORE TABLES:
1. users(user_id, username, email, signup_date)
2. products(product_id, category, name, description, price, rating)
3. product_images(product_id, image_path)
4. purchases(user_id, product_id, purchase_date, quantity, amount)
5. browsing_history(user_id, product_id, browse_date, duration_seconds)

### ANNOTATION TABLES (from DeepFashion):
6. categories(category_id, category_name) - 50 types
7. attributes(attr_id, attr_name, attr_type) - 1000 attributes
8. image_annotations(image_path, category_label, bbox_coords, landmarks[8], attributes[1000], eval_set)

### RELATIONSHIPS (Keys):
- purchases.user_id → users.user_id
- purchases.product_id → products.product_id
- browsing_history.user_id → users.user_id
- browsing_history.product_id → products.product_id
- product_images.product_id → products.product_id
- image_annotations.image_path → product_images.image_path
```

---

## 🎯 CÁC TRƯỜNG HỢP SỬ DỤNG CHÍNH

1. **Recommendation System**: Dùng purchases + browsing
2. **Image-based Retrieval**: Dùng product_images + annotations
3. **Fashion Attribute Detection**: Dùng annotations + images
4. **User Behavior Analysis**: Dùng browsing + purchases patterns
5. **Cold-start Problem**: Dùng product attributes + images
