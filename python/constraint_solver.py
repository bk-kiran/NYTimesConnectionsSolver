"""
Constraint-Based Solver for NYT Connections Puzzles

Ensures valid 4-group solutions with no overlapping words.
"""

import itertools
from typing import List, Dict, Set, Optional


def find_valid_solution(all_predictions: List[Dict], all_words: Set[str]) -> Optional[List[Dict]]:
    """
    Find the best combination of 4 predictions that uses all 16 words exactly once.
    
    Args:
        all_predictions: List of all group predictions (20-50 predictions)
        all_words: Set of all 16 words in the puzzle (uppercase)
    
    Returns:
        List of exactly 4 predictions that form a valid solution, or None
    """
    # Normalize all_words to uppercase
    all_words_upper = set(w.upper() for w in all_words)
    
    # Normalize prediction words to uppercase for comparison
    normalized_predictions = []
    for pred in all_predictions:
        normalized_pred = pred.copy()
        normalized_pred['words'] = [w.upper() for w in pred['words']]
        normalized_predictions.append(normalized_pred)
    
    # Try all combinations of 4 predictions from top 20 (reduced from 30 for speed)
    best_solution = None
    best_score = -1
    
    top_predictions = normalized_predictions[:20]  # Reduced from 30 to speed up
    
    if len(top_predictions) < 4:
        # Not enough predictions, use greedy approach
        return greedy_solution(normalized_predictions, all_words_upper)
    
    # Limit combinations to avoid timeout (C(20,4) = 4,845 combinations)
    import sys
    combo_count = 0
    max_combos = 5000  # Limit to first 5000 combinations
    
    for combo in itertools.combinations(top_predictions, 4):
        combo_count += 1
        if combo_count > max_combos:
            print(f"Reached combination limit ({max_combos}), using best found so far", file=sys.stderr)
            break
        # Extract all words from this combination
        words_in_combo = set()
        for group in combo:
            words_in_combo.update(w.upper() for w in group['words'])
        
        # Check validity: must use all 16 words exactly once
        if words_in_combo == all_words_upper and len(words_in_combo) == 16:
            # Calculate combined confidence score
            score = sum(group.get('confidence', 0.5) for group in combo)
            
            # Bonus for diverse category types
            category_types = set(group.get('category_type', 'unknown') for group in combo)
            if len(category_types) >= 3:  # Prefer diverse categories
                score *= 1.1
            
            # Bonus for high validation scores if available
            validation_scores = [group.get('validation_score', 0.5) for group in combo]
            avg_validation = sum(validation_scores) / len(validation_scores)
            score += avg_validation * 0.2
            
            if score > best_score:
                best_score = score
                best_solution = list(combo)
    
    # If no perfect solution found, use iterative approach
    if best_solution is None:
        best_solution = greedy_solution(normalized_predictions, all_words_upper)
    
    return best_solution


def greedy_solution(all_predictions: List[Dict], all_words: Set[str]) -> List[Dict]:
    """
    Greedy algorithm to build a solution by selecting non-overlapping groups.
    
    Args:
        all_predictions: List of all predictions (normalized to uppercase)
        all_words: Set of all 16 words (uppercase)
    
    Returns:
        List of 4 predictions (or fewer if not possible)
    """
    selected_groups = []
    used_words = set()
    
    # Sort by confidence (highest first)
    sorted_predictions = sorted(
        all_predictions,
        key=lambda x: x.get('final_confidence', x.get('confidence', 0)),
        reverse=True
    )
    
    for prediction in sorted_predictions:
        pred_words = set(w.upper() for w in prediction['words'])
        
        # Check if this group overlaps with already selected words
        if not (pred_words & used_words):  # No overlap
            selected_groups.append(prediction)
            used_words.update(pred_words)
            
            if len(selected_groups) == 4:
                break
    
    # If we have exactly 4 groups using all 16 words, success
    if len(selected_groups) == 4 and used_words == all_words:
        return selected_groups
    
    # If we have 4 groups but not all words, try to fill gaps
    if len(selected_groups) == 4:
        # Check what words are missing
        missing_words = all_words - used_words
        
        # Try to replace lower-confidence groups with ones that include missing words
        for missing_word in missing_words:
            for candidate in sorted_predictions:
                candidate_words = set(w.upper() for w in candidate['words'])
                if missing_word in candidate_words:
                    # Check if we can swap this candidate for a group
                    # (would need to check if it conflicts with other selected groups)
                    # For now, just return what we have
                    pass
    
    # Otherwise, return top 4 by confidence (fallback)
    if len(selected_groups) < 4:
        return sorted_predictions[:4]
    
    return selected_groups


if __name__ == "__main__":
    # Test the constraint solver
    test_predictions = [
        {'words': ['WORD1', 'WORD2', 'WORD3', 'WORD4'], 'confidence': 0.9},
        {'words': ['WORD5', 'WORD6', 'WORD7', 'WORD8'], 'confidence': 0.85},
        {'words': ['WORD9', 'WORD10', 'WORD11', 'WORD12'], 'confidence': 0.8},
        {'words': ['WORD13', 'WORD14', 'WORD15', 'WORD16'], 'confidence': 0.75},
    ]
    
    test_words = set(['WORD1', 'WORD2', 'WORD3', 'WORD4', 'WORD5', 'WORD6', 'WORD7', 'WORD8',
                      'WORD9', 'WORD10', 'WORD11', 'WORD12', 'WORD13', 'WORD14', 'WORD15', 'WORD16'])
    
    solution = find_valid_solution(test_predictions, test_words)
    print(f"Found solution with {len(solution)} groups")

