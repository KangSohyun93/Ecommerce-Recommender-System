import pandas as pd
import logging
import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv
from sentence_transformers import SentenceTransformer
from torchvision.models import resnet50
from torchvision import transforms
from PIL import Image
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def collaborative_filtering(user_id, purchases, products):
    logger.debug(f"Collaborative Filtering for user_id: {user_id}")
    user_purchases = purchases[purchases['user_id'] == user_id]['product_id'].unique()
    logger.debug(f"User purchases: {user_purchases}")
    other_users = purchases[purchases['product_id'].isin(user_purchases) & 
                            (purchases['user_id'] != user_id)]['user_id'].unique()
    other_purchases = purchases[purchases['user_id'].isin(other_users)]

    product_counts = other_purchases['product_id'].value_counts()
    recommendations = products[products['product_id'].isin(product_counts.index) & 
                               ~products['product_id'].isin(user_purchases)].copy()
    
    # Enhanced scoring: frequency * rating, normalized
    recommendations['score'] = (recommendations['product_id'].map(product_counts).fillna(0) * 
                                recommendations['rating']) / product_counts.max()
    recommendations['source'] = 'Collaborative Filtering'
    logger.debug(f"Collaborative recommendations:\n{recommendations[['product_id', 'score', 'source']]}")
    return recommendations.sort_values(by='score', ascending=False)

def content_based_filtering(user_id, purchases, browsing_history, products):
    logger.debug(f"Content-Based Filtering for user_id: {user_id}")
    user_history = browsing_history[browsing_history['user_id'] == user_id]['product_id'].unique()
    logger.debug(f"User browsing history: {user_history}")
    user_products = products[products['product_id'].isin(user_history)]

    if not user_products.empty and 'category' in products.columns:
        recommendations = products[products['category'].isin(user_products['category']) & 
                                   ~products['product_id'].isin(user_history)].copy()
        # Enhanced scoring: average rating of browsed products in category
        avg_rating = user_products['rating'].mean()
        recommendations['score'] = recommendations['rating'] / 5.0 * avg_rating
    else:
        recommendations = pd.DataFrame(columns=['product_id', 'product_name', 'price', 'rating', 'score', 'source'])
        logger.debug("No content-based recommendations.")
    
    recommendations['source'] = 'Content-Based Filtering'
    logger.debug(f"Content-based recommendations:\n{recommendations[['product_id', 'score', 'source']]}")
    return recommendations

def hybrid_recommendation(user_id, purchases, browsing_history, products):
    logger.debug(f"Hybrid Recommendation for user_id: {user_id}")

    user_purchases = purchases[purchases['user_id'] == user_id]['product_id'].unique()
    user_browsed = browsing_history[browsing_history['user_id'] == user_id]['product_id'].unique()
    user_history = set(user_purchases).union(user_browsed)
    logger.debug(f"User history (purchases + browsed): {user_history}")

    collab_recs = collaborative_filtering(user_id, purchases, products)
    content_recs = content_based_filtering(user_id, purchases, browsing_history, products)

    all_recommendations = pd.concat([collab_recs, content_recs], ignore_index=True)
    logger.debug(f"Combined recommendations:\n{all_recommendations[['product_id', 'score', 'source']]}")

    if all_recommendations.empty:
        logger.debug("No recommendations; adding popular products.")
        popular_products = purchases['product_id'].value_counts().head(3).index
        all_recommendations = products[products['product_id'].isin(popular_products) &
                                      ~products['product_id'].isin(user_history)].copy()
        all_recommendations['score'] = 0.5
        all_recommendations['source'] = 'Popular Products'

    final_recommendations = all_recommendations.sort_values(by='score', ascending=False) \
                                               .drop_duplicates(subset=['product_id'], keep='first')
    logger.debug(f"Final hybrid recommendations:\n{final_recommendations[['product_id', 'score', 'source']]}")

    return final_recommendations

def get_dynamic_weights(user_id, purchases, browsing_history):
    """
    Tính Dynamic Weights dựa vào số lần tương tác của user

    Trả về: (alpha, beta, gamma) - Trọng số cho CF, CB, Deep Learning

    Rules:
    - User mới (< 3 interactions): Ưu tiên CB (0.1, 0.8, 0.1)
    - User trung bình (3-10): Chia đều CF và CB (0.5, 0.4, 0.1)
    - User trung thành (> 10): Ưu tiên CF (0.7, 0.2, 0.1)
    """
    user_purchases = purchases[purchases['user_id'] == user_id]['product_id'].nunique()
    user_browsed = browsing_history[browsing_history['user_id'] == user_id]['product_id'].nunique()
    total_interactions = user_purchases + user_browsed

    logger.debug(f"User {user_id}: {total_interactions} interactions (P:{user_purchases}, B:{user_browsed})")

    if total_interactions < 3:
        weights = (0.1, 0.8, 0.1)  # New user: prioritize CB
        logger.debug(f"→ New User (< 3): weights={weights}")
    elif total_interactions < 10:
        weights = (0.5, 0.4, 0.1)  # Medium user: balanced
        logger.debug(f"→ Medium User (3-10): weights={weights}")
    else:
        weights = (0.7, 0.2, 0.1)  # Loyal user: prioritize CF
        logger.debug(f"→ Loyal User (> 10): weights={weights}")

    return weights

def normalize_scores(scores):
    """Normalize điểm từ 0-1 cho các phương pháp"""
    if len(scores) == 0:
        return scores
    min_score = scores.min()
    max_score = scores.max()
    if max_score == min_score:
        return pd.Series([0.5] * len(scores), index=scores.index)
    return (scores - min_score) / (max_score - min_score)

def weighted_hybrid_recommendation(user_id, purchases, browsing_history, products, alpha=0.5, beta=0.4, gamma=0.1):
    """
    Weighted Hybrid với Dynamic Weights

    alpha: Trọng số Collaborative Filtering
    beta: Trọng số Content-Based Filtering
    gamma: Trọng số Deep Learning (nếu có)
    """
    logger.debug(f"Weighted Hybrid (α={alpha}, β={beta}, γ={gamma}) for user_id: {user_id}")

    user_purchases = purchases[purchases['user_id'] == user_id]['product_id'].unique()
    user_browsed = browsing_history[browsing_history['user_id'] == user_id]['product_id'].unique()
    user_history = set(user_purchases).union(user_browsed)

    # Get recommendations from each algorithm
    collab_recs = collaborative_filtering(user_id, purchases, products)
    content_recs = content_based_filtering(user_id, purchases, browsing_history, products)

    # Normalize scores to 0-1 range
    collab_recs = collab_recs.copy()
    content_recs = content_recs.copy()

    collab_recs['norm_score'] = normalize_scores(collab_recs['score'])
    content_recs['norm_score'] = normalize_scores(content_recs['score'])

    logger.debug(f"CF: {len(collab_recs)} recs (avg score: {collab_recs['norm_score'].mean():.3f})")
    logger.debug(f"CB: {len(content_recs)} recs (avg score: {content_recs['norm_score'].mean():.3f})")

    # Merge all recommendations and calculate weighted score
    merged = pd.concat([collab_recs, content_recs], ignore_index=True)

    # Group by product_id and calculate weighted score
    final_recs = []
    for product_id in merged['product_id'].unique():
        product_data = merged[merged['product_id'] == product_id]

        # Get normalized scores from each source
        cf_score = product_data[product_data['source'] == 'Collaborative Filtering']['norm_score'].values
        cf_score = cf_score[0] if len(cf_score) > 0 else 0

        cb_score = product_data[product_data['source'] == 'Content-Based Filtering']['norm_score'].values
        cb_score = cb_score[0] if len(cb_score) > 0 else 0

        # Calculate weighted score
        weighted_score = (alpha * cf_score) + (beta * cb_score)

        # Get product info from first match
        product_info = product_data.iloc[0]

        final_recs.append({
            'product_id': product_id,
            'name': product_info['name'],
            'category': product_info['category'],
            'description': product_info['description'],
            'price': product_info['price'],
            'rating': product_info['rating'],
            'score': weighted_score,
            'source': 'Weighted Hybrid'
        })

    final_recs_df = pd.DataFrame(final_recs)

    if final_recs_df.empty:
        logger.debug("No recommendations; adding popular products.")
        popular_products = purchases['product_id'].value_counts().head(5).index
        final_recs_df = products[products['product_id'].isin(popular_products) &
                                ~products['product_id'].isin(user_history)].copy()
        final_recs_df['score'] = 0.5
        final_recs_df['source'] = 'Popular Products'

    final_recs_df = final_recs_df.sort_values(by='score', ascending=False)
    logger.debug(f"Final weighted hybrid: {len(final_recs_df)} recs")

    return final_recs_df

def diversify_recommendations(recommendations, k=5):
    """
    Filter recommendations để tăng diversity theo category

    Ưu tiên: Category - Score - Diversity
    """
    if len(recommendations) == 0:
        return recommendations

    selected = []
    seen_categories = set()

    # Sắp xếp theo score
    sorted_recs = recommendations.sort_values(by='score', ascending=False)

    # Chọn từng category khác nhau
    for idx, row in sorted_recs.iterrows():
        category = row['category']

        # Nếu chưa chọn category này, thêm vào
        if category not in seen_categories:
            selected.append(row)
            seen_categories.add(category)
            if len(selected) == k:
                break

    # Nếu không đủ k sản phẩm, thêm từ category trùng (high score)
    if len(selected) < k:
        for idx, row in sorted_recs.iterrows():
            if len(selected) == k:
                break
            if row['product_id'] not in [s['product_id'] for s in selected]:
                selected.append(row)

    result_df = pd.DataFrame(selected)
    logger.debug(f"Diversified: {len(result_df)} items, {len(seen_categories)} categories")

    return result_df

class MultiModalModel(nn.Module):
    def __init__(self, num_users, num_products, embedding_dim=128):
        super().__init__()
        # Collaborative filtering components
        self.user_emb = nn.Embedding(num_users, embedding_dim)
        self.product_emb = nn.Embedding(num_products, embedding_dim)
        
        # Enhanced image feature extractor for fashion items
        self.image_encoder = resnet50(pretrained=True)
        self.image_encoder.fc = nn.Linear(2048, embedding_dim)
        
        # Fashion-specific feature layers
        self.view_embedding = nn.Embedding(4, embedding_dim)  # front, side, back, full
        self.style_projection = nn.Linear(embedding_dim, embedding_dim)
        
        # Freeze initial layers but fine-tune higher layers for fashion features
        for name, param in self.image_encoder.named_parameters():
            if 'layer4' in name or 'fc' in name:
                param.requires_grad = True
            else:
                param.requires_grad = False
        
        # Text feature extractor
        self.text_encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.text_proj = nn.Linear(384, embedding_dim)
        
        # GNN components
        self.conv1 = GCNConv(embedding_dim, embedding_dim)
        
        # Fusion layer
        self.fusion = nn.Linear(embedding_dim * 3, embedding_dim)

    def forward(self, user_ids, product_ids, text_batch, edge_index, product_images_df=None):
        # Collaborative features
        user_emb = self.user_emb(user_ids)
        product_emb = self.product_emb(product_ids)
        
        # Expand user embeddings to match product dimensions for element-wise multiplication
        if len(user_emb.shape) == 2 and len(product_emb.shape) == 2 and user_emb.shape[0] == 1:
            user_emb = user_emb.expand(product_emb.shape[0], -1)
        
        # Enhanced image features with fashion-specific processing
        if product_images_df is not None:
            # Fashion-optimized image transforms
            transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            # Map product_ids to their image paths and view types
            product_id_to_info = {}
            for _, row in product_images_df.iterrows():
                path = row['image_path']
                # Extract view type from filename (e.g., 1_front, 2_side, 3_back, 4_full)
                view_type = 0  # default to front view
                if '_1_front' in path:
                    view_type = 0
                elif '_2_side' in path:
                    view_type = 1
                elif '_3_back' in path:
                    view_type = 2
                elif '_4_full' in path:
                    view_type = 3
                product_id_to_info[row['product_id']] = {'path': path, 'view_type': view_type}
            
            # Process images with view information
            image_tensors = []
            view_types = []
            for pid in product_ids.cpu().numpy():
                if pid in product_id_to_info:
                    info = product_id_to_info[pid]
                    img_path = info['path']
                    if os.path.exists(img_path):
                        try:
                            img = Image.open(img_path).convert('RGB')
                            img_tensor = transform(img)
                            image_tensors.append(img_tensor)
                            view_types.append(info['view_type'])
                            logger.debug(f"Successfully loaded image for product {pid}: {img_path}")
                        except Exception as e:
                            logger.error(f"Error loading image for product {pid}: {e}")
                            image_tensors.append(torch.zeros(3, 224, 224))
                            view_types.append(0)
                    else:
                        logger.warning(f"Image path does not exist for product {pid}: {img_path}")
                        image_tensors.append(torch.zeros(3, 224, 224))
                        view_types.append(0)
                else:
                    logger.warning(f"No image mapping for product {pid}")
                    image_tensors.append(torch.zeros(3, 224, 224))
                    view_types.append(0)
            
            # Process image features with view embeddings
            image_batch = torch.stack(image_tensors).to(user_emb.device)
            view_batch = torch.tensor(view_types).to(user_emb.device)
            
            # Get base image features and enhance with view information
            base_image_emb = self.image_encoder(image_batch)
            view_emb = self.view_embedding(view_batch)
            
            # Combine image and view features
            image_emb = self.style_projection(base_image_emb + view_emb)
        else:
            # If no images provided, use zeros with proper dimensions
            image_emb = torch.zeros(product_emb.shape[0], product_emb.shape[1]).to(user_emb.device)
        
        # Text features
        if isinstance(text_batch, list) and len(text_batch) > 0:
            text_features = self.text_encoder.encode(text_batch, convert_to_tensor=True).to(user_emb.device)
            text_emb = self.text_proj(text_features)
        else:
            # If no text provided, use zeros with proper dimensions
            text_emb = torch.zeros(product_emb.shape[0], product_emb.shape[1]).to(user_emb.device)
        
        # Graph features (if edge_index is provided)
        if edge_index is not None:
            graph_emb = self.conv1(product_emb, edge_index)
        else:
            # If no graph structure provided, use product embeddings directly
            graph_emb = product_emb
        
        # Feature fusion - ensure all tensors have compatible dimensions
        cf_emb = user_emb * product_emb  # Collaborative filtering embeddings
        combined = torch.cat([cf_emb, image_emb, text_emb], dim=-1)
        return self.fusion(combined)