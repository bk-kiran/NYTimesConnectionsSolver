"""
Word Conflict Resolver for NYT Connections Puzzles

Fixes word assignment issues in groups to ensure valid solutions.
"""

from typing import List, Dict, Set
import numpy as np
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


def get_embedding(word: str):
    """Get embedding for a word."""
    model = _get_model()
    return model.encode([word], show_progress_bar=False)[0]


def has_wordplay_pattern(word: str) -> bool:
    """Check if word has wordplay patterns."""
    try:
        from python.wordplay_detector import detect_name_combinations
        return len(detect_name_combinations(word)) > 0
    except:
        return False


def fits_blank_pattern(word: str, group: Dict) -> bool:
    """Check if word fits the group's fill-in-blank pattern."""
    category = group.get('category', '').lower()
    
    # Simple heuristic: check if category mentions a pattern
    if 'before' in category or 'after' in category:
        # Would need more sophisticated checking
        return True
    
    return False


def calculate_word_fit_score(word: str, group: Dict) -> float:
    """
    Calculate how well a word fits a group's category.
    
    Args:
        word: Word to check
        group: Group dictionary with 'words' and 'category'
    
    Returns:
        Fit score between 0.0 and 1.0
    """
    score = 0.0
    
    # Check semantic similarity with other words in group
    other_words = [w for w in group['words'] if w.upper() != word.upper()]
    if other_words:
        try:
            word_embedding = get_embedding(word)
            group_embeddings = [get_embedding(w) for w in other_words]
            similarities = [cosine_similarity(word_embedding, ge) for ge in group_embeddings]
            score += np.mean(similarities) * 0.7
        except Exception:
            pass
    
    # Check if word matches group's category pattern
    category = group.get('category', '').lower()
    category_type = group.get('category_type', '')
    
    if category_type == 'wordplay' and has_wordplay_pattern(word):
        score += 0.3
    elif category_type == 'fill_in_blank' and fits_blank_pattern(word, group):
        score += 0.3
    
    # Check if word is in the same category (simple keyword matching)
    word_lower = word.lower()
    if word_lower in category or any(word_lower in w.lower() for w in other_words):
        score += 0.1
    
    return min(1.0, score)


def resolve_word_conflicts(top_4_groups: List[Dict], all_words: Set[str]) -> List[Dict]:
    """
    Fix word assignment issues in the top 4 groups.
    Ensures each word goes to its best-fit group.
    
    Args:
        top_4_groups: List of 4 group dictionaries
        all_words: Set of all 16 words (uppercase)
    
    Returns:
        Fixed list of 4 groups
    """
    import sys
    
    # Normalize all_words to uppercase
    all_words_upper = set(w.upper() for w in all_words)
    
    # Make a copy to avoid modifying original
    groups = []
    for group in top_4_groups:
        groups.append({
            'words': [w.upper() for w in group['words']],
            'category': group.get('category', ''),
            'category_type': group.get('category_type', ''),
            'confidence': group.get('confidence', 0.5),
            'validation_score': group.get('validation_score', 0.5),
        })
    
    # Step 1: Find all word conflicts (words in multiple groups or missing)
    word_assignments = {}  # word → list of group indices
    for i, group in enumerate(groups):
        for word in group['words']:
            if word not in word_assignments:
                word_assignments[word] = []
            word_assignments[word].append(i)
    
    # Find duplicated and missing words
    duplicated_words = {w: groups for w, groups in word_assignments.items() if len(groups) > 1}
    assigned_words = set(word_assignments.keys())
    missing_words = all_words_upper - assigned_words
    
    print(f"Word conflicts: {len(duplicated_words)} duplicates, {len(missing_words)} missing", file=sys.stderr)
    
    # Step 2: Resolve duplicates - keep word in best-fit group
    for word, group_indices in duplicated_words.items():
        # Calculate fit score for each group
        best_group_idx = None
        best_score = -1
        
        for idx in group_indices:
            group = groups[idx]
            # Score based on: semantic similarity + category match
            score = calculate_word_fit_score(word, group)
            
            if score > best_score:
                best_score = score
                best_group_idx = idx
        
        # Remove word from all groups except best fit
        for idx in group_indices:
            if idx != best_group_idx:
                groups[idx]['words'] = [w for w in groups[idx]['words'] if w != word]
                print(f"Moved '{word}' from group {idx+1} to group {best_group_idx+1} (score: {best_score:.2f})", file=sys.stderr)
    
    # Step 3: Assign missing words to groups that need them
    for word in missing_words:
        # Find which group needs more words (has < 4)
        best_group_idx = None
        best_score = -1
        
        for idx, group in enumerate(groups):
            if len(group['words']) < 4:
                # Check if word fits this group's category
                fit_score = calculate_word_fit_score(word, group)
                if fit_score > best_score:
                    best_score = fit_score
                    best_group_idx = idx
        
        if best_group_idx is not None and best_score > 0.3:  # Threshold for fit
            groups[best_group_idx]['words'].append(word)
            print(f"Assigned missing word '{word}' to group {best_group_idx+1} (score: {best_score:.2f})", file=sys.stderr)
    
    # Step 4: Final validation and repair
    # Check if any group has wrong number of words
    for i, group in enumerate(groups):
        if len(group['words']) != 4:
            print(f"Warning: Group {i+1} has {len(group['words'])} words (should be 4)", file=sys.stderr)
            # Try to rebalance
            current_words = set(group['words'])
            needed = 4 - len(current_words)
            
            if needed > 0:
                # Try to find words that fit this group
                available_words = all_words_upper - set(w for g in groups for w in g['words'])
                for word in available_words:
                    if needed <= 0:
                        break
                    fit_score = calculate_word_fit_score(word, group)
                    if fit_score > 0.3:
                        group['words'].append(word)
                        needed -= 1
    
    return groups


if __name__ == "__main__":
    # Test the conflict resolver
    test_groups = [
        {'words': ['WORD1', 'WORD2', 'WORD3', 'WORD4'], 'category': 'Test Category 1'},
        {'words': ['WORD5', 'WORD6', 'WORD7', 'WORD8'], 'category': 'Test Category 2'},
        {'words': ['WORD9', 'WORD10', 'WORD11', 'WORD12'], 'category': 'Test Category 3'},
        {'words': ['WORD13', 'WORD14', 'WORD15', 'WORD16'], 'category': 'Test Category 4'},
    ]
    
    test_words = set(['WORD1', 'WORD2', 'WORD3', 'WORD4', 'WORD5', 'WORD6', 'WORD7', 'WORD8',
                      'WORD9', 'WORD10', 'WORD11', 'WORD12', 'WORD13', 'WORD14', 'WORD15', 'WORD16'])
    
    resolved = resolve_word_conflicts(test_groups, test_words)
    print(f"Resolved to {len(resolved)} groups")

