import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from scipy.stats import rankdata

def compute_unified_scores(forgetting_counts: np.ndarray, avg_loss: np.ndarray, 
                           aum_scores: np.ndarray, tracin_scores: np.ndarray, 
                           rarity_scores: np.ndarray, weights: Optional[List[float]] = None) -> Tuple[np.ndarray, List[str]]:
    """Computes unified sample valuation scores and categorizes them."""
    if weights is None:
        weights = [0.20, 0.15, 0.25, 0.20, 0.20]
        
    N = len(forgetting_counts)
    
    pct_forgetting = rankdata(forgetting_counts) / N
    pct_loss = rankdata(avg_loss) / N
    pct_neg_aum = rankdata(-aum_scores) / N
    pct_tracin = rankdata(tracin_scores) / N
    pct_rarity = rankdata(rarity_scores) / N
    
    scores = (weights[0] * pct_forgetting + 
              weights[1] * pct_loss + 
              weights[2] * pct_neg_aum + 
              weights[3] * pct_tracin + 
              weights[4] * pct_rarity)
              
    categories = []
    for i in range(N):
        score = scores[i]
        aum = aum_scores[i]
        rarity = pct_rarity[i]
        loss = pct_loss[i]
        forgetting = forgetting_counts[i]
        tracin = tracin_scores[i]
        
        if tracin < 0 or pct_neg_aum[i] > 0.95:
            categories.append('harmful')
        elif loss > 0.95 and forgetting > 0 and aum < 0:
            categories.append('suspicious')
        elif forgetting == 0 and rarity < 0.20 and loss < 0.20:
            categories.append('redundant')
        elif score > 0.80 and aum > 0 and rarity > 0.80:
            categories.append('high_value')
        else:
            categories.append('normal')
            
    return scores, categories

def generate_health_report(categories: List[str], scores: np.ndarray, **kwargs) -> Dict[str, Any]:
    """Generates a summary health report."""
    from collections import Counter
    counts = Counter(categories)
    N = len(categories)
    
    removal_candidates = counts.get('harmful', 0) + counts.get('redundant', 0)
    
    suspicious_indices = [i for i, c in enumerate(categories) if c == 'suspicious']
    suspicious_scores = scores[suspicious_indices]
    
    top_suspicious = []
    if len(suspicious_indices) > 0:
        sorted_sus = np.argsort(-suspicious_scores)
        top_suspicious = [suspicious_indices[idx] for idx in sorted_sus[:10]]
        
    return {
        "total_samples": N,
        "category_counts": dict(counts),
        "recommended_removal_percentage": (removal_candidates / N) * 100 if N > 0 else 0,
        "top_suspicious_samples": top_suspicious
    }
