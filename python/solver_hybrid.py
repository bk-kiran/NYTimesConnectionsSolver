"""
NYT Connections Hybrid Solver

Combines embeddings-based and LLM-based solving methods for better accuracy.
"""

import time
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

# Add parent directory to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from python.solver_embeddings import solve_with_embeddings
from python.solver_llm import solve_with_llm
from python.wordplay_detector import analyze_all_wordplay
from python.difficulty_predictor import add_difficulty_to_predictions


def _normalize_group(words: List[str]) -> tuple:
    """
    Normalize a group of words for comparison (sorted tuple).
    
    Args:
        words: List of words
        
    Returns:
        Sorted tuple of words (case-insensitive)
    """
    return tuple(sorted(word.upper() for word in words))


def _groups_match(group1: List[str], group2: List[str]) -> bool:
    """
    Check if two groups contain the same words (order-independent).
    
    Args:
        group1: First group of words
        group2: Second group of words
        
    Returns:
        True if groups match
    """
    return _normalize_group(group1) == _normalize_group(group2)


def _has_word_overlap(group1: List[str], group2: List[str]) -> bool:
    """
    Check if two groups share any words.
    
    Args:
        group1: First group of words
        group2: Second group of words
        
    Returns:
        True if groups share any words
    """
    set1 = set(word.upper() for word in group1)
    set2 = set(word.upper() for word in group2)
    return len(set1.intersection(set2)) > 0


def find_best_solution(predictions: List[Dict[str, Any]], all_words: List[str]) -> Optional[List[Dict[str, Any]]]:
    """
    Find optimal 4-group combination that uses all 16 words exactly once.
    
    Args:
        predictions: List of all predictions (sorted by confidence)
        all_words: List of all 16 words
        
    Returns:
        List of 4 predictions that cover all words, or None if not found
    """
    import itertools
    
    all_words_set = set(word.upper() for word in all_words)
    
    # Try combinations of 4 predictions from top candidates
    # Limit to top 20 to balance coverage vs computation time
    # (C(20,4) = 4,845 combinations - manageable)
    top_predictions = predictions[:20]
    
    if len(top_predictions) < 4:
        return None
    
    best_solution = None
    best_score = -1
    
    # Try all combinations of 4 groups
    for combo in itertools.combinations(top_predictions, 4):
        used_words = set()
        valid = True
        
        # Check each group in this combination
        for pred in combo:
            pred_words = set(word.upper() for word in pred['words'])
            
            # Check for overlaps between groups
            if pred_words.intersection(used_words):
                valid = False
                break
            
            used_words.update(pred_words)
        
        # Check if all 16 words are covered exactly
        if valid and used_words == all_words_set:
            # Calculate score (sum of confidences)
            score = sum(g['confidence'] for g in combo)
            
            if score > best_score:
                best_score = score
                best_solution = list(combo)
    
    if best_solution:
        print(f"Found best solution with score {best_score:.3f}: 4 groups covering all 16 words!", file=sys.stderr)
    
    return best_solution


def _find_complete_solution(predictions: List[Dict[str, Any]], all_words: List[str]) -> Optional[List[Dict[str, Any]]]:
    """
    Alias for find_best_solution (backward compatibility).
    """
    return find_best_solution(predictions, all_words)


def solve_puzzle(
    words: List[str],
    use_llm: bool = False,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Solve NYT Connections puzzle using hybrid approach.
    
    Args:
        words: List of 16 puzzle words
        use_llm: Whether to use LLM solver (default: False)
        api_key: OpenAI API key (required if use_llm=True)
        
    Returns:
        Dictionary with:
        - predictions: List of top 10 unique predictions
        - solve_time_ms: Time taken in milliseconds
        - methods_used: List of methods used
    """
    start_time = time.time()
    methods_used = ["embeddings"]
    
    # Validate input
    if len(words) != 16:
        raise ValueError(f"Expected 16 words, got {len(words)}")
    
    if use_llm and not api_key:
        raise ValueError("API key required when use_llm=True")
    
    import sys
    print("Starting hybrid solver...", file=sys.stderr)
    
    # Step 0: Run wordplay analysis
    print("\n[0/3] Analyzing wordplay patterns...", file=sys.stderr)
    wordplay_findings = analyze_all_wordplay(words)
    print(f"Wordplay analysis complete", file=sys.stderr)
    
    # Step 1: Always run embeddings solver (fast)
    print("\n[1/3] Running embeddings solver...", file=sys.stderr)
    embeddings_results = solve_with_embeddings(words)
    print(f"Embeddings solver found {len(embeddings_results)} predictions", file=sys.stderr)
    
    # Step 2: Conditionally run LLM solver
    llm_results = []
    if use_llm:
        print("\n[2/3] Running LLM solver...", file=sys.stderr)
        print(f"use_llm={use_llm}, api_key present={bool(api_key)}", file=sys.stderr)
        try:
            if not api_key:
                raise ValueError("API key is required for LLM solver but was not provided")
            llm_results = solve_with_llm(words, api_key, wordplay_findings=wordplay_findings)
            print(f"LLM solver found {len(llm_results)} predictions", file=sys.stderr)
            methods_used.append("llm")
        except Exception as e:
            print(f"ERROR: LLM solver failed: {str(e)}", file=sys.stderr)
            print("Continuing with embeddings-only results...", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
    else:
        print("\n[2/3] Skipping LLM solver (use_llm=False)", file=sys.stderr)
    
    # Merge and rank predictions
    import sys
    print("\nMerging and ranking predictions...", file=sys.stderr)
    
    # Create a dictionary to track merged predictions
    merged_predictions: Dict[tuple, Dict[str, Any]] = {}
    
    # Helper function to check if prediction matches wordplay pattern
    def matches_wordplay(pred_words: List[str], findings: Dict[str, Any]) -> bool:
        """Check if prediction matches any wordplay pattern"""
        pred_set = set(w.upper() for w in pred_words)
        
        # Check name combinations
        name_words = set(findings.get('name_combinations', {}).keys())
        if len(pred_set.intersection(name_words)) >= 3:
            return True
        
        # Check fill-in-blank patterns
        for suffix, words_list in findings.get('fill_in_blank', {}).get('suffixes', {}).items():
            if len(pred_set.intersection(set(words_list))) >= 3:
                return True
        
        # Check compound patterns
        for compound in findings.get('compounds', []):
            if len(pred_set.intersection(set(compound.get('words', [])))) >= 3:
                return True
        
        return False
    
    # Process embeddings results with calibrated confidence
    min_embeddings_confidence = 0.4
    for result in embeddings_results:
        raw_confidence = result['confidence']
        
        # Calibrate embeddings confidence: map 0.4→0% and 0.8→100%
        if raw_confidence < 0.4:
            continue  # Skip very low confidence
        calibrated_confidence = min(1.0, (raw_confidence - 0.4) / 0.4)
        
        normalized = _normalize_group(result['words'])
        if normalized not in merged_predictions:
            # Check for wordplay match
            wordplay_boost = 0.0
            if matches_wordplay(result['words'], wordplay_findings):
                wordplay_boost = 0.1
            
            merged_predictions[normalized] = {
                "words": result['words'],
                "confidence": (calibrated_confidence * 0.4) + wordplay_boost,  # Weight embeddings + wordplay
                "method": "embeddings",
                "category": None,
                "explanation": None,
                "sources": ["embeddings"]
            }
        else:
            # Already exists, keep higher confidence
            existing = merged_predictions[normalized]
            wordplay_boost = 0.1 if matches_wordplay(result['words'], wordplay_findings) else 0.0
            existing['confidence'] = max(existing['confidence'], (calibrated_confidence * 0.4) + wordplay_boost)
    
    # Process LLM results (weight 0.6, boost if also in embeddings)
    for result in llm_results:
        normalized = _normalize_group(result['words'])
        
        # Only include LLM predictions with confidence > 0.6
        if result.get('confidence', 0) < 0.6:
            continue  # Skip low-confidence LLM predictions
        
        # Check for wordplay match
        wordplay_boost = 0.0
        if matches_wordplay(result['words'], wordplay_findings):
            wordplay_boost = 0.15  # Strong boost for wordplay matches
        
        if normalized in merged_predictions:
            # Found in both solvers - boost confidence significantly
            base_confidence = merged_predictions[normalized]['confidence']
            llm_confidence = result.get('confidence', 0.8)
            
            # Boost more if both have high confidence
            if base_confidence > 0.5 and llm_confidence > 0.7:
                final_confidence = min(0.98, base_confidence + 0.4 + wordplay_boost)
            else:
                final_confidence = min(0.95, base_confidence + 0.3 + wordplay_boost)
            
            merged_predictions[normalized]['confidence'] = final_confidence
            merged_predictions[normalized]['sources'].append("llm")
            # Update with LLM metadata if available
            if result.get('category'):
                merged_predictions[normalized]['category'] = result['category']
            if result.get('explanation'):
                merged_predictions[normalized]['explanation'] = result['explanation']
            merged_predictions[normalized]['method'] = "hybrid"
        else:
            # LLM-only prediction (weight 0.5 + wordplay boost)
            merged_predictions[normalized] = {
                "words": result['words'],
                "confidence": (result['confidence'] * 0.5) + wordplay_boost,  # Weight LLM + wordplay
                "method": "llm",
                "category": result.get('category'),
                "explanation": result.get('explanation'),
                "sources": ["llm"]
            }
    
    # Create wordplay-based predictions if we found strong patterns
    if wordplay_findings.get('name_combination_group') and len(wordplay_findings['name_combination_group']) >= 4:
        name_words = wordplay_findings['name_combination_group'][:4]
        normalized = _normalize_group(name_words)
        if normalized not in merged_predictions:
            merged_predictions[normalized] = {
                "words": name_words,
                "confidence": 0.75,  # High confidence for detected wordplay
                "method": "wordplay",
                "category": "WORDS WITH HIDDEN NAMES",
                "explanation": "Words that can be split into two names",
                "sources": ["wordplay"]
            }
    
    # Convert to list and sort by confidence
    all_predictions = list(merged_predictions.values())
    
    # Apply overlap penalties
    for i, pred1 in enumerate(all_predictions):
        words1 = set(w.upper() for w in pred1['words'])
        for j, pred2 in enumerate(all_predictions):
            if i == j:
                continue
            words2 = set(w.upper() for w in pred2['words'])
            overlap = len(words1.intersection(words2))
            if overlap >= 2:  # Major conflict
                # Penalize both, but more heavily the lower confidence one
                if pred1['confidence'] > pred2['confidence']:
                    pred2['confidence'] *= 0.7  # 30% penalty
                else:
                    pred1['confidence'] *= 0.7  # 30% penalty
    
    # Re-sort after penalties
    all_predictions.sort(key=lambda x: x['confidence'], reverse=True)
    
    print(f"Total unique predictions after merging: {len(all_predictions)}", file=sys.stderr)
    print(f"LLM results count: {len(llm_results)}, Embeddings results count: {len(embeddings_results)}", file=sys.stderr)
    
    # Find best 4-group solution that uses all 16 words
    best_4_groups = find_best_solution(all_predictions, words)
    all_words_covered = False
    
    if best_4_groups:
        # Found valid 4-group solution
        all_words_covered = True
        print(f"Found valid 4-group solution covering all 16 words", file=sys.stderr)
        
        # Diversity bonus: boost all by 5%
        for pred in best_4_groups:
            pred['confidence'] = min(0.98, pred['confidence'] * 1.05)
    else:
        # Fallback: Get top 4 non-overlapping predictions
        print("Warning: No perfect 4-group solution found, using top 4 by confidence", file=sys.stderr)
        best_4_groups = []
        used_words: Set[str] = set()
        
        for pred in all_predictions:
            pred_words_upper = set(word.upper() for word in pred['words'])
            
            # Check if this prediction overlaps with any already selected
            if pred_words_upper.intersection(used_words):
                continue  # Skip if overlaps
            
            # Add this prediction
            best_4_groups.append(pred)
            used_words.update(pred_words_upper)
            
            if len(best_4_groups) >= 4:
                break
        
        # Check if we got all 16 words
        all_used = set()
        for pred in best_4_groups:
            all_used.update(w.upper() for w in pred['words'])
        if len(all_used) == 16:
            all_words_covered = True
            print("Top 4 predictions cover all words", file=sys.stderr)
            # Boost for diversity
            for pred in best_4_groups:
                pred['confidence'] = min(0.98, pred['confidence'] * 1.05)
    
    # Get additional predictions for exploration (up to 10 total)
    additional_predictions = []
    used_in_solution = set()
    for pred in best_4_groups:
        used_in_solution.update(w.upper() for w in pred['words'])
    
    for pred in all_predictions:
        if len(additional_predictions) >= 6:  # 4 in solution + 6 more = 10 total
            break
        pred_words_upper = set(word.upper() for word in pred['words'])
        # Skip if already in solution or overlaps with solution
        if not pred_words_upper.intersection(used_in_solution):
            additional_predictions.append(pred)
    
    # Add difficulty predictions
    try:
        best_4_groups = add_difficulty_to_predictions(best_4_groups, words)
        additional_predictions = add_difficulty_to_predictions(additional_predictions, words)
    except Exception as e:
        print(f"Warning: Could not add difficulty predictions: {e}", file=sys.stderr)
    
    # Calculate solve time
    solve_time_ms = (time.time() - start_time) * 1000
    
    print(f"\nTop solution: {len(best_4_groups)} groups", file=sys.stderr)
    print(f"Additional predictions: {len(additional_predictions)}", file=sys.stderr)
    print(f"All words covered: {all_words_covered}", file=sys.stderr)
    print(f"Solve time: {solve_time_ms:.2f}ms", file=sys.stderr)
    
    return {
        "top_solution": best_4_groups,
        "all_predictions": best_4_groups + additional_predictions,  # Solution first, then alternatives
        "solve_time_ms": round(solve_time_ms, 2),
        "methods_used": methods_used,
        "all_words_covered": all_words_covered
    }


if __name__ == "__main__":
    """Test the hybrid solver"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Test with sample words
    test_words = [
        "FAST", "FIRM", "SECURE", "TIGHT",
        "ACCOUNT", "CLIENT", "CONSUMER", "USER",
        "FROSTY", "MISTLETOE", "RAINMAKER", "SNOWMAN",
        "AUCTION", "MOVIE", "PARTNER", "TREATMENT"
    ]
    
    print("Testing hybrid solver...")
    print(f"Words: {test_words}\n")
    
    # Test with embeddings only
    print("=" * 60)
    print("TEST 1: Embeddings Only")
    print("=" * 60)
    try:
        result = solve_puzzle(test_words, use_llm=False)
        print(f"\nMethods used: {result['methods_used']}")
        print(f"Solve time: {result['solve_time_ms']}ms")
        print(f"\nTop 5 predictions:")
        for i, pred in enumerate(result['predictions'][:5], 1):
            print(f"\n{i}. Confidence: {pred['confidence']:.3f} ({pred['method']})")
            print(f"   Words: {pred['words']}")
            if pred.get('category'):
                print(f"   Category: {pred['category']}")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    # Test with both methods
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print("\n" + "=" * 60)
        print("TEST 2: Embeddings + LLM (Hybrid)")
        print("=" * 60)
        try:
            result = solve_puzzle(test_words, use_llm=True, api_key=api_key)
            print(f"\nMethods used: {result['methods_used']}")
            print(f"Solve time: {result['solve_time_ms']}ms")
            print(f"\nTop 5 predictions:")
            for i, pred in enumerate(result['predictions'][:5], 1):
                print(f"\n{i}. Confidence: {pred['confidence']:.3f} ({pred['method']})")
                print(f"   Words: {pred['words']}")
                if pred.get('category'):
                    print(f"   Category: {pred['category']}")
                if pred.get('explanation'):
                    print(f"   Explanation: {pred['explanation']}")
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\nSkipping LLM test (no API key found)")

