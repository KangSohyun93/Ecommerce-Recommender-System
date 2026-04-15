import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def classify_user_segment(user_id, purchases, browsing_history):
    """
    User Segmentation Formula: Segment = classify(total_interactions)
    where interactions = unique_products_purchased + unique_products_browsed
    Returns: ('NEW':<5, 'ACTIVE':5-20, 'LOYAL':>20) + adaptive weights
    Phân loại người dùng dựa trên số lần tương tác = mua + xem
    """
    user_purchases = purchases[purchases['user_id'] == user_id]['product_id'].nunique()
    user_browsed = browsing_history[browsing_history['user_id'] == user_id]['product_id'].nunique()
    total_interactions = user_purchases + user_browsed

    if total_interactions < 5:
        return 'NEW', {'cf': 0.2, 'cb': 0.6, 'pop': 0.2, 'recency': 0.0}
    elif total_interactions < 20:
        return 'ACTIVE', {'cf': 0.4, 'cb': 0.4, 'pop': 0.1, 'recency': 0.1}
    else:
        return 'LOYAL', {'cf': 0.5, 'cb': 0.2, 'pop': 0.1, 'recency': 0.2}

def calculate_recency_weight(purchase_dates_by_product, days_window=60):
    """
    Recency Weight Formula: weight = min(1.0, purchase_count / (days_window/30))
    Logic: More recent purchases and higher frequency → higher recency weight
    Tiếng Việt: Trọng số gần đây = min(1.0, số lần mua / (cửa_sổ_ngày/30))
    """
    if not hasattr(purchase_dates_by_product, '__iter__'):
        return {}

    recency_weights = {}
    cutoff_date = datetime.now() - timedelta(days=days_window)

    for product_id, dates in purchase_dates_by_product.items():
        # For products, assume purchase date is recent if in dataset
        # Give full boost to products frequently purchased
        recency_weights[product_id] = min(1.0, len(dates) / (days_window / 30))

    return recency_weights

def calculate_popularity_score(purchases, products):
    """
    Popularity Score Formula: score = 0.6×(freq/max_freq) + 0.4×(unique_buyers/max_buyers)
    Logic: Weighted combination of purchase frequency and buyer diversity
    Tiếng Việt: Điểm phổ biến = 0.6×(tần_suất/max) + 0.4×(độc_nhất_mua/max)
    """
    purchase_freq = purchases.groupby('product_id').size()
    unique_buyers = purchases.groupby('product_id')['user_id'].nunique()

    popularity_scores = {}
    for product_id in products['product_id'].values:
        if product_id in purchase_freq.index:
            freq_score = purchase_freq[product_id] / purchase_freq.max()
            buyer_score = unique_buyers[product_id] / unique_buyers.max()
            # Weighted Popularity Formula: 0.6×frequency + 0.4×buyer_diversity
            popularity_scores[product_id] = 0.6 * freq_score + 0.4 * buyer_score
        else:
            popularity_scores[product_id] = 0.0

    return popularity_scores

def premium_hybrid_recommendation(user_id, purchases, browsing_history, products,
                                 cf_scores=None, cb_scores=None):
    """
    Premium Hybrid Algorithm v2.0:
    - Ensemble: CF + CB + Popularity + Recency
    - User Segmentation: Different weights per user type
    - Adaptive weights based on interaction count
    """

    # Step 1: User segmentation
    segment, segment_weights = classify_user_segment(user_id, purchases, browsing_history)

    # Step 2: Calculate component scores
    if cf_scores is None:
        cf_scores = {}
    if cb_scores is None:
        cb_scores = {}

    popularity_scores = calculate_popularity_score(purchases, products)
    recency_weights = calculate_recency_weight({})

    # Step 3: Normalize scores (0-1)
    cf_array = np.array([cf_scores.get(pid, 0.0) for pid in products['product_id'].values])
    cb_array = np.array([cb_scores.get(pid, 0.0) for pid in products['product_id'].values])
    pop_array = np.array([popularity_scores.get(pid, 0.0) for pid in products['product_id'].values])
    rec_array = np.array([recency_weights.get(pid, 0.5) for pid in products['product_id'].values])

    # Normalize each component
    cf_norm = (cf_array - cf_array.min()) / (cf_array.max() - cf_array.min() + 1e-5)
    cb_norm = (cb_array - cb_array.min()) / (cb_array.max() - cb_array.min() + 1e-5)
    pop_norm = (pop_array - pop_array.min()) / (pop_array.max() - pop_array.min() + 1e-5)
    rec_norm = (rec_array - rec_array.min()) / (rec_array.max() - rec_array.min() + 1e-5)

    # Step 4: Apply segment-specific weights
    ensemble_score = (
        segment_weights['cf'] * cf_norm +
        segment_weights['cb'] * cb_norm +
        segment_weights['pop'] * pop_norm +
        segment_weights['recency'] * rec_norm
    )

    # Step 5: Create result dataframe
    results = products.copy()
    results['cf_score'] = cf_norm
    results['cb_score'] = cb_norm
    results['popularity_score'] = pop_norm
    results['recency_score'] = rec_norm
    results['score'] = ensemble_score
    results['segment'] = segment
    results['source'] = f'Premium ({segment})'

    return results.sort_values('score', ascending=False)

def adaptive_premium_recommendation(user_id, purchases, browsing_history, products):
    """
    Adaptive Premium: Automatically select best method per user
    """
    user_interactions = len(purchases[purchases['user_id'] == user_id])

    segment, weights = classify_user_segment(user_id, purchases, browsing_history)

    # Build from scratch or use existing functions
    # For now, return premium result
    recommendations = products.copy()
    recommendations['score'] = np.random.rand(len(products))  # Placeholder
    recommendations['segment'] = segment
    recommendations['source'] = f'Adaptive Premium ({segment})'

    return recommendations

# ====== TESTING FUNCTIONS ======

def test_premium_algorithm():
    """
    Test the premium algorithm on sample data
    """
    import os
    import sys

    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    DATA_DIR = os.path.join(os.path.dirname(__file__), 'datasets')

    # Load data
    products = pd.read_csv(os.path.join(DATA_DIR, 'filtered', 'products_filtered.csv'))
    purchases = pd.read_csv(os.path.join(DATA_DIR, 'filtered', 'purchases_filtered.csv'))
    browsing = pd.read_csv(os.path.join(DATA_DIR, 'filtered', 'browsing_filtered.csv'))

    print("\n" + "="*80)
    print("[TEST] Premium Algorithm Segmentation Analysis")
    print("="*80)

    # Test on few users
    test_users = purchases['user_id'].unique()[:5]

    print(f"\nTesting on {len(test_users)} sample users:\n")
    print(f"{'User ID':<10} {'Purchases':<15} {'Browsed':<15} {'Segment':<15} {'Weights':<50}")
    print("-"*100)

    for user_id in test_users:
        user_purchases = len(purchases[purchases['user_id'] == user_id])
        user_browsed = len(browsing[browsing['user_id'] == user_id])
        segment, weights = classify_user_segment(user_id, purchases, browsing)

        weights_str = f"CF:{weights['cf']:.1f} CB:{weights['cb']:.1f} Pop:{weights['pop']:.1f} Rec:{weights['recency']:.1f}"
        print(f"{user_id:<10} {user_purchases:<15} {user_browsed:<15} {segment:<15} {weights_str:<50}")

    # Summary
    print("\n" + "="*80)
    print("User Segment Distribution:")
    print("="*80)

    all_users = purchases['user_id'].unique()
    segments = {'NEW': 0, 'ACTIVE': 0, 'LOYAL': 0}

    for user_id in all_users:
        segment, _ = classify_user_segment(user_id, purchases, browsing)
        segments[segment] += 1

    for seg, count in segments.items():
        pct = (count / len(all_users)) * 100
        print(f"  {seg:<10} {count:<10} ({pct:>6.1f}%)")

    print("\n" + "="*80)
    print("Algorithm Weights per Segment:")
    print("="*80)

    weight_examples = {
        'NEW': {'cf': 0.2, 'cb': 0.6, 'pop': 0.2, 'recency': 0.0},
        'ACTIVE': {'cf': 0.4, 'cb': 0.4, 'pop': 0.1, 'recency': 0.1},
        'LOYAL': {'cf': 0.5, 'cb': 0.2, 'pop': 0.1, 'recency': 0.2},
    }

    for segment, weights in weight_examples.items():
        print(f"\n{segment} Users:")
        print(f"  CF (Collaborative):    {weights['cf']*100:>5.0f}%  (User similarity based)")
        print(f"  CB (Content-Based):    {weights['cb']*100:>5.0f}%  (Product similarity)")
        print(f"  Popularity:            {weights['pop']*100:>5.0f}%  (Popular items)")
        print(f"  Recency:               {weights['recency']*100:>5.0f}%  (Recently purchased)")

    print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    test_premium_algorithm()
