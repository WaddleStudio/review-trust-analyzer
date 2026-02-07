from sentence_transformers import SentenceTransformer, util
import torch

# Load a multilingual model
# paraphrase-multilingual-MiniLM-L12-v2 supports 50+ languages including Chinese
try:
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
except Exception as e:
    print(f"Error loading model: {e}")
    model = None

# Seed sentences representing suspicious promotional behavior (English + Chinese)
PROMO_SEEDS = [
    # English
    "Write a 5-star review to get a free gift.",
    "Show this review at the counter for a discount.",
    "We offer a rebate if you leave a positive rating.",
    "Receive a complimentary item for your feedback.",
    "Get a coupon code by posting a good review.",
    "Free dessert for 5 star reviews.",
    "Promotion valid only for positive feedback.",
    "Give us 5 stars and get a reward.",
    
    # Chinese (Traditional & Simplified)
    "寫五星好評送小菜",
    "出示此評論可享九折優惠",
    "打卡送飲料",
    "好評截圖給客服領紅包",
    "給滿分評價就送禮物",
    "參加活動請留五星",
    "評論送折價券",
    "好評返現"
]

# Seed sentences representing GENUINE reviews (Safe Anchors)
# Used to reduce false positives by checking if text is closer to these than promo seeds
SAFE_SEEDS = [
    # English
    "The food was delicious and service was great.",
    "I really enjoyed my stay here.",
    "Highly recommended because of the quality.",
    "Gave 5 stars because the staff was so friendly.",
    "Best experience I've ever had.",
    
    # Chinese
    "東西很好吃所以給五星",
    "服務親切，餐點美味，值得五顆星",
    "真心推薦這家店",
    "因為很好吃特地來留言",
    "環境舒適，會再來光顧",
    "好吃給店家五星好評", # Explicitly add the user's false positive case as a safe anchor
    "CP值很高",
    "雖然貴了點但很值得",
    
    # Anti-Promo Safe Seeds (Mentioning promo to deny it)
    "沒送贈品也值得五星",
    "就算沒有優惠也推薦",
    "原價吃也划算",
    "不是為了贈品才寫的",
    "Even without a discount, I would come back.",
    "Worth full price.",
    "No freebies needed, it's just good."
]

# Pre-compute embeddings
if model:
    PROMO_EMBEDDINGS = model.encode(PROMO_SEEDS, convert_to_tensor=True)
    SAFE_EMBEDDINGS = model.encode(SAFE_SEEDS, convert_to_tensor=True)
else:
    PROMO_EMBEDDINGS = None
    SAFE_EMBEDDINGS = None

def calculate_semantic_promo_score(text: str) -> float:
    """
    Calculates the semantic promo score using contrastive analysis.
    If text is closer to SAFE_SEEDS than PROMO_SEEDS, score is reduced.
    """
    if not text or not model or PROMO_EMBEDDINGS is None:
        return 0.0
        
    # Skip very short texts to avoid false positives
    if len(text) < 5:
        return 0.0
    
    try:
        # Encode the input text
        text_embedding = model.encode(text, convert_to_tensor=True)
        
        # Compute cosine similarities
        promo_scores = util.cos_sim(text_embedding, PROMO_EMBEDDINGS)
        safe_scores = util.cos_sim(text_embedding, SAFE_EMBEDDINGS)
        
        # Get max scores
        max_promo = torch.max(promo_scores).item()
        max_safe = torch.max(safe_scores).item()
        
        # Contrastive Logic:
        # If it looks more like a safe review than a promo review, suppress the score.
        if max_safe > max_promo:
            return 0.0
            
        # If it's somewhat safe, dampen the promo score
        # e.g. promo=0.76, safe=0.70 -> result might be low
        # But if promo=0.8, safe=0.2 -> result stays high
        
        # Simple heuristic: Only return score if promo dominates
        return max_promo
        
    except Exception as e:
        print(f"Error in semantic analysis: {e}")
        return 0.0
