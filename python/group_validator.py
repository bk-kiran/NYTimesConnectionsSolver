"""
Universal Group Validator for NYT Connections Puzzles

Validates ANY potential group regardless of category type.
"""

from typing import List, Dict, Any, Set, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
from python.word_analyzer import analyze_word

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


def calculate_average_pairwise_similarity(embeddings: np.ndarray) -> float:
    """Calculate average pairwise cosine similarity."""
    similarities = []
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            similarities.append(sim)
    
    return np.mean(similarities) if similarities else 0.0


def calculate_min_pairwise_similarity(embeddings: np.ndarray) -> float:
    """Calculate minimum pairwise cosine similarity."""
    similarities = []
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            sim = cosine_similarity(embeddings[i], embeddings[j])
            similarities.append(sim)
    
    return np.min(similarities) if similarities else 0.0


def find_intersection(lists: List[List[str]]) -> List[str]:
    """Find intersection of multiple lists."""
    if not lists:
        return []
    
    result = set(lists[0])
    for lst in lists[1:]:
        result = result.intersection(set(lst))
    
    return list(result)


def validate_group(
    group_words: List[str],
    category: str,
    all_words: List[str],
    other_groups: Optional[List[List[str]]] = None
) -> Dict[str, Any]:
    """
    Universally validate if a group is likely correct.
    
    Args:
        group_words: List of 4 words in the group
        category: Category name for the group
        all_words: All 16 words in the puzzle
        other_groups: Other potential groups (for exclusivity check)
        
    Returns:
        Validation result with score, reasons, and validity
    """
    if len(group_words) != 4:
        return {
            'score': 0.0,
            'reasons': ['Group must have exactly 4 words'],
            'valid': False
        }
    
    score = 0.0
    reasons = []
    
    # 1. Check embedding similarity (works for semantic groups)
    # Skip embedding calculation if we already have validation scores to speed up
    if 'validation_score' not in group_words:  # Only calculate if not already done
        try:
            model = _get_model()
            embeddings = model.encode(group_words, show_progress_bar=False)
            embeddings = np.array(embeddings)
            
            avg_similarity = calculate_average_pairwise_similarity(embeddings)
            min_similarity = calculate_min_pairwise_similarity(embeddings)
            
            if avg_similarity > 0.6:
                score += 0.3
                reasons.append("High semantic similarity")
            elif avg_similarity < 0.3 and min_similarity < 0.2:
                # Low similarity might indicate wordplay
                reasons.append("Low similarity - possible wordplay")
                score += 0.1  # Don't penalize, might be wordplay
            elif avg_similarity > 0.4:
                score += 0.15
                reasons.append("Moderate semantic similarity")
        except Exception as e:
            reasons.append(f"Could not calculate embeddings: {e}")
    
    # 2. Check pattern consistency (works for any pattern)
    word_analyses = [analyze_word(w) for w in group_words]
    
    # Do all 4 words share a common category?
    all_categories = [set(a['categories']) for a in word_analyses]
    common_categories = find_intersection([list(cats) for cats in all_categories])
    if len(common_categories) > 0:
        score += 0.3
        reasons.append(f"Shared category: {common_categories[0]}")
    
    # Do all 4 words work with same fill-in-blank?
    all_before = [set(a['before_words']) for a in word_analyses]
    all_after = [set(a['after_words']) for a in word_analyses]
    
    common_before = find_intersection([list(b) for b in all_before])
    common_after = find_intersection([list(a) for a in all_after])
    
    if common_before:
        score += 0.4
        reasons.append(f"Fill-in-blank pattern (before): {common_before[0]}")
    if common_after:
        score += 0.4
        reasons.append(f"Fill-in-blank pattern (after): {common_after[0]}")
    
    # Do all 4 words have name splits?
    name_splits_count = sum(1 for a in word_analyses if len(a['name_splits']) > 0)
    if name_splits_count == 4:
        score += 0.4
        reasons.append("All words contain name combinations")
    elif name_splits_count >= 3:
        score += 0.2
        reasons.append("Most words contain name combinations")
    
    # Check for shared prefixes
    prefixes = [a['affixes'].get('prefix') for a in word_analyses if a['affixes'].get('prefix')]
    if len(set(prefixes)) == 1 and len(prefixes) == 4:
        score += 0.3
        reasons.append(f"Shared prefix: {prefixes[0]}")
    
    # Check for homophones
    homophones = [a['homophones'] for a in word_analyses if a['homophones']]
    if len(homophones) >= 3:
        score += 0.2
        reasons.append("Multiple homophones detected")
    
    # 3. Check exclusivity (these words shouldn't fit better elsewhere)
    if other_groups:
        for other_group in other_groups:
            if set(w.upper() for w in other_group).intersection(set(w.upper() for w in group_words)):
                # There's overlap - check if words fit better in other group
                # Simplified check: if other group has higher score, penalize
                score *= 0.95  # Slight penalty for potential overlap
                reasons.append("Potential overlap with other groups")
    
    # 4. Category name specificity check
    if category:
        category_lower = category.lower()
        if len(category.split()) <= 3:  # Concise
            score += 0.1
            reasons.append("Concise category name")
        
        vague_terms = ['related to', 'associated with', 'things that can', 'things that are']
        if any(vague in category_lower for vague in vague_terms):
            score *= 0.8  # Penalize vague categories
            reasons.append("Vague category name")
    
    # 5. Word length consistency (sometimes groups have similar lengths)
    lengths = [len(w) for w in group_words]
    if len(set(lengths)) == 1:  # All same length
        score += 0.05
        reasons.append("All words have same length")
    
    return {
        'score': min(1.0, score),
        'reasons': reasons,
        'valid': score > 0.4
    }


if __name__ == "__main__":
    # Test the validator
    test_group = ["JACKAL", "LEVITATE", "MELTED", "PATRON"]
    all_words = test_group + ["BASKET", "FOOT", "SNOW", "EYE", "FAST", "QUICK", "RAPID", "SPEEDY", "RED", "BLUE", "GREEN", "YELLOW"]
    
    result = validate_group(test_group, "WORDS WITH HIDDEN NAMES", all_words)
    print(f"Validation score: {result['score']:.2f}")
    print(f"Valid: {result['valid']}")
    print(f"Reasons: {result['reasons']}")

