import pandas as pd
import numpy as np
import torch
import os
from model import (collaborative_filtering, content_based_filtering, hybrid_recommendation,
                   weighted_hybrid_recommendation, get_dynamic_weights, diversify_recommendations,
                   MultiModalModel)
import logging
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Load data from datasets folder
DATA_DIR = os.path.join(os.path.dirname(__file__), 'datasets')
users = pd.read_csv(os.path.join(DATA_DIR, 'users_expanded.csv'))
products = pd.read_csv(os.path.join(DATA_DIR, 'products_expanded.csv'))
product_images = pd.read_csv(os.path.join(DATA_DIR, 'product_images_expanded.csv'))
purchases = pd.read_csv(os.path.join(DATA_DIR, 'purchases_expanded.csv'))
browsing_history = pd.read_csv(os.path.join(DATA_DIR, 'browsing_history_expanded.csv'))

# ==================== METRICS ====================

def precision_at_k(recommended_product_ids, true_product_ids, k=5):
    if len(recommended_product_ids) == 0:
        return 0.0
    recommended_k = recommended_product_ids[:k]
    hits = len(set(recommended_k) & set(true_product_ids))
    return hits / k

def recall_at_k(recommended_product_ids, true_product_ids, k=5):
    if len(true_product_ids) == 0:
        return 0.0
    recommended_k = recommended_product_ids[:k]
    hits = len(set(recommended_k) & set(true_product_ids))
    return hits / len(true_product_ids)

def ndcg_at_k(recommended_product_ids, true_product_ids, k=5):
    if len(true_product_ids) == 0:
        return 0.0

    recommended_k = recommended_product_ids[:k]
    dcg = 0.0
    for i, product_id in enumerate(recommended_k):
        if product_id in true_product_ids:
            dcg += 1 / np.log2(i + 2)

    idcg = sum(1 / np.log2(i + 2) for i in range(min(k, len(true_product_ids))))
    return dcg / idcg if idcg > 0 else 0.0

def hit_rate(recommended_product_ids, true_product_ids, k=5):
    if len(true_product_ids) == 0:
        return 0.0
    recommended_k = recommended_product_ids[:k]
    hits = len(set(recommended_k) & set(true_product_ids))
    return 1.0 if hits > 0 else 0.0

def diversity_at_k(recommended_df, k=5):
    """Tính diversity từ dataframe (dùng category column)"""
    if len(recommended_df) == 0:
        return 0.0
    rec_k = recommended_df.head(k)
    unique_categories = rec_k['category'].nunique()
    return unique_categories / k

def mae_score(recommended_product_ids, true_product_ratings, k=5):
    if len(recommended_product_ids) == 0 or len(true_product_ratings) == 0:
        return 0.0
    recommended_k = recommended_product_ids[:k]
    errors = []
    for pid in recommended_k:
        if pid in true_product_ratings:
            errors.append(true_product_ratings[pid])
    return np.mean(errors) if errors else 0.0

# ==================== COMPREHENSIVE EVALUATION ====================

def evaluate_algorithm_improved(algorithm_name, user_id, test_purchases, train_purchases,
                               train_browsing, products, product_images):
    """Evaluate algorithms including Weighted Hybrid + Diversify"""

    try:
        if algorithm_name == 'collaborative':
            recommendations = collaborative_filtering(user_id, train_purchases, products)
        elif algorithm_name == 'content-based':
            recommendations = content_based_filtering(user_id, train_purchases, train_browsing, products)
        elif algorithm_name == 'hybrid':
            recommendations = hybrid_recommendation(user_id, train_purchases, train_browsing, products)
        elif algorithm_name == 'weighted-hybrid':
            # Get dynamic weights
            alpha, beta, gamma = get_dynamic_weights(user_id, train_purchases, train_browsing)
            recommendations = weighted_hybrid_recommendation(user_id, train_purchases, train_browsing,
                                                           products, alpha=alpha, beta=beta, gamma=gamma)
        elif algorithm_name == 'weighted-hybrid-diverse':
            # With diversify
            alpha, beta, gamma = get_dynamic_weights(user_id, train_purchases, train_browsing)
            recommendations = weighted_hybrid_recommendation(user_id, train_purchases, train_browsing,
                                                           products, alpha=alpha, beta=beta, gamma=gamma)
            recommendations = diversify_recommendations(recommendations, k=20)
        elif algorithm_name == 'multi-modal':
            num_users = users['user_id'].nunique()
            num_products = products['product_id'].nunique()
            model = MultiModalModel(num_users, num_products)

            product_ids = torch.LongTensor(products['product_id'].values) - 1
            texts = products['description'].tolist()

            with torch.no_grad():
                outputs = model(
                    torch.LongTensor([user_id - 1]),
                    product_ids,
                    texts,
                    edge_index=None,
                    product_images_df=None
                )

            scores = outputs.mean(dim=1).cpu().numpy()
            recommendations = products.copy()
            recommendations['score'] = scores
            recommendations['source'] = 'Multi-Modal'
            recommendations = diversify_recommendations(recommendations, k=20)
        else:
            return None

        recommended_ids = recommendations['product_id'].values.tolist()
        test_ids = test_purchases['product_id'].values.tolist()

        # Filter out train purchases
        train_ids = train_purchases[train_purchases['user_id'] == user_id]['product_id'].values
        recommended_ids = [pid for pid in recommended_ids if pid not in train_ids]

        # Create dicts for metrics
        category_dict = dict(zip(products['product_id'], products['category']))
        rating_dict = dict(zip(products['product_id'], products['rating']))

        metrics = {
            'precision@5': precision_at_k(recommended_ids, test_ids, 5),
            'precision@10': precision_at_k(recommended_ids, test_ids, 10),
            'recall@5': recall_at_k(recommended_ids, test_ids, 5),
            'recall@10': recall_at_k(recommended_ids, test_ids, 10),
            'ndcg@5': ndcg_at_k(recommended_ids, test_ids, 5),
            'ndcg@10': ndcg_at_k(recommended_ids, test_ids, 10),
            'hit_rate@5': hit_rate(recommended_ids, test_ids, 5),
            'hit_rate@10': hit_rate(recommended_ids, test_ids, 10),
            'diversity@5': diversity_at_k(recommendations, 5),  # ← Dùng từ recommendations DataFrame
            'mae': mae_score(recommended_ids, rating_dict, 10),
        }

        return metrics
    except Exception as e:
        logger.warning(f"Error evaluating {algorithm_name} for user {user_id}: {e}")
        return None

# ==================== MAIN EVALUATION ====================

def run_evaluation_improved(n_test_users=100):
    """
    Evaluation toàn diện: Test 6 algorithms (gồm Weighted Hybrid variants)
    """

    # Get active users
    user_purchase_counts = purchases.groupby('user_id').size()
    active_users = user_purchase_counts[user_purchase_counts >= 5].index.tolist()

    if len(active_users) < n_test_users:
        n_test_users = len(active_users)
        print(f"⚠️  Chỉ có {n_test_users} user có đủ lịch sử mua hàng")

    test_users = np.random.choice(active_users, n_test_users, replace=False)

    results = {
        'collaborative': [],
        'content-based': [],
        'hybrid': [],
        'weighted-hybrid': [],
        'weighted-hybrid-diverse': [],
        'multi-modal': []
    }

    total_products = products['product_id'].nunique()

    print(f"\n🔄 Đang evaluate {len(test_users)} users...")
    print(f"{'='*80}")

    for idx, user_id in enumerate(test_users):
        # Split purchases
        user_purchases = purchases[purchases['user_id'] == user_id]
        train_purchases, test_purchases = train_test_split(
            user_purchases, test_size=0.2, random_state=42
        )

        if len(test_purchases) == 0:
            continue

        # Split browsing
        user_browsing = browsing_history[browsing_history['user_id'] == user_id]
        if len(user_browsing) > 0:
            train_browsing, _ = train_test_split(
                user_browsing, test_size=0.2, random_state=42
            )
        else:
            train_browsing = pd.DataFrame()

        all_train_purchases = pd.concat([
            purchases[purchases['user_id'] != user_id],
            train_purchases
        ])

        # Evaluate each algorithm
        for algo in results.keys():
            metrics = evaluate_algorithm_improved(
                algo, user_id, test_purchases,
                all_train_purchases, train_browsing,
                products, product_images
            )

            if metrics:
                results[algo].append(metrics)

        if (idx + 1) % 20 == 0:
            print(f"✓ Hoàn thành {idx + 1}/{len(test_users)} users")

    # ==================== RESULTS ====================

    print(f"\n{'='*80}")
    print("📊 KẾT QUẢ ĐÁNH GIÁ (6 PHƯƠNG PHÁP)")
    print(f"{'='*80}\n")

    algorithms = ['collaborative', 'content-based', 'hybrid', 'weighted-hybrid',
                  'weighted-hybrid-diverse', 'multi-modal']
    metrics_list = ['precision@5', 'precision@10', 'recall@5', 'recall@10',
                   'ndcg@5', 'ndcg@10', 'hit_rate@5', 'hit_rate@10',
                   'diversity@5', 'mae']

    # Create summary table
    summary_data = []
    for algo in algorithms:
        if len(results[algo]) == 0:
            continue

        avg_metrics = {}
        for metric in metrics_list:
            avg_metrics[metric] = np.mean([r[metric] for r in results[algo]])

        summary_data.append({
            'Algorithm': algo.replace('-', ' ').title(),
            'Precision@5': f"{avg_metrics['precision@5']:.4f}",
            'Recall@5': f"{avg_metrics['recall@5']:.4f}",
            'NDCG@5': f"{avg_metrics['ndcg@5']:.4f}",
            'Diversity@5': f"{avg_metrics['diversity@5']:.4f}",
            'Hit Rate@5': f"{avg_metrics['hit_rate@5']:.4f}",
            'MAE': f"{avg_metrics['mae']:.4f}",
        })

    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))

    # Detailed metrics
    print(f"\n{'='*80}")
    print("📈 CHI TIẾT CÁC METRIC (μ = mean, σ = std)")
    print(f"{'='*80}\n")

    for algo in algorithms:
        if len(results[algo]) == 0:
            print(f"⚠️  {algo.title()}: Không có kết quả")
            continue

        print(f"\n🔹 {algo.upper().replace('-', ' ')}")
        print("-" * 70)

        for metric in metrics_list:
            values = [r[metric] for r in results[algo]]
            print(f"  {metric:20s}: μ={np.mean(values):.4f}  σ={np.std(values):.4f}  "
                  f"[{np.min(values):.4f} - {np.max(values):.4f}]")

    # Rankings and improvements
    print(f"\n{'='*80}")
    print("🏆 SO SÁNH: Hybrid base vs Weighted Hybrid variants")
    print(f"{'='*80}\n")

    if (len(results['hybrid']) > 0 and len(results['weighted-hybrid']) > 0 and
        len(results['weighted-hybrid-diverse']) > 0):

        hybrid_data = results['hybrid']
        wh_data = results['weighted-hybrid']
        wh_diverse_data = results['weighted-hybrid-diverse']

        metrics_compare = ['precision@5', 'recall@5', 'diversity@5', 'hit_rate@5']

        for metric in metrics_compare:
            h_val = np.mean([r[metric] for r in hybrid_data])
            wh_val = np.mean([r[metric] for r in wh_data])
            whd_val = np.mean([r[metric] for r in wh_diverse_data])

            print(f"\n{metric.upper()}:")
            print(f"  Hybrid:              {h_val:.4f}")
            print(f"  Weighted Hybrid:     {wh_val:.4f}  ({(wh_val/h_val - 1)*100:+.1f}%)")
            print(f"  WH + Diverse:        {whd_val:.4f}  ({(whd_val/h_val - 1)*100:+.1f}%)")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    # Run on 100 users
    run_evaluation_improved(n_test_users=100)
