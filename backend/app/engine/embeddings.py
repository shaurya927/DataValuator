import torch
import numpy as np
from typing import Tuple, List

try:
    import faiss
    HAS_FAISS = True
except ImportError:
    HAS_FAISS = False

try:
    import umap
    HAS_UMAP = True
except ImportError:
    HAS_UMAP = False

def extract_embeddings(model: torch.nn.Module, dataloader: torch.utils.data.DataLoader, device: torch.device) -> Tuple[np.ndarray, np.ndarray]:
    """Extracts embeddings from the penultimate layer."""
    model.eval()
    embeddings = []
    all_indices = []
    
    layer_name = getattr(model, 'feature_layer_name', None)
    if layer_name is None:
        raise ValueError("Model does not have a feature_layer_name attribute.")
        
    target_layer = dict([*model.named_modules()]).get(layer_name)
    if target_layer is None:
        raise ValueError(f"Layer {layer_name} not found in model.")

    features = []
    def hook(module, input, output):
        features.append(output.detach())
        
    handle = target_layer.register_forward_hook(hook)

    with torch.no_grad():
        for indices, data, _ in dataloader:
            data = data.to(device)
            features.clear()
            model(data)
            
            feat = features[0].view(features[0].size(0), -1)
            embeddings.append(feat.cpu().numpy())
            all_indices.append(indices.numpy())
            
    handle.remove()
    
    embeddings = np.concatenate(embeddings, axis=0)
    all_indices = np.concatenate(all_indices, axis=0)
    
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    embeddings = embeddings / (norms + 1e-8)
    
    sort_idx = np.argsort(all_indices)
    
    return embeddings[sort_idx], all_indices[sort_idx]

def compute_rarity_scores(embeddings: np.ndarray, k: int = 10) -> np.ndarray:
    """Computes rarity scores based on k-NN similarity."""
    if not HAS_FAISS:
        raise ImportError("faiss is required for compute_rarity_scores")
        
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    
    distances, _ = index.search(embeddings, k + 1)
    mean_knn_similarity = distances[:, 1:].mean(axis=1)
    rarity = 1.0 - mean_knn_similarity
    return rarity

def find_redundant_pairs(embeddings: np.ndarray, threshold: float = 0.95) -> List[Tuple[int, int, float]]:
    """Finds pairs of highly similar samples."""
    if not HAS_FAISS:
        raise ImportError("faiss is required for find_redundant_pairs")
        
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    
    k = min(50, len(embeddings))
    distances, indices = index.search(embeddings, k)
    
    redundant_pairs = []
    for i in range(len(embeddings)):
        for j, dist in zip(indices[i], distances[i]):
            if i < j and dist > threshold:
                redundant_pairs.append((i, int(j), float(dist)))
                
    return redundant_pairs

def compute_umap_projection(embeddings: np.ndarray, n_components: int = 2) -> np.ndarray:
    """Computes UMAP projection of embeddings."""
    if not HAS_UMAP:
        raise ImportError("umap-learn is required for compute_umap_projection")
        
    reducer = umap.UMAP(n_components=n_components)
    projection = reducer.fit_transform(embeddings)
    return projection
