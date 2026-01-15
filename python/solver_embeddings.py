"""
NYT Connections Solver using Semantic Embeddings

Uses sentence-transformers to find word groups based on semantic similarity.
"""

import numpy as np
from itertools import combinations
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import warnings
import sys

# Suppress warnings
warnings.filterwarnings('ignore')

# Global model cache to avoid reloading
_model = None


def _get_model():
    """Get or load the sentence transformer model (cached globally)"""
    global _model
    if _model is None:
        print("Loading sentence-transformers model 'all-mpnet-base-v2'...", file=sys.stderr)
        _model = SentenceTransformer('all-mpnet-base-v2')
        print("Model loaded successfully!", file=sys.stderr)
    return _model


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score (0-1)
    """
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def solve_with_embeddings(words: List[str]) -> List[Dict[str, Any]]:
    """
    Solve NYT Connections puzzle using semantic embeddings.
    
    Args:
        words: List of 16 puzzle words
        
    Returns:
        List of top 20 predictions, each with:
        - words: List of 4 words
        - confidence: Similarity score (0-1)
        - method: "embeddings"
    """
    if len(words) != 16:
        raise ValueError(f"Expected 16 words, got {len(words)}")
    
    # Get the model
    model = _get_model()
    
    # Generate embeddings for all words (vectorized operation)
    import sys
    print(f"Generating embeddings for {len(words)} words...", file=sys.stderr)
    embeddings = model.encode(words, show_progress_bar=False)
    embeddings = np.array(embeddings)
    
    # Get all possible 4-word combinations
    print("Calculating similarity scores for all 4-word combinations...", file=sys.stderr)
    all_combinations = list(combinations(range(len(words)), 4))
    print(f"Total combinations to evaluate: {len(all_combinations)}", file=sys.stderr)
    
    results = []
    
    # Process combinations in batches for efficiency
    batch_size = 1000
    for i in range(0, len(all_combinations), batch_size):
        batch = all_combinations[i:i + batch_size]
        
        for combo_indices in batch:
            # Get embeddings for this 4-word combination
            combo_embeddings = embeddings[list(combo_indices)]
            
            # Calculate all pairwise cosine similarities
            # Use vectorized operations for speed
            pairwise_similarities = []
            
            # Get all pairs within this combination (6 pairs for 4 words)
            pairs = list(combinations(range(4), 2))
            
            for pair in pairs:
                idx1, idx2 = pair
                similarity = cosine_similarity(
                    combo_embeddings[idx1],
                    combo_embeddings[idx2]
                )
                pairwise_similarities.append(similarity)
            
            # Calculate average pairwise similarity (confidence score)
            # Also consider minimum similarity to ensure all pairs are reasonably similar
            avg_similarity = np.mean(pairwise_similarities)
            min_similarity = np.min(pairwise_similarities)
            
            # Combined confidence: weighted average with minimum threshold
            # This penalizes groups where one pair is very dissimilar
            confidence = (avg_similarity * 0.7) + (min_similarity * 0.3)
            
            # Additional penalty if minimum similarity is too low
            if min_similarity < 0.3:
                confidence *= 0.7  # Reduce confidence for weak connections
            
            # Get the actual words for this combination
            combo_words = [words[idx] for idx in combo_indices]
            
            results.append({
                "words": combo_words,
                "confidence": float(confidence),
                "method": "embeddings"
            })
        
        # Progress update
        if (i + batch_size) % 5000 == 0:
            import sys
            print(f"Processed {min(i + batch_size, len(all_combinations))} combinations...", file=sys.stderr)
    
    # Sort by confidence (highest first)
    results.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Find non-overlapping groups to ensure better coverage
    def find_non_overlapping_groups(all_combinations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find top non-overlapping groups."""
        selected_groups = []
        used_words = set()
        
        for combo in all_combinations:  # Already sorted by confidence
            words_in_combo = set(w.upper() for w in combo['words'])
            
            # Check if this group overlaps with already selected
            if not words_in_combo.intersection(used_words):
                selected_groups.append(combo)
                used_words.update(words_in_combo)
                
            if len(selected_groups) >= 30:  # Get up to 30 non-overlapping
                break
        
        return selected_groups
    
    # Get non-overlapping groups first
    non_overlapping = find_non_overlapping_groups(results)
    
    # Also include top by confidence (even if overlapping) for more options
    top_by_confidence = results[:30]
    
    # Merge and deduplicate
    seen = set()
    final_results = []
    
    # Add non-overlapping first (higher priority)
    for pred in non_overlapping:
        normalized = tuple(sorted(w.upper() for w in pred['words']))
        if normalized not in seen:
            seen.add(normalized)
            final_results.append(pred)
    
    # Add top by confidence if not already included
    for pred in top_by_confidence:
        normalized = tuple(sorted(w.upper() for w in pred['words']))
        if normalized not in seen and len(final_results) < 30:
            seen.add(normalized)
            final_results.append(pred)
    
    print(f"Top prediction confidence: {final_results[0]['confidence']:.4f}", file=sys.stderr)
    print(f"Returning {len(final_results)} predictions ({len(non_overlapping)} non-overlapping)", file=sys.stderr)
    
    return final_results


if __name__ == "__main__":
    """Test the solver"""
    # Test with sample words from a puzzle
    test_words = [
        "FAST", "FIRM", "SECURE", "TIGHT",
        "ACCOUNT", "CLIENT", "CONSUMER", "USER",
        "FROSTY", "MISTLETOE", "RAINMAKER", "SNOWMAN",
        "AUCTION", "MOVIE", "PARTNER", "TREATMENT"
    ]
    
    print("Testing solver with sample words...")
    print(f"Words: {test_words}\n")
    
    try:
        results = solve_with_embeddings(test_words)
        
        print(f"\n=== Top 5 Predictions ===")
        for i, result in enumerate(results[:5], 1):
            print(f"\n{i}. Confidence: {result['confidence']:.4f}")
            print(f"   Words: {result['words']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

