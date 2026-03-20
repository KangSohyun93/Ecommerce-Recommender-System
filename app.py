from flask import Flask, render_template, request, flash, redirect, url_for
import pandas as pd
import torch
from model import (collaborative_filtering, content_based_filtering, hybrid_recommendation,
                   weighted_hybrid_recommendation, get_dynamic_weights, diversify_recommendations,
                   MultiModalModel)
from premium_algorithm import classify_user_segment, calculate_popularity_score
import logging
import numpy as np

app = Flask(__name__)
app.secret_key = 'your-secret-key'
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load data from datasets folder
import os
DATA_DIR = os.path.join(os.path.dirname(__file__), 'datasets')

# Config: Set to True to use filtered dataset (high-confidence products only)
USE_FILTERED_DATASET = True

def load_data(use_filtered=False):
    """Load dataset with optional filtering"""
    if use_filtered:
        filtered_dir = os.path.join(DATA_DIR, 'filtered')
        users = pd.read_csv(os.path.join(DATA_DIR, 'users_expanded.csv'))
        products = pd.read_csv(os.path.join(filtered_dir, 'products_filtered.csv'))
        purchases = pd.read_csv(os.path.join(filtered_dir, 'purchases_filtered.csv'))
        browsing_history = pd.read_csv(os.path.join(filtered_dir, 'browsing_filtered.csv'))
        logger.info(f"[LOADED] Filtered dataset: {len(products)} products, {len(purchases)} purchases")
    else:
        users = pd.read_csv(os.path.join(DATA_DIR, 'users_expanded.csv'))
        products = pd.read_csv(os.path.join(DATA_DIR, 'products_expanded.csv'))
        purchases = pd.read_csv(os.path.join(DATA_DIR, 'purchases_expanded.csv'))
        browsing_history = pd.read_csv(os.path.join(DATA_DIR, 'browsing_history_expanded.csv'))
        logger.info(f"[LOADED] Full dataset: {len(products)} products, {len(purchases)} purchases")

    product_images = pd.read_csv(os.path.join(DATA_DIR, 'product_images_expanded.csv'))
    return users, products, purchases, browsing_history, product_images

# Load data
users, products, purchases, browsing_history, product_images = load_data(use_filtered=USE_FILTERED_DATASET)

# Initialize multi-modal model
num_users = users['user_id'].nunique()
num_products = products['product_id'].nunique()
model = MultiModalModel(num_users, num_products)
logger.info(f"[CONFIG] Using {'FILTERED' if USE_FILTERED_DATASET else 'FULL'} dataset for recommendations")

@app.route('/')
def index():
    return render_template('index.html', products=products.to_dict(orient='records'))

@app.route('/recommend', methods=['POST'])
def get_recommendations():
    try:
        user_id = int(request.form['user_id'])
        algorithm = request.form['algorithm']
        logger.debug(f"Processing request for user_id: {user_id}, algorithm: {algorithm}")

        if user_id not in users['user_id'].values:
            flash('User ID not found!')
            return redirect(url_for('index'))

        # Get interacted products
        purchased_product_ids = purchases[purchases['user_id'] == user_id]['product_id'].unique()
        browsed_product_ids = browsing_history[browsing_history['user_id'] == user_id]['product_id'].unique()
        interacted_products = products[products['product_id'].isin(purchased_product_ids) |
                                      products['product_id'].isin(browsed_product_ids)].copy()
        interacted_products['source'] = interacted_products['product_id'].apply(
            lambda x: 'Purchased' if x in purchased_product_ids else 'Browsed'
        )
        logger.debug(f"Interacted products: {interacted_products['product_id'].tolist()}")

        # Generate recommendations
        if algorithm == 'collaborative':
            recommendations = collaborative_filtering(user_id, purchases, products)
        elif algorithm == 'content-based':
            recommendations = content_based_filtering(user_id, purchases, browsing_history, products)
        elif algorithm == 'hybrid':
            recommendations = hybrid_recommendation(user_id, purchases, browsing_history, products)
        elif algorithm == 'weighted-hybrid':
            # Get dynamic weights based on user interaction count
            alpha, beta, gamma = get_dynamic_weights(user_id, purchases, browsing_history)
            recommendations = weighted_hybrid_recommendation(user_id, purchases, browsing_history,
                                                           products, alpha=alpha, beta=beta, gamma=gamma)
            # Diversify by category
            recommendations = diversify_recommendations(recommendations, k=20)
        elif algorithm == 'improved':
            # NEW: Improved algorithm using filtered dataset or weighted-hybrid with boosting
            alpha, beta, gamma = get_dynamic_weights(user_id, purchases, browsing_history)
            recommendations = weighted_hybrid_recommendation(user_id, purchases, browsing_history,
                                                           products, alpha=alpha, beta=beta, gamma=gamma)

            # Boost scores for products with high interaction count (confidence-based)
            purchases_per_product = purchases.groupby('product_id').size()
            high_confidence_threshold = 20  # Same as filtering threshold
            recommendations['confidence'] = recommendations['product_id'].map(
                lambda pid: 1.0 if pid in purchases_per_product.index and purchases_per_product[pid] >= high_confidence_threshold else 0.5
            ).fillna(0.5)
            recommendations['score'] = recommendations['score'] * recommendations['confidence']

            # Diversify by category
            recommendations = diversify_recommendations(recommendations, k=20)
        elif algorithm == 'premium':
            # PREMIUM v2.0: Ensemble + Recency + User Segmentation
            alpha, beta, gamma = get_dynamic_weights(user_id, purchases, browsing_history)
            recommendations = weighted_hybrid_recommendation(user_id, purchases, browsing_history,
                                                           products, alpha=alpha, beta=beta, gamma=gamma)

            # Get user segment
            segment, segment_weights = classify_user_segment(user_id, purchases, browsing_history)

            # Calculate popularity scores
            popularity_scores = calculate_popularity_score(purchases, products)

            # Build ensemble scores
            cf_scores = recommendations['score'].values
            cb_scores = recommendations['score'].values * 0.8  # Reduce CB slightly

            # Normalize
            cf_norm = (cf_scores - cf_scores.min()) / (cf_scores.max() - cf_scores.min() + 1e-5)
            cb_norm = (cb_scores - cb_scores.min()) / (cb_scores.max() - cb_scores.min() + 1e-5)
            pop_array = np.array([popularity_scores.get(pid, 0.0) for pid in recommendations['product_id'].values])
            pop_norm = (pop_array - pop_array.min()) / (pop_array.max() - pop_array.min() + 1e-5)

            # Apply segment weights (all LOYAL in filtered dataset)
            recommendations['score'] = (
                segment_weights['cf'] * cf_norm +
                segment_weights['cb'] * cb_norm +
                segment_weights['pop'] * pop_norm
            )

            recommendations['segment'] = segment
            recommendations['source'] = f'Premium+ ({segment})'

            # Diversify by category
            recommendations = diversify_recommendations(recommendations, k=20)
        elif algorithm == 'multi-modal':
            # Prepare multi-modal inputs
            # Adjust product IDs to be 0-indexed for the embedding layer
            product_ids = torch.LongTensor(products['product_id'].values) - 1
            texts = products['description'].tolist()

            # Generate recommendations using all available modalities
            with torch.no_grad():
                outputs = model(
                    torch.LongTensor([user_id - 1]),
                    product_ids,
                    texts,
                    edge_index=None,
                    product_images_df=None
                )

            # Calculate recommendation scores
            scores = outputs.mean(dim=1).cpu().numpy()

            # Create recommendations dataframe
            recommendations = products.copy()
            recommendations['score'] = scores
            recommendations['source'] = 'Multi-Modal'
            # Diversify multi-modal as well
            recommendations = diversify_recommendations(recommendations, k=20)
        else:
            flash('Invalid algorithm selected!')
            return redirect(url_for('index'))

        # Filter out interacted products
        recommended_products = recommendations[~recommendations['product_id'].isin(purchased_product_ids) &
                                               ~recommendations['product_id'].isin(browsed_product_ids)].copy()
        logger.debug(f"Filtered recommendations:\n{recommended_products[['product_id', 'score', 'source']]}")

        if recommended_products.empty:
            flash('No recommendations available for this user.')

        return render_template('recommendations.html',
                             interacted_products=interacted_products.to_dict(orient='records'),
                             recommended_products=recommended_products.to_dict(orient='records'))
    except Exception as e:
        logger.error(f"Error in get_recommendations: {str(e)}")
        flash(f'An error occurred: {str(e)}')
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Use gunicorn in production, debug mode locally
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)