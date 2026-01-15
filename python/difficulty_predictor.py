"""
Difficulty Predictor for NYT Connections Categories

Predicts the difficulty level (Yellow/Green/Blue/Purple) of a word group.
"""

import numpy as np
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer

# Global model cache
_model = None


def _get_model():
    """Get or load the sentence transformer model (cached globally)"""
    global _model
    if _model is None:
        _model = SentenceTransformer('all-mpnet-base-v2')
    return _model


def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)


def has_wordplay_pattern(words: List[str]) -> bool:
    """
    Check if words have wordplay patterns (name combinations, compounds, etc.).
    
    Args:
        words: List of 4 words
        
    Returns:
        True if wordplay pattern detected
    """
    try:
        from python.wordplay_detector import analyze_all_wordplay
        findings = analyze_all_wordplay(words)
        
        # Check for name combinations
        if findings.get('name_combinations'):
            return True
        
        # Check for fill-in-blank patterns
        if findings.get('fill_in_blank', {}).get('suffixes') or findings.get('fill_in_blank', {}).get('prefixes'):
            return True
        
        # Check for compound patterns
        if findings.get('compounds'):
            return True
        
        return False
    except ImportError:
        return False


def predict_difficulty(
    group: List[str],
    embeddings: Optional[np.ndarray] = None,
    model: Optional[SentenceTransformer] = None
) -> str:
    """
    Predict the difficulty level of a word group.
    
    Args:
        group: List of 4 words in the group
        embeddings: Optional pre-computed embeddings (4x768 array)
        model: Optional model instance
        
    Returns:
        Difficulty level: "yellow", "green", "blue", or "purple"
    """
    if len(group) != 4:
        return "unknown"
    
    # Check for wordplay patterns first
    has_wordplay = has_wordplay_pattern(group)
    
    # Calculate average pairwise cosine similarity
    if embeddings is None:
        if model is None:
            model = _get_model()
        embeddings = model.encode(group, show_progress_bar=False)
        embeddings = np.array(embeddings)
    
    # Calculate all pairwise similarities
    similarities = []
    for i in range(4):
        for j in range(i + 1, 4):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            similarities.append(sim)
    
    avg_similarity = np.mean(similarities)
    min_similarity = np.min(similarities)
    
    # Predict difficulty based on similarity and wordplay
    if has_wordplay and avg_similarity < 0.4:
        return "purple"  # Hardest - wordplay with low semantic similarity
    elif has_wordplay and avg_similarity < 0.5:
        return "blue"  # Tricky - wordplay with moderate similarity
    elif avg_similarity > 0.7:
        return "yellow"  # Easiest - high semantic similarity
    elif avg_similarity > 0.5:
        return "green"  # Moderate - medium semantic similarity
    elif avg_similarity > 0.3:
        return "blue"  # Tricky - lower similarity
    else:
        return "purple"  # Hardest - very low similarity (likely wordplay)


def add_difficulty_to_predictions(
    predictions: List[Dict[str, Any]],
    words: List[str],
    model: Optional[SentenceTransformer] = None
) -> List[Dict[str, Any]]:
    """
    Add difficulty predictions to a list of predictions.
    
    Args:
        predictions: List of prediction dictionaries
        words: Full list of 16 words (for context)
        model: Optional model instance
        
    Returns:
        Predictions with added 'difficulty' field
    """
    if model is None:
        model = _get_model()
    
    # Generate embeddings for all words once
    all_embeddings = model.encode(words, show_progress_bar=False)
    all_embeddings = np.array(all_embeddings)
    
    # Create word to index mapping
    word_to_idx = {word.upper(): i for i, word in enumerate(words)}
    
    for pred in predictions:
        pred_words = pred['words']
        
        # Get embeddings for this group
        group_indices = [word_to_idx.get(w.upper()) for w in pred_words]
        if None in group_indices:
            pred['difficulty'] = 'unknown'
            continue
        
        group_embeddings = all_embeddings[group_indices]
        
        # Predict difficulty
        difficulty = predict_difficulty(pred_words, group_embeddings, model)
        pred['difficulty'] = difficulty
    
    return predictions


if __name__ == "__main__":
    # Test the difficulty predictor
    test_groups = [
        ["FAST", "QUICK", "RAPID", "SPEEDY"],  # Should be yellow
        ["SNOW", "ICE", "COLD", "FROST"],  # Should be green
        ["BASKET", "FOOT", "SNOW", "EYE"],  # Should be blue (fill-in-blank)
        ["JACKAL", "LEVITATE", "MELTED", "PATRON"],  # Should be purple (name combinations)
    ]
    
    print("Testing difficulty predictor...")
    model = _get_model()
    
    for group in test_groups:
        difficulty = predict_difficulty(group, model=model)
        print(f"{group} → {difficulty.upper()}")

