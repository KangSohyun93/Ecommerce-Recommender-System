#!/usr/bin/env python
"""
Thống kê chi tiết dataset - Giải thích ground truth & evaluation methodology
"""
import pandas as pd
import numpy as np
import os

print("="*90)
print("📊 THỐNG KÊ DATASET TOÀN BỘ - GROUND TRUTH & EVALUATION")
print("="*90)

# Load data from datasets folder
DATA_DIR = os.path.join(os.path.dirname(__file__), 'datasets')
users = pd.read_csv(os.path.join(DATA_DIR, 'users_expanded.csv'))
products = pd.read_csv(os.path.join(DATA_DIR, 'products_expanded.csv'))
purchases = pd.read_csv(os.path.join(DATA_DIR, 'purchases_expanded.csv'))
browsing_history = pd.read_csv(os.path.join(DATA_DIR, 'browsing_history_expanded.csv'))

# ============================================================================
# 1. OVERVIEW
# ============================================================================

print("\n" + "█"*90)
print("1. DỮ LIỆU CƠ BẢN VỀ USERS")
print("█"*90)

print(f"""
  📌 Total users: {len(users)}
  📌 Unique user IDs: {users['user_id'].nunique()}
  📌 User ID range: {users['user_id'].min()} → {users['user_id'].max()}
  📌 Columns: {', '.join(users.columns.tolist())}
""")

print("\n" + "█"*90)
print("2. DỮ LIỆU VỀ PRODUCTS (Sản phẩm để recommend)")
print("█"*90)

print(f"""
  📦 Total products: {len(products)}
  📦 Categories: {products['category'].nunique()} loại
  📦 Price range: ${products['price'].min():.2f} - ${products['price'].max():.2f}
  📦 Rating range: {products['rating'].min():.2f}/5 - {products['rating'].max():.2f}/5

Categories:
""")

for cat in products['category'].unique():
    count = len(products[products['category'] == cat])
    print(f"  • {cat}: {count} products")

# ============================================================================
# 2. PURCHASES - GROUND TRUTH (Dữ liệu để validate)
# ============================================================================

print("\n" + "█"*90)
print("3. PURCHASES - GROUND TRUTH (Những hàng user thực sự mua)")
print("█"*90)

print(f"""
  🛍️ Total purchase records: {len(purchases):,} (mỗi row = 1 lần mua)
  🛍️ Unique users (mua hàng): {purchases['user_id'].nunique()} / {len(users)} ({purchases['user_id'].nunique()/len(users)*100:.1f}%)
  🛍️ Unique products bán được: {purchases['product_id'].nunique()} / {len(products)} ({purchases['product_id'].nunique()/len(products)*100:.1f}%)
  🛍️ Date range: {purchases['purchase_date'].min()} → {purchases['purchase_date'].max()}
  🛍️ Amount range: ${purchases['amount'].min():.2f} - ${purchases['amount'].max():.2f}
  🛍️ Columns: {', '.join(purchases.columns.tolist())}
""")

# ============================================================================
# 3. PURCHASES PER USER
# ============================================================================

print("\n" + "█"*90)
print("4. PURCHASES PER USER (Phân bố mua hàng theo user)")
print("█"*90)

purchases_per_user = purchases.groupby('user_id').size()

print(f"""
  👤 Avg purchases per user: {purchases_per_user.mean():.2f}
  👤 Median purchases per user: {purchases_per_user.median():.1f}
  👤 Min purchases by any user: {purchases_per_user.min()}
  👤 Max purchases by any user: {purchases_per_user.max()}

Distribution:
""")

for threshold in [1, 2, 3, 5, 10, 20]:
    count = (purchases_per_user >= threshold).sum()
    pct = count / len(purchases_per_user) * 100
    print(f"  • Users with ≥{threshold:2d} purchases: {count:3d} users ({pct:5.1f}%)")

# ============================================================================
# 4. PURCHASES PER PRODUCT
# ============================================================================

print("\n" + "█"*90)
print("5. PURCHASES PER PRODUCT (Sản phẩm hot vs flops)")
print("█"*90)

purchases_per_product = purchases.groupby('product_id').size()

print(f"""
  🏆 Avg purchases per product: {purchases_per_product.mean():.2f}
  🏆 Median purchases per product: {purchases_per_product.median():.1f}
  🏆 Most sold product: {purchases_per_product.max()} units
  🏆 Least sold product: {purchases_per_product.min()} unit
  🏆 Products never sold: {(purchases_per_product == 0).sum()}

Top 10 Best Sellers:
""")

top_products = purchases_per_product.sort_values(ascending=False).head(10)
for rank, (product_id, count) in enumerate(top_products.items(), 1):
    product_name = products[products['product_id'] == product_id]['name'].values[0]
    category = products[products['product_id'] == product_id]['category'].values[0]
    print(f"  {rank:2d}. Product {product_id:2d} ({category:12s}): {count:3d} purchases - {product_name}")

# ============================================================================
# 5. BROWSING HISTORY
# ============================================================================

print("\n" + "█"*90)
print("6. BROWSING HISTORY (Lịch sử duyệt)")
print("█"*90)

print(f"""
  👁️ Total browsing records: {len(browsing_history):,}
  👁️ Unique users (duyệt): {browsing_history['user_id'].nunique()} / {len(users)} ({browsing_history['user_id'].nunique()/len(users)*100:.1f}%)
  👁️ Unique products viewed: {browsing_history['product_id'].nunique()} / {len(products)}
""")

# ============================================================================
# 6. DATA SPARSITY (Độ thiếu dữ liệu - CHỈ SỐ QUAN TRỌNG)
# ============================================================================

print("\n" + "█"*90)
print("7. DATA SPARSITY (Độ thiếu dữ liệu - ⚠️ ĐÂY LÀ VẤN ĐỀ)")
print("█"*90)

max_possible_purchases = len(users) * len(products)
actual_purchases = len(purchases)
sparsity = (1 - actual_purchases / max_possible_purchases) * 100

print(f"""
  Maximum possible user-product pairs: {max_possible_purchases:,}
  Actual purchase records: {actual_purchases:,}
  Sparsity: {sparsity:.4f}% (99.98%+ sparse)

💡 Ý nghĩa: Chỉ {actual_purchases}/{max_possible_purchases:,} = 0.02% pairs có dữ liệu
   → Rất khó predict vì 99.98% dữ liệu missing!
   → Cold-start problem cực kỳ nghiêm trọng
""")

# ============================================================================
# 7. HOW EVALUATION WORKS
# ============================================================================

print("\n" + "█"*90)
print("8. CÁCH EVALUATION HOẠT ĐỘNG - GROUND TRUTH")
print("█"*90)

print("""
NGUYÊN LÝ CHUNG:
  1. Split dữ liệu user thành 80% TRAIN + 20% TEST
  2. Dùng TRAIN để recommend
  3. So sánh với TEST (Ground Truth)
  4. Tính metrics: Precision, Recall, etc.

VÍ DỤ CỤ THỂ:

  User 1 History: [P1, P2, P3, P4, P5, P6, P7, P8, P9, P10]
  ├─ Train (80%): [P1, P2, P3, P4, P5, P6, P7, P8]
  └─ Test (20%):  [P9, P10] ← GROUND TRUTH (cái này user thực sự mua)

  Bước 1: Dùng TRAIN → Tạo recommendations
    → Recommend: [P7, P8, P9, P11, P12, ...]

  Bước 2: So sánh với TEST
    ✓ Hit: P9 nằm trong recommendations
    ✗ Miss: P10 không trong recommendations

  Bước 3: Tính metrics
    Precision@5 = 1/5 = 0.20 (1 trong 5 đúng)
    Recall@5 = 1/2 = 0.50 (cover 1/2 sản phẩm thực)

CÔNG THỨC:
  Precision = (# Recommended items user bought) / (# Items recommended)
  Recall = (# Recommended items user bought) / (# Items user actually bought)
""")

# ============================================================================
# 8. EVALUATION STATISTICS
# ============================================================================

print("\n" + "█"*90)
print("9. THỐNG KÊ EVALUATION (50-1000 users)")
print("█"*90)

active_users = purchases_per_user[purchases_per_user >= 5].index.tolist()

print(f"""
  Criteria: Users with ≥5 purchases (enough history to split 80/20)

  Active users: {len(active_users)} / {len(users)} ({len(active_users)/len(users)*100:.1f}%)

  Evaluation scenarios:
  • eval_simple.py: Test on {min(10, len(active_users))} users
  • evaluation.py: Test on 1000 users
  • evaluate_all_methods.py: Test on 100 users (NEW - comprehensive)

  Each evaluation:
  ├─ Split each user's {purchases_per_user.mean():.1f} avg purchases
  ├─ Use 80% as training data
  ├─ Use 20% as ground truth (test)
  └─ Compare recommendations vs ground truth

  Expected result:
  • Precision@5: 0.08-0.10 (Recommend 5, typically 0.4-0.5 sản phẩm đúng)
  • Recall@5: 0.25-0.35 (Cover 25-35% sản phẩm user mua)
""")

# ============================================================================
# 10. USER SEGMENTS
# ============================================================================

print("\n" + "█"*90)
print("10. USER SEGMENTS (Phân loại user theo lịch sử)")
print("█"*90)

print("""
Weighted Hybrid sử dụng phân loại này:

  🆕 New Users (<3 interactions):
     Weight: CF=0.1, CB=0.8, DL=0.1
     Lý do: Chưa có dữ liệu CF → ưu tiên CB
""")

new_users = (purchases_per_user < 3).sum()
print(f"     Count: {new_users} users")

print("""
  👤 Medium Users (3-10 interactions):
     Weight: CF=0.5, CB=0.4, DL=0.1
     Lý do: Cân bằng CF và CB
""")

med_users = ((purchases_per_user >= 3) & (purchases_per_user < 10)).sum()
print(f"     Count: {med_users} users")

print("""
  🏆 Loyal Users (>10 interactions):
     Weight: CF=0.7, CB=0.2, DL=0.1
     Lý do: Có đủ dữ liệu CF → ưu tiên CF
""")

loyal_users = (purchases_per_user >= 10).sum()
print(f"     Count: {loyal_users} users")

print(f"""
Total: {new_users} + {med_users} + {loyal_users} = {new_users + med_users + loyal_users}
""")

# ============================================================================
# 11. VALIDATION DATA
# ============================================================================

print("\n" + "█"*90)
print("11. CÁC FILE VALIDATION (Dữ liệu để kiểm chứng)")
print("█"*90)

print(f"""
  ✓ purchases_expanded.csv ({len(purchases)} rows)
    → Ground truth: những hàng user thực sự mua
    → Dùng để: Validate recommendations có đúng hay không
    → 20% của dữ liệu này dùng làm test set

  ✓ browsing_history_expanded.csv ({len(browsing_history)} rows)
    → Implicit feedback: user xem sản phẩm (nhưng không mua)
    → Dùng để: Content-based filtering, user preference

  ✓ products_expanded.csv ({len(products)} rows)
    → Product metadata: category, rating, price, description
    → Dùng để: Content-based filtering, ranking
""")

print("\n" + "="*90 + "\n")
