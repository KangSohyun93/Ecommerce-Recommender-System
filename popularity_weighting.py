"""
Improved recommendation models with popularity weighting
Helps overcome cold-start problem
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def calculate_product_popularity(purchases, products, window_days=None):
    """
    Calculate popularity score for each product

    Metrics:
    - Purchase frequency
    - Unique users
    - Average rating
    """

    # Purchase frequency
    purchase_freq = purchases.groupby('product_id').size()

    # Unique users for each product
    unique_users = purchases.groupby('product_id')['user_id'].nunique()

    # Rating
    product_ratings = products.set_index('product_id')['rating']

    popularity = pd.DataFrame({
        'product_id': purchase_freq.index,
        'purchase_count': purchase_freq.values,
        'unique_users': unique_users.values,
        'rating': [product_ratings.get(pid, 3.0) for pid in purchase_freq.index]
    })

    # Normalize scores
    popularity['freq_score'] = (popularity['purchase_count'] - popularity['purchase_count'].min()) / \
                               (popularity['purchase_count'].max() - popularity['purchase_count'].min() + 1)
    popularity['user_score'] = (popularity['unique_users'] - popularity['unique_users'].min()) / \
                              (popularity['unique_users'].max() - popularity['unique_users'].min() + 1)
    popularity['rating_score'] = (popularity['rating'] - 3.0) / 2.0  # Normalize 3-5 to 0-1

    # Combined popularity score (weighted average)
    popularity['popularity_score'] = (
        0.5 * popularity['freq_score'] +
        0.3 * popularity['user_score'] +
        0.2 * popularity['rating_score']
    )

    return popularity.set_index('product_id')['popularity_score'].to_dict()

def boost_recommendations_with_popularity(recommendations_df, popularity_dict, boost_factor=0.3):
    """
    Boost recommendation scores with popularity weight

    Formula: final_score = (1-α) * original_score + α * popularity_score
    where α = boost_factor (default 0.3)
    """

    recommendations_df = recommendations_df.copy()

    # Get popularity scores
    pop_scores = recommendations_df['product_id'].map(lambda pid: popularity_dict.get(pid, 0.5))

    # Normalize existing scores
    if 'score' in recommendations_df.columns:
        original_score = recommendations_df['score']
        min_score = original_score.min()
        max_score = original_score.max()
        if max_score > min_score:
            norm_score = (original_score - min_score) / (max_score - min_score)
        else:
            norm_score = 0.5

        # Combine with popularity
        recommendations_df['score'] = (1 - boost_factor) * norm_score + boost_factor * pop_scores
        recommendations_df['score_breakdown'] = original_score  # Keep original for tracking
    else:
        recommendations_df['score'] = pop_scores

    return recommendations_df

def popularity_recommendation(user_id, purchases, products, top_k=20):
    """
    Simple popularity-based recommendation
    Good baseline for cold-start users
    """

    user_purchases = purchases[purchases['user_id'] == user_id]['product_id'].unique()

    # Calculate popularity
    popularity = calculate_product_popularity(purchases, products)

    # Get top products excluding already purchased
    all_products = pd.DataFrame({
        'product_id': products['product_id'],
        'popularity_score': [popularity.get(pid, 0) for pid in products['product_id']]
    })

    available = all_products[~all_products['product_id'].isin(user_purchases)]
    top_products = available.nlargest(top_k, 'popularity_score')

    recommendations = products[products['product_id'].isin(top_products['product_id'])].copy()
    recommendations['score'] = recommendations['product_id'].map(popularity)
    recommendations['source'] = 'Popularity'

    return recommendations.sort_values('score', ascending=False)

# Example usage
if __name__ == '__main__':
    import os

    DATA_DIR = os.path.join(os.path.dirname(__file__), 'datasets')

    print("Loading data...")
    purchases = pd.read_csv(os.path.join(DATA_DIR, 'purchases_expanded.csv'))
    products = pd.read_csv(os.path.join(DATA_DIR, 'products_expanded.csv'))

    print("\n" + "="*80)
    print("Testing Popularity-Based Recommendation")
    print("="*80)

    # Test user
    user_id = 1
    print(f"\nUser {user_id} recommendations (Popularity-based):")

    recs = popularity_recommendation(user_id, purchases, products, top_k=10)
    print(recs[['product_id', 'name', 'category', 'rating', 'score']].head(10))

    print("\n" + "="*80)
    print("✅ Popularity weighting can improve:")
    print("  • Cold-start users (new users with no history)")
    print("  • New products (boost popular ones quickly)")
    print("  • Diversity (popular items vary in category)")
    print("="*80)
