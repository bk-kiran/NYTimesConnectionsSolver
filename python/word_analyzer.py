"""
Universal Word Analyzer for NYT Connections Puzzles

Analyzes individual words for ALL possible properties and patterns.
"""

from typing import List, Dict, Any, Set, Optional
from python.wordplay_detector import detect_name_combinations, COMMON_NAMES, COMMON_COMPOUNDS


def check_word_combinations(word: str) -> List[tuple[str, str]]:
    """
    Check if a word can be split into two common words.
    
    Args:
        word: Word to analyze
        
    Returns:
        List of tuples (word1, word2) if valid splits found
    """
    word_upper = word.upper()
    results = []
    
    # Try all possible splits (minimum 2 chars per word)
    for split_point in range(2, len(word_upper) - 1):
        part1 = word_upper[:split_point]
        part2 = word_upper[split_point:]
        
        # Check if both parts are common words (simple heuristic)
        # In a real implementation, you'd use a dictionary
        if len(part1) >= 2 and len(part2) >= 2:
            results.append((part1, part2))
    
    return results


def check_affixes(word: str) -> Dict[str, Optional[str]]:
    """
    Check for common prefixes and suffixes.
    
    Args:
        word: Word to analyze
        
    Returns:
        Dictionary with 'prefix' and 'suffix' keys
    """
    word_upper = word.upper()
    
    common_prefixes = ['UN', 'RE', 'PRE', 'DIS', 'MIS', 'OVER', 'OUT', 'IN', 'IM', 'NON']
    common_suffixes = ['ING', 'TION', 'LY', 'ER', 'ED', 'S', 'ES', 'NESS', 'MENT', 'ABLE', 'IBLE']
    
    prefix = None
    suffix = None
    
    for p in common_prefixes:
        if word_upper.startswith(p):
            prefix = p
            break
    
    for s in common_suffixes:
        if word_upper.endswith(s):
            suffix = s
            break
    
    return {'prefix': prefix, 'suffix': suffix}


def get_common_preceding_words(word: str) -> List[str]:
    """
    Get words that commonly precede this word (for fill-in-blank patterns).
    
    Args:
        word: Word to analyze
        
    Returns:
        List of words that commonly precede this word
    """
    word_upper = word.upper()
    preceding = []
    
    # Check COMMON_COMPOUNDS for words that precede this word
    for compound, common_words in COMMON_COMPOUNDS.items():
        if word_upper == compound:
            preceding.extend(common_words)
    
    return preceding


def get_common_following_words(word: str) -> List[str]:
    """
    Get words that commonly follow this word (for fill-in-blank patterns).
    
    Args:
        word: Word to analyze
        
    Returns:
        List of words that commonly follow this word
    """
    word_upper = word.upper()
    following = []
    
    # Check if this word is a common prefix in compounds
    for compound, common_words in COMMON_COMPOUNDS.items():
        if word_upper in common_words:
            following.append(compound)
    
    return following


def get_definitions(word: str) -> List[str]:
    """
    Get multiple meanings/definitions for a word.
    
    Args:
        word: Word to analyze
        
    Returns:
        List of possible meanings (simplified - in production use a dictionary API)
    """
    # Simplified - in production, use WordNet, dictionary API, or embeddings
    # For now, return common multiple meanings based on word
    word_upper = word.upper()
    
    multiple_meanings = {
        'STILL': ['motionless', 'yet/nevertheless', 'distillery', 'photograph'],
        'BANK': ['financial institution', 'river edge', 'to tilt'],
        'BARK': ['tree covering', 'dog sound', 'boat'],
        'BAT': ['flying mammal', 'sports equipment', 'to hit'],
        'BEAR': ['animal', 'to carry', 'to tolerate'],
        'BOW': ['weapon', 'to bend', 'front of ship'],
        'FAIR': ['just', 'carnival', 'light-colored'],
        'LEAD': ['metal', 'to guide', 'first position'],
        'MATCH': ['game', 'to correspond', 'fire starter'],
        'PARK': ['green space', 'to leave vehicle'],
        'PLAY': ['drama', 'to engage in activity', 'freedom of movement'],
        'RING': ['jewelry', 'sound', 'arena'],
        'ROCK': ['stone', 'to sway', 'music genre'],
        'SEAL': ['animal', 'to close', 'stamp'],
        'TIE': ['neckwear', 'to fasten', 'equal score'],
        'WAVE': ['water movement', 'to gesture', 'hair pattern'],
    }
    
    return multiple_meanings.get(word_upper, [word_upper.lower()])


def get_categories(word: str) -> List[str]:
    """
    Get categories/hypernyms for a word.
    
    Args:
        word: Word to analyze
        
    Returns:
        List of categories this word belongs to
    """
    # Simplified - in production, use WordNet or embeddings
    word_upper = word.upper()
    
    # Common category mappings
    category_map = {
        'HAMMER': ['tool', 'hardware', 'percussion instrument'],
        'SCREWDRIVER': ['tool', 'hardware', 'drink'],
        'WRENCH': ['tool', 'hardware'],
        'SHOVEL': ['tool', 'gardening equipment'],
        'RAKE': ['tool', 'gardening equipment'],
        'SPADE': ['tool', 'gardening equipment', 'card suit'],
        'HOSE': ['tool', 'gardening equipment', 'clothing'],
    }
    
    return category_map.get(word_upper, [])


def get_homophones(word: str) -> List[str]:
    """
    Get homophones (words that sound the same).
    
    Args:
        word: Word to analyze
        
    Returns:
        List of homophones
    """
    # Simplified - in production, use phonetic matching
    word_upper = word.upper()
    
    homophone_map = {
        'THERE': ['THEIR', "THEY'RE"],
        'THEIR': ['THERE', "THEY'RE"],
        "THEY'RE": ['THERE', 'THEIR'],
        'TO': ['TWO', 'TOO'],
        'TWO': ['TO', 'TOO'],
        'TOO': ['TO', 'TWO'],
        'SEE': ['SEA', 'C'],
        'SEA': ['SEE', 'C'],
        'C': ['SEE', 'SEA'],
        'REIGN': ['RAIN', 'REIN'],
        'RAIN': ['REIGN', 'REIN'],
        'REIN': ['REIGN', 'RAIN'],
        'BREAK': ['BRAKE'],
        'BRAKE': ['BREAK'],
        'FLOUR': ['FLOWER'],
        'FLOWER': ['FLOUR'],
    }
    
    return homophone_map.get(word_upper, [])


def get_rhyming_words(word: str) -> List[str]:
    """
    Get words that rhyme with this word.
    
    Args:
        word: Word to analyze
        
    Returns:
        List of rhyming words (simplified)
    """
    # Simplified - in production, use phonetic library
    # For now, return empty as this is complex
    return []


def analyze_word(word: str) -> Dict[str, Any]:
    """
    Extract all properties and patterns for a single word.
    
    Args:
        word: Word to analyze
        
    Returns:
        Comprehensive analysis dictionary
    """
    analysis = {
        'word': word.upper(),
        'length': len(word),
        'name_splits': detect_name_combinations(word),
        'word_splits': check_word_combinations(word),
        'affixes': check_affixes(word),
        'before_words': get_common_preceding_words(word),
        'after_words': get_common_following_words(word),
        'definitions': get_definitions(word),
        'categories': get_categories(word),
        'homophones': get_homophones(word),
        'rhymes': get_rhyming_words(word),
    }
    
    return analysis


def find_words_with_name_splits(word_analyses: List[Dict[str, Any]]) -> List[str]:
    """Find words that have name splits."""
    return [a['word'] for a in word_analyses if len(a['name_splits']) > 0]


def find_common_before_words(word_analyses: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Find words that share common preceding words."""
    before_map = {}
    for analysis in word_analyses:
        for before_word in analysis['before_words']:
            if before_word not in before_map:
                before_map[before_word] = []
            before_map[before_word].append(analysis['word'])
    
    # Filter to groups with 3+ words
    return {k: v for k, v in before_map.items() if len(v) >= 3}


def find_common_after_words(word_analyses: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Find words that share common following words."""
    after_map = {}
    for analysis in word_analyses:
        for after_word in analysis['after_words']:
            if after_word not in after_map:
                after_map[after_word] = []
            after_map[after_word].append(analysis['word'])
    
    # Filter to groups with 3+ words
    return {k: v for k, v in after_map.items() if len(v) >= 3}


def find_shared_categories(word_analyses: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Find words that share common categories."""
    category_map = {}
    for analysis in word_analyses:
        for category in analysis['categories']:
            if category not in category_map:
                category_map[category] = []
            category_map[category].append(analysis['word'])
    
    # Filter to groups with 3+ words
    return {k: v for k, v in category_map.items() if len(v) >= 3}


def find_shared_prefixes(word_analyses: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Find words that share common prefixes."""
    prefix_map = {}
    for analysis in word_analyses:
        prefix = analysis['affixes'].get('prefix')
        if prefix:
            if prefix not in prefix_map:
                prefix_map[prefix] = []
            prefix_map[prefix].append(analysis['word'])
    
    # Filter to groups with 3+ words
    return {k: v for k, v in prefix_map.items() if len(v) >= 3}


def find_homophone_groups(word_analyses: List[Dict[str, Any]]) -> List[List[str]]:
    """Find groups of homophones."""
    homophone_groups = []
    seen = set()
    
    for analysis in word_analyses:
        word = analysis['word']
        if word in seen:
            continue
        
        homophones = analysis['homophones']
        if homophones:
            group = [word]
            for h in homophones:
                # Check if homophone is in our word list
                for other_analysis in word_analyses:
                    if other_analysis['word'] == h:
                        group.append(h)
                        seen.add(h)
                        break
            
            if len(group) >= 2:
                homophone_groups.append(group)
                seen.add(word)
    
    return homophone_groups


def find_rhyme_groups(word_analyses: List[Dict[str, Any]]) -> List[List[str]]:
    """Find groups of rhyming words."""
    # Simplified - would need phonetic library for real implementation
    return []


def analyze_all_words(words: List[str]) -> Dict[str, Any]:
    """
    Analyze all 16 words and find cross-word patterns.
    
    Args:
        words: List of 16 puzzle words
        
    Returns:
        Comprehensive analysis with individual word analyses and cross-word patterns
    """
    word_analyses = [analyze_word(w) for w in words]
    
    # Find patterns across all words
    patterns = {
        'name_combinations': find_words_with_name_splits(word_analyses),
        'fill_in_blank_before': find_common_before_words(word_analyses),
        'fill_in_blank_after': find_common_after_words(word_analyses),
        'shared_categories': find_shared_categories(word_analyses),
        'shared_prefixes': find_shared_prefixes(word_analyses),
        'homophone_groups': find_homophone_groups(word_analyses),
        'rhyme_groups': find_rhyme_groups(word_analyses),
    }
    
    return {
        'individual_analyses': word_analyses,
        'cross_word_patterns': patterns
    }


if __name__ == "__main__":
    # Test the word analyzer
    test_words = ["JACKAL", "LEVITATE", "MELTED", "PATRON", "BASKET", "FOOT", "SNOW", "EYE"]
    
    print("Testing word analyzer...")
    analysis = analyze_all_words(test_words)
    
    print("\nName combinations found:")
    print(analysis['cross_word_patterns']['name_combinations'])
    
    print("\nFill-in-blank patterns (before):")
    print(analysis['cross_word_patterns']['fill_in_blank_before'])
    
    print("\nFill-in-blank patterns (after):")
    print(analysis['cross_word_patterns']['fill_in_blank_after'])

