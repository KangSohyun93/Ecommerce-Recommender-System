import pandas as pd
import numpy as np
import torch
import os
from model import (collaborative_filtering, content_based_filtering,
                   hybrid_recommendation, MultiModalModel)
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
    """Tỷ lệ sản phẩm được recommend mà user thực sự mua"""
    if len(recommended_product_ids) == 0:
        return 0.0
    recommended_k = recommended_product_ids[:k]
    hits = len(set(recommended_k) & set(true_product_ids))
    return hits / k

def recall_at_k(recommended_product_ids, true_product_ids, k=5):
    """Tỷ lệ sản phẩm user mua được recommendation cover"""
    if len(true_product_ids) == 0:
        return 0.0
    recommended_k = recommended_product_ids[:k]
    hits = len(set(recommended_k) & set(true_product_ids))
    return hits / len(true_product_ids)

def ndcg_at_k(recommended_product_ids, true_product_ids, k=5):
    """Normalized Discounted Cumulative Gain - xếp hạng quan trọng nhất ở top"""
    if len(true_product_ids) == 0:
        return 0.0

    recommended_k = recommended_product_ids[:k]

    # DCG: Cumulative gain weighted by position
    dcg = 0.0
    for i, product_id in enumerate(recommended_k):
        if product_id in true_product_ids:
            dcg += 1 / np.log2(i + 2)  # Position weight

    # IDCG: Ideal DCG (all true items ranked first)
    idcg = sum(1 / np.log2(i + 2) for i in range(min(k, len(true_product_ids))))

    return dcg / idcg if idcg > 0 else 0.0

def hit_rate(recommended_product_ids, true_product_ids, k=5):
    """Có ít nhất 1 hit"""
    if len(true_product_ids) == 0:
        return 0.0
    recommended_k = recommended_product_ids[:k]
    hits = len(set(recommended_k) & set(true_product_ids))
    return 1.0 if hits > 0 else 0.0

def coverage(all_recommendations, total_products):
    """% sản phẩm được recommend ít nhất 1 lần"""
    unique_recommended = set(all_recommendations)
    return len(unique_recommended) / total_products

def diversity(recommended_product_ids, product_categories_dict, k=5):
    """Tỷ lệ các category khác nhau trong top-k"""
    recommended_k = recommended_product_ids[:k]
    categories = [product_categories_dict.get(pid, 'Unknown') for pid in recommended_k]
    unique_categories = len(set(categories))
    return unique_categories / len(recommended_k) if len(recommended_k) > 0 else 0.0

def mae_score(recommended_product_ids, true_product_ratings, k=5):
    """Mean Absolute Error - so sánh rating"""
    if len(recommended_product_ids) == 0 or len(true_product_ratings) == 0:
        return 0.0
    recommended_k = recommended_product_ids[:k]
    errors = []
    for pid in recommended_k:
        if pid in true_product_ratings:
            errors.append(true_product_ratings[pid])
    return np.mean(errors) if errors else 0.0

# ==================== EVALUATION ====================

def evaluate_algorithm(algorithm_name, user_id, test_purchases, train_purchases,
                      train_browsing, products, product_images):
    """Evaluate một algorithm cho user cụ thể"""

    try:
        if algorithm_name == 'collaborative':
            recommendations = collaborative_filtering(user_id, train_purchases, products)
        elif algorithm_name == 'content-based':
            recommendations = content_based_filtering(user_id, train_purchases, train_browsing, products)
        elif algorithm_name == 'hybrid':
            recommendations = hybrid_recommendation(user_id, train_purchases, train_browsing, products)
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
                    product_images_df=None  # Skip image loading
                )

            scores = outputs.mean(dim=1).cpu().numpy()
            recommendations = products.copy()
            recommendations['score'] = scores
            recommendations['source'] = 'Multi-Modal'
        else:
            return None

        recommended_ids = recommendations['product_id'].values.tolist()
        test_ids = test_purchases['product_id'].values.tolist()

        # Filter out train purchases
        train_ids = train_purchases[train_purchases['user_id'] == user_id]['product_id'].values
        recommended_ids = [pid for pid in recommended_ids if pid not in train_ids]

        # Create category dict for diversity
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
            'diversity@5': diversity(recommended_ids, category_dict, 5),
            'mae': mae_score(recommended_ids, rating_dict, 10),
        }

        return metrics
    except Exception as e:
        logger.warning(f"Error evaluating {algorithm_name} for user {user_id}: {e}")
        return None

# ==================== MAIN EVALUATION ====================

def run_evaluation(n_test_users=50):
    """
    Chạy evaluation trên n_test_users
    Chia 80% lịch sử làm train, 20% làm test
    """

    # Get users with enough purchase history (ít nhất 5 lần mua)
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
        'multi-modal': []
    }

    coverage_data = {
        'collaborative': [],
        'content-based': [],
        'hybrid': [],
        'multi-modal': []
    }

    total_products = products['product_id'].nunique()

    print(f"\n🔄 Đang evaluate {len(test_users)} users...")
    print(f"{'='*80}")

    for idx, user_id in enumerate(test_users):
        # Split purchases: 80% train, 20% test
        user_purchases = purchases[purchases['user_id'] == user_id]
        train_purchases, test_purchases = train_test_split(
            user_purchases, test_size=0.2, random_state=42
        )

        # Only evaluate if user has test purchases
        if len(test_purchases) == 0:
            continue

        # Split browsing history similarly
        user_browsing = browsing_history[browsing_history['user_id'] == user_id]
        if len(user_browsing) > 0:
            train_browsing, _ = train_test_split(
                user_browsing, test_size=0.2, random_state=42
            )
        else:
            train_browsing = pd.DataFrame()

        # Combine all train purchases for other users
        all_train_purchases = pd.concat([
            purchases[purchases['user_id'] != user_id],
            train_purchases
        ])

        # Evaluate each algorithm
        for algo in results.keys():
            metrics = evaluate_algorithm(
                algo, user_id, test_purchases,
                all_train_purchases, train_browsing,
                products, product_images
            )

            if metrics:
                results[algo].append(metrics)

        if (idx + 1) % 10 == 0:
            print(f"✓ Hoàn thành {idx + 1}/{len(test_users)} users")

    # ==================== PRINT RESULTS ====================

    print(f"\n{'='*80}")
    print("📊 KẾT QUẢ ĐÁNH GIÁ HIỆU SUẤT")
    print(f"{'='*80}\n")

    algorithms = ['collaborative', 'content-based', 'hybrid', 'multi-modal']
    metrics_list = [
        'precision@5', 'precision@10', 'recall@5', 'recall@10',
        'ndcg@5', 'ndcg@10', 'hit_rate@5', 'hit_rate@10',
        'diversity@5', 'mae'
    ]

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
            'Precision@5': f"{avg_metrics['precision@5']:.3f}",
            'Recall@5': f"{avg_metrics['recall@5']:.3f}",
            'NDCG@5': f"{avg_metrics['ndcg@5']:.3f}",
            'Hit Rate@5': f"{avg_metrics['hit_rate@5']:.3f}",
            'Diversity@5': f"{avg_metrics['diversity@5']:.3f}",
            'MAE': f"{avg_metrics['mae']:.3f}",
        })

    summary_df = pd.DataFrame(summary_data)
    print(summary_df.to_string(index=False))

    # Detailed metrics
    print(f"\n{'='*80}")
    print("📈 CHI TIẾT CÁC METRIC")
    print(f"{'='*80}\n")

    for algo in algorithms:
        if len(results[algo]) == 0:
            print(f"⚠️  {algo.title()}: Không có kết quả")
            continue

        print(f"\n🔹 {algo.replace('-', ' ').upper()}")
        print("-" * 60)

        for metric in metrics_list:
            values = [r[metric] for r in results[algo]]
            print(f"  {metric:15s}: μ={np.mean(values):.4f}  σ={np.std(values):.4f}  "
                  f"min={np.min(values):.4f}  max={np.max(values):.4f}")

    # Rankings
    print(f"\n{'='*80}")
    print("🏆 RANKING THEO CÁC METRIC")
    print(f"{'='*80}\n")

    for metric in ['precision@5', 'recall@5', 'ndcg@5', 'hit_rate@5']:
        rankings = []
        for algo in algorithms:
            if len(results[algo]) > 0:
                avg = np.mean([r[metric] for r in results[algo]])
                rankings.append((algo.title(), avg))

        rankings.sort(key=lambda x: x[1], reverse=True)
        print(f"\n📌 {metric.upper()}")
        for rank, (algo, score) in enumerate(rankings, 1):
            print(f"  {rank}. {algo:20s}: {score:.4f}")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    # Run evaluation on 1000 test users
    run_evaluation(n_test_users=1000)

    # Or run on all active users: run_evaluation(n_test_users=999)
