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
    
    print("Starting hybrid solver...")
    
    # Always run embeddings solver (fast)
    print("\n[1/2] Running embeddings solver...")
    embeddings_results = solve_with_embeddings(words)
    print(f"Embeddings solver found {len(embeddings_results)} predictions")
    
    # Conditionally run LLM solver
    llm_results = []
    if use_llm:
        print("\n[2/2] Running LLM solver...")
        try:
            llm_results = solve_with_llm(words, api_key)
            print(f"LLM solver found {len(llm_results)} predictions")
            methods_used.append("llm")
        except Exception as e:
            print(f"Warning: LLM solver failed: {str(e)}")
            print("Continuing with embeddings-only results...")
    
    # Merge and rank predictions
    print("\nMerging and ranking predictions...")
    
    # Create a dictionary to track merged predictions
    merged_predictions: Dict[tuple, Dict[str, Any]] = {}
    
    # Process embeddings results (weight 0.4)
    for result in embeddings_results:
        normalized = _normalize_group(result['words'])
        if normalized not in merged_predictions:
            merged_predictions[normalized] = {
                "words": result['words'],
                "confidence": result['confidence'] * 0.4,  # Weight embeddings
                "method": "embeddings",
                "category": None,
                "explanation": None,
                "sources": ["embeddings"]
            }
        else:
            # Already exists, keep higher confidence
            existing = merged_predictions[normalized]
            existing['confidence'] = max(existing['confidence'], result['confidence'] * 0.4)
    
    # Process LLM results (weight 0.6, boost if also in embeddings)
    for result in llm_results:
        normalized = _normalize_group(result['words'])
        
        if normalized in merged_predictions:
            # Found in both solvers - boost confidence to 0.95+
            merged_predictions[normalized]['confidence'] = max(0.95, merged_predictions[normalized]['confidence'] + 0.3)
            merged_predictions[normalized]['sources'].append("llm")
            # Update with LLM metadata if available
            if result.get('category'):
                merged_predictions[normalized]['category'] = result['category']
            if result.get('explanation'):
                merged_predictions[normalized]['explanation'] = result['explanation']
            merged_predictions[normalized]['method'] = "hybrid"
        else:
            # LLM-only prediction (weight 0.6)
            merged_predictions[normalized] = {
                "words": result['words'],
                "confidence": result['confidence'] * 0.6,  # Weight LLM
                "method": "llm",
                "category": result.get('category'),
                "explanation": result.get('explanation'),
                "sources": ["llm"]
            }
    
    # Convert to list and sort by confidence
    all_predictions = list(merged_predictions.values())
    all_predictions.sort(key=lambda x: x['confidence'], reverse=True)
    
    print(f"Total unique predictions after merging: {len(all_predictions)}")
    
    # Filter to top 10, ensuring no word overlaps
    top_predictions = []
    used_words: Set[str] = set()
    
    for pred in all_predictions:
        pred_words_upper = set(word.upper() for word in pred['words'])
        
        # Check if this prediction overlaps with any already selected
        if pred_words_upper.intersection(used_words):
            continue  # Skip if overlaps
        
        # Add this prediction
        top_predictions.append(pred)
        used_words.update(pred_words_upper)
        
        if len(top_predictions) >= 10:
            break
    
    # Calculate solve time
    solve_time_ms = (time.time() - start_time) * 1000
    
    print(f"\nSelected top {len(top_predictions)} non-overlapping predictions")
    print(f"Solve time: {solve_time_ms:.2f}ms")
    
    return {
        "predictions": top_predictions,
        "solve_time_ms": round(solve_time_ms, 2),
        "methods_used": methods_used
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

