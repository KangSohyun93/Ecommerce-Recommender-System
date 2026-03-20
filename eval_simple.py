#!/usr/bin/env python
"""
Simple evaluation script - test recommendations trên 10 users đầu tiên
Giảm complexity để chạy nhanh hơn
"""
import sys
import os
import pandas as pd
import numpy as np
import torch
import warnings
warnings.filterwarnings('ignore')

print("📦 Loading data...")
try:
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'datasets')
    users = pd.read_csv(os.path.join(DATA_DIR, 'users_expanded.csv'))
    products = pd.read_csv(os.path.join(DATA_DIR, 'products_expanded.csv'))
    purchases = pd.read_csv(os.path.join(DATA_DIR, 'purchases_expanded.csv'))
    browsing_history = pd.read_csv(os.path.join(DATA_DIR, 'browsing_history_expanded.csv'))
    product_images = pd.read_csv(os.path.join(DATA_DIR, 'product_images_expanded.csv'))
    print(f"✓ Loaded: {len(users)} users, {len(products)} products")
except Exception as e:
    print(f"❌ Error loading data: {e}")
    sys.exit(1)

print("\n📥 Importing models...")
try:
    from model import (collaborative_filtering, content_based_filtering,
                       hybrid_recommendation, weighted_hybrid_recommendation,
                       get_dynamic_weights, diversify_recommendations, MultiModalModel)
    print("✓ Models imported successfully")
except Exception as e:
    print(f"❌ Error importing models: {e}")
    sys.exit(1)

# ==================== SIMPLE METRICS ====================

def precision_at_k(recommended_ids, true_ids, k=5):
    if len(recommended_ids) == 0:
        return 0.0
    rec_k = recommended_ids[:k]
    hits = len(set(rec_k) & set(true_ids))
    return hits / k

def recall_at_k(recommended_ids, true_ids, k=5):
    if len(true_ids) == 0:
        return 0.0
    rec_k = recommended_ids[:k]
    hits = len(set(rec_k) & set(true_ids))
    return hits / len(true_ids)

def hit_rate(recommended_ids, true_ids, k=5):
    if len(true_ids) == 0:
        return 0.0
    rec_k = recommended_ids[:k]
    hits = len(set(rec_k) & set(true_ids))
    return 1.0 if hits > 0 else 0.0

def diversity_at_k(recommendations_df, k=5):
    """Calculate category diversity (number of different categories / k)"""
    if len(recommendations_df) == 0:
        return 0.0
    rec_k = recommendations_df.head(k)
    unique_categories = rec_k['category'].nunique()
    return unique_categories / k

# ==================== TEST ON 10 USERS ====================

print("\n" + "="*70)
print("🔄 Testing on 10 users (quick evaluation)")
print("="*70)

# Get active users (with 5+ purchases)
active_users = purchases.groupby('user_id').size()
active_users = active_users[active_users >= 5].index.tolist()[:10]

print(f"\nTesting {len(active_users)} users: {active_users}\n")

results = {'collaborative': [], 'content-based': [], 'hybrid': [], 'multi-modal': []}

for user_idx, user_id in enumerate(active_users):
    print(f"[{user_idx+1}/10] User {user_id}...", end=" ")

    # Get user's products
    user_purchases = purchases[purchases['user_id'] == user_id]['product_id'].unique()

    if len(user_purchases) < 2:
        print("⊘ (insufficient data)")
        continue

    # Split: use first 50% as test (simulate known items)
    test_size = len(user_purchases) // 2
    true_products = user_purchases[:test_size]

    # Train data: all except his purchases
    train_purchases = purchases[purchases['user_id'] != user_id]
    train_browsing = browsing_history[browsing_history['user_id'] != user_id]

    # Test each algorithm
    try:
        # 1. Collaborative Filtering
        recs = collaborative_filtering(user_id, train_purchases, products)
        rec_ids = recs['product_id'].values.tolist()
        results['collaborative'].append({
            'precision': precision_at_k(rec_ids, true_products, 5),
            'recall': recall_at_k(rec_ids, true_products, 5),
            'hit_rate': hit_rate(rec_ids, true_products, 5),
        })
    except Exception as e:
        print(f"CF Error: {e}")

    try:
        # 2. Content-based
        recs = content_based_filtering(user_id, train_purchases, train_browsing, products)
        rec_ids = recs['product_id'].values.tolist()
        results['content-based'].append({
            'precision': precision_at_k(rec_ids, true_products, 5),
            'recall': recall_at_k(rec_ids, true_products, 5),
            'hit_rate': hit_rate(rec_ids, true_products, 5),
        })
    except Exception as e:
        print(f"CB Error: {e}")

    try:
        # 3. Hybrid
        recs = hybrid_recommendation(user_id, train_purchases, train_browsing, products)
        rec_ids = recs['product_id'].values.tolist()
        results['hybrid'].append({
            'precision': precision_at_k(rec_ids, true_products, 5),
            'recall': recall_at_k(rec_ids, true_products, 5),
            'hit_rate': hit_rate(rec_ids, true_products, 5),
        })
    except Exception as e:
        print(f"Hybrid Error: {e}")

    try:
        # 4. Multi-modal
        num_users = users['user_id'].nunique()
        num_products = products['product_id'].nunique()
        model = MultiModalModel(num_users, num_products)

        product_ids = torch.LongTensor(products['product_id'].values) - 1
        texts = products['description'].tolist()

        with torch.no_grad():
            # Pass None for product_images_df since images don't exist
            outputs = model(
                torch.LongTensor([user_id - 1]),
                product_ids,
                texts,
                edge_index=None,
                product_images_df=None  # Skip image loading
            )

        scores = outputs.mean(dim=1).cpu().numpy()
        recs_df = products.copy()
        recs_df['score'] = scores
        rec_ids = recs_df.nlargest(20, 'score')['product_id'].tolist()

        results['multi-modal'].append({
            'precision': precision_at_k(rec_ids, true_products, 5),
            'recall': recall_at_k(rec_ids, true_products, 5),
            'hit_rate': hit_rate(rec_ids, true_products, 5),
        })
    except Exception as e:
        print(f"MM Error: {e}")

    print("✓")

# ==================== RESULTS ====================

print("\n" + "="*70)
print("📊 KẾT QUẢ ĐÁNH GIÁ")
print("="*70 + "\n")

summary = []
for algo in ['collaborative', 'content-based', 'hybrid', 'multi-modal']:
    if len(results[algo]) == 0:
        print(f"⚠️  {algo}: Không có kết quả")
        continue

    data = results[algo]
    precisions = [d['precision'] for d in data]
    recalls = [d['recall'] for d in data]
    hit_rates = [d['hit_rate'] for d in data]

    print(f"🔹 {algo.upper()}")
    print(f"   Precision@5: {np.mean(precisions):.4f} (±{np.std(precisions):.4f})")
    print(f"   Recall@5:    {np.mean(recalls):.4f} (±{np.std(recalls):.4f})")
    print(f"   Hit Rate@5:  {np.mean(hit_rates):.4f} (±{np.std(hit_rates):.4f})")
    print()

    summary.append({
        'Algorithm': algo.title(),
        'Precision@5': f"{np.mean(precisions):.4f}",
        'Recall@5': f"{np.mean(recalls):.4f}",
        'Hit Rate@5': f"{np.mean(hit_rates):.4f}",
    })

print("\n" + "="*70)
print("📋 BẢNG TỔNG KẾT")
print("="*70 + "\n")

summary_df = pd.DataFrame(summary)
print(summary_df.to_string(index=False))

print("\n" + "="*70)
print("✅ Evaluation hoàn tất!")
print("="*70 + "\n")
