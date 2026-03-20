#!/usr/bin/env python
"""
Evaluation script - Improved version with Weighted Hybrid + Diversity
Test trên 20 users để so sánh performance
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

# ==================== METRICS ====================

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

# ==================== TEST ON 20 USERS ====================

print("\n" + "="*80)
print("🔄 Comparing: Hybrid vs Weighted Hybrid vs Diversified")
print("="*80)

# Get active users (with 5+ purchases)
active_users = purchases.groupby('user_id').size()
active_users = active_users[active_users >= 5].index.tolist()[:20]

print(f"\nTesting {len(active_users)} users: {active_users}\n")

results = {
    'hybrid': [],
    'weighted-hybrid': [],
    'weighted-hybrid-diverse': []
}

for user_idx, user_id in enumerate(active_users):
    print(f"[{user_idx+1}/{len(active_users)}] User {user_id}...", end=" ", flush=True)

    # Get user's products
    user_purchases = purchases[purchases['user_id'] == user_id]['product_id'].unique()

    if len(user_purchases) < 2:
        print("⊘")
        continue

    # Split: use first 50% as test (simulate known items)
    test_size = len(user_purchases) // 2
    true_products = user_purchases[:test_size]

    # Train data: all except his purchases
    train_purchases = purchases[purchases['user_id'] != user_id]
    train_browsing = browsing_history[browsing_history['user_id'] != user_id]

    try:
        # 1. Standard Hybrid
        recs = hybrid_recommendation(user_id, train_purchases, train_browsing, products)
        rec_ids = recs['product_id'].values.tolist()
        results['hybrid'].append({
            'precision': precision_at_k(rec_ids, true_products, 5),
            'recall': recall_at_k(rec_ids, true_products, 5),
            'hit_rate': hit_rate(rec_ids, true_products, 5),
            'diversity': diversity_at_k(recs, 5),
        })
    except Exception as e:
        print(f"H Error: {e}", end=" ")

    try:
        # 2. Weighted Hybrid (without diversity)
        alpha, beta, gamma = get_dynamic_weights(user_id, train_purchases, train_browsing)
        recs = weighted_hybrid_recommendation(user_id, train_purchases, train_browsing,
                                             products, alpha=alpha, beta=beta, gamma=gamma)
        rec_ids = recs['product_id'].values.tolist()
        results['weighted-hybrid'].append({
            'precision': precision_at_k(rec_ids, true_products, 5),
            'recall': recall_at_k(rec_ids, true_products, 5),
            'hit_rate': hit_rate(rec_ids, true_products, 5),
            'diversity': diversity_at_k(recs, 5),
        })
    except Exception as e:
        print(f"WH Error: {e}", end=" ")

    try:
        # 3. Weighted Hybrid + Diversify
        alpha, beta, gamma = get_dynamic_weights(user_id, train_purchases, train_browsing)
        recs = weighted_hybrid_recommendation(user_id, train_purchases, train_browsing,
                                             products, alpha=alpha, beta=beta, gamma=gamma)
        recs = diversify_recommendations(recs, k=20)  # Diversify by category
        rec_ids = recs['product_id'].values.tolist()
        results['weighted-hybrid-diverse'].append({
            'precision': precision_at_k(rec_ids, true_products, 5),
            'recall': recall_at_k(rec_ids, true_products, 5),
            'hit_rate': hit_rate(rec_ids, true_products, 5),
            'diversity': diversity_at_k(recs, 5),
        })
    except Exception as e:
        print(f"WHD Error: {e}", end=" ")

    print("✓")

# ==================== RESULTS ====================

print("\n" + "="*80)
print("📊 KẾT QUẢ SO SÁNH")
print("="*80 + "\n")

summary = []
for method in ['hybrid', 'weighted-hybrid', 'weighted-hybrid-diverse']:
    if len(results[method]) == 0:
        print(f"⚠️  {method}: Không có kết quả")
        continue

    data = results[method]
    precisions = [d['precision'] for d in data]
    recalls = [d['recall'] for d in data]
    hit_rates = [d['hit_rate'] for d in data]
    diversities = [d['diversity'] for d in data]

    print(f"🔹 {method.upper().replace('-', ' ')}")
    print(f"   Precision@5: {np.mean(precisions):.4f} (±{np.std(precisions):.4f})")
    print(f"   Recall@5:    {np.mean(recalls):.4f} (±{np.std(recalls):.4f})")
    print(f"   Hit Rate@5:  {np.mean(hit_rates):.4f} (±{np.std(hit_rates):.4f})")
    print(f"   Diversity@5: {np.mean(diversities):.4f} (±{np.std(diversities):.4f})")
    print()

    summary.append({
        'Method': method.replace('-', ' ').title(),
        'Precision@5': f"{np.mean(precisions):.4f}",
        'Recall@5': f"{np.mean(recalls):.4f}",
        'Hit Rate@5': f"{np.mean(hit_rates):.4f}",
        'Diversity@5': f"{np.mean(diversities):.4f}",
    })

print("\n" + "="*80)
print("📋 BẢNG TỔNG KẾT")
print("="*80 + "\n")

summary_df = pd.DataFrame(summary)
print(summary_df.to_string(index=False))

# ==================== IMPROVEMENTS ====================

print("\n" + "="*80)
print("📈 CẢI THIỆN (so với Hybrid chuẩn)")
print("="*80 + "\n")

if len(results['hybrid']) > 0 and len(results['weighted-hybrid-diverse']) > 0:
    hybrid_data = results['hybrid']
    improved_data = results['weighted-hybrid-diverse']

    baseline_precision = np.mean([d['precision'] for d in hybrid_data])
    baseline_recall = np.mean([d['recall'] for d in hybrid_data])
    baseline_diversity = np.mean([d['diversity'] for d in hybrid_data])

    improved_precision = np.mean([d['precision'] for d in improved_data])
    improved_recall = np.mean([d['recall'] for d in improved_data])
    improved_diversity = np.mean([d['diversity'] for d in improved_data])

    print(f"Precision@5:  {baseline_precision:.4f} → {improved_precision:.4f}  "
          f"({(improved_precision/baseline_precision - 1)*100:+.1f}%)")
    print(f"Recall@5:     {baseline_recall:.4f} → {improved_recall:.4f}  "
          f"({(improved_recall/baseline_recall - 1)*100:+.1f}%)")
    print(f"Diversity@5:  {baseline_diversity:.4f} → {improved_diversity:.4f}  "
          f"({(improved_diversity/baseline_diversity - 1)*100:+.1f}%)")

print("\n" + "="*80)
print("✅ Evaluation hoàn tất!")
print("="*80 + "\n")
