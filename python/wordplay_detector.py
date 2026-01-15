"""
Wordplay Detection for NYT Connections Puzzles

Detects common wordplay patterns used in Connections puzzles.
"""

import re
from typing import List, Dict, Tuple, Any, Optional
from itertools import combinations

# Common first names (top 200 most common)
COMMON_NAMES = {
    'JACK', 'JOHN', 'JAMES', 'ROBERT', 'MICHAEL', 'WILLIAM', 'DAVID', 'RICHARD',
    'JOSEPH', 'THOMAS', 'CHARLES', 'CHRISTOPHER', 'DANIEL', 'MATTHEW', 'ANTHONY',
    'MARK', 'DONALD', 'STEVEN', 'PAUL', 'ANDREW', 'JOSHUA', 'KENNETH', 'KEVIN',
    'BRIAN', 'GEORGE', 'EDWARD', 'RONALD', 'TIMOTHY', 'JASON', 'JEFFREY',
    'RYAN', 'JACOB', 'GARY', 'NICHOLAS', 'ERIC', 'JONATHAN', 'STEPHEN', 'LARRY',
    'JUSTIN', 'SCOTT', 'BRANDON', 'BENJAMIN', 'SAMUEL', 'FRANK', 'GREGORY',
    'RAYMOND', 'ALEXANDER', 'PATRICK', 'JACK', 'DENNIS', 'JERRY', 'TYLER',
    'AARON', 'JOSE', 'HENRY', 'ADAM', 'DOUGLAS', 'NATHAN', 'ZACHARY', 'KYLE',
    'NOAH', 'ETHAN', 'JEREMY', 'WALTER', 'CHRISTIAN', 'KEITH', 'ROGER', 'TERRY',
    'ALAN', 'SEAN', 'WAYNE', 'RALPH', 'ROY', 'JUAN', 'LOUIS', 'PHILIP', 'BOBBY',
    'JOHNNY', 'RUSSELL', 'ALBERT', 'ALEX', 'AL', 'TED', 'MEL', 'PAT', 'RON',
    'LEVI', 'TATE', 'TED', 'MEL', 'PAT', 'RON', 'JACK', 'AL', 'LEVI', 'TATE',
    'BEN', 'SAM', 'JIM', 'TOM', 'DAN', 'BOB', 'JOE', 'LEO', 'MAX', 'IAN',
    'NOAH', 'LUKE', 'OWEN', 'ELI', 'LEO', 'HENRY', 'JACK', 'OLIVER', 'WILLIAM',
    'JAMES', 'BENJAMIN', 'LUCAS', 'HENRY', 'ALEXANDER', 'MASON', 'MICHAEL',
    'ETHAN', 'DANIEL', 'JACOB', 'LOGAN', 'JACKSON', 'LEVI', 'SEBASTIAN', 'MATTHEW',
    'JACK', 'LUKE', 'OWEN', 'THEODORE', 'AIDEN', 'SAMUEL', 'JOSEPH', 'JOHN',
    'DAVID', 'WYATT', 'MATTHEW', 'LUKE', 'ASHER', 'CARTER', 'JULIAN', 'GRAYSON',
    'LEO', 'JAYDEN', 'GABRIEL', 'ISAAC', 'LINCOLN', 'ANTHONY', 'HUDSON', 'DYLAN',
    'EZRA', 'THOMAS', 'CHARLES', 'CHRISTOPHER', 'JAXON', 'MAVERICK', 'JOSIAH',
    'ISAIAH', 'ANDREW', 'ELIAS', 'JOSHUA', 'NATHAN', 'CALEB', 'RYAN', 'ADRIAN',
    'MILES', 'ELI', 'NOLAN', 'CHRISTIAN', 'AARON', 'COLIN', 'CHARLES', 'BLake',
    'ADAM', 'TRUMAN', 'ROMAN', 'BRODY', 'IAN', 'COOPER', 'AXEL', 'CARLOS',
    'JAXON', 'JASON', 'JAXON', 'JAXON', 'JAXON', 'JAXON', 'JAXON', 'JAXON',
    # Female names (less common but still possible)
    'ANN', 'MAY', 'JOY', 'LEE', 'KAY', 'EVE', 'ADA', 'IDA', 'IVY', 'AMY',
    'JILL', 'JANE', 'JOAN', 'JEAN', 'ROSE', 'RUTH', 'MARY', 'ANNA', 'ELLA',
    'LILY', 'EMMA', 'OLIVIA', 'SOPHIA', 'ISABELLA', 'CHARLOTTE', 'AMELIA',
    'MIA', 'HARPER', 'EVELYN', 'ABIGAIL', 'EMILY', 'ELIZABETH', 'MILA',
    'ELLA', 'AVERY', 'SOFIA', 'CAMILA', 'ARIA', 'SCARLETT', 'VICTORIA',
    'MADISON', 'LUNA', 'GRACE', 'CHLOE', 'PENELOPE', 'LAYLA', 'RILEY',
    'ZOEY', 'NORA', 'LILY', 'ELEANOR', 'HANNAH', 'LILLIAN', 'ADDISON',
    'AUBREY', 'ELLIE', 'STELLA', 'NATALIE', 'ZOEY', 'LEAH', 'HAZEL',
    'VIOLET', 'AURORA', 'SAVANNAH', 'AUDREY', 'BROOKLYN', 'BELLA',
    'CLAIRE', 'SKYLAR', 'LUCY', 'Paisley', 'EVERLY', 'ANNA', 'CAROLINE',
    'NOVA', 'GENESIS', 'AALIYAH', 'KENNEDY', 'KINSLEY', 'ALLISON', 'MAYA',
    'SARAH', 'ARIANNA', 'ALICE', 'MADELYN', 'CORALINE', 'HADLEY', 'GABRIELLA',
    'CELESTE', 'JADE', 'JOSEPHINE', 'PEARL', 'RUBY', 'SADIE', 'AUDREY',
    'NAOMI', 'ELIZA', 'ARIA', 'ELENA', 'QUINN', 'MADELEINE', 'DELILAH',
    'GENEVIEVE', 'JULIETTE', 'ROSE', 'MARGARET', 'CATHERINE', 'ANNABELLE'
}

# Common compound word patterns
COMMON_COMPOUNDS = {
    'BALL': ['BASKET', 'FOOT', 'SNOW', 'EYE', 'BASE', 'SOFT', 'VOLLEY', 'BEACH'],
    'BOARD': ['CHESS', 'DASH', 'KEY', 'CUTTING', 'BULLETIN', 'BLACK', 'WHITE'],
    'ROOM': ['BED', 'LIVING', 'DINING', 'BATH', 'CLASS', 'WAITING', 'BOOM'],
    'MATE': ['CLASS', 'ROOM', 'TEAM', 'SOUL', 'CHECK', 'PLAY'],
    'WORK': ['HOME', 'FIRE', 'TEAM', 'NET', 'FRAME', 'ART', 'HOUSE'],
    'HOUSE': ['TREE', 'WHITE', 'GREEN', 'PLAY', 'WARE', 'LIGHTHOUSE'],
    'LINE': ['PICKUP', 'BOTTOM', 'DEAD', 'FINISH', 'GOAL', 'TIMELINE'],
    'CODE': ['ZIP', 'AREA', 'POSTAL', 'MORSE', 'BAR', 'SOURCE'],
    'BAR': ['CANDY', 'CHOCOLATE', 'SOAP', 'CEREAL', 'PROGRESS', 'SNACK'],
    'FIRE': ['CAMP', 'WILD', 'BON', 'CEASE', 'GUN', 'PLACE'],
    'SNOW': ['BLOW', 'SHOW', 'FALL', 'BALL', 'MAN', 'WHITE'],
    'SUN': ['RISE', 'SET', 'SHINE', 'LIGHT', 'GLASS', 'FLOWER'],
    'MOON': ['FULL', 'NEW', 'HALF', 'LIGHT', 'BEAM', 'SHINE'],
    'SEA': ['UNDER', 'OVER', 'DEEP', 'SHALLOW', 'LEVEL', 'SHORE'],
    'AIR': ['FRESH', 'THIN', 'FAIR', 'STAIR', 'HAIR', 'PAIR'],
    'TIME': ['LIFE', 'PART', 'FULL', 'HALF', 'QUARTER', 'PRIME'],
    'DAY': ['BIRTH', 'HOLI', 'WEEK', 'YESTER', 'TO', 'SUN'],
    'NIGHT': ['MID', 'TO', 'OVER', 'LIGHT', 'DARK', 'LATE'],
    'LIGHT': ['DAY', 'NIGHT', 'MOON', 'SUN', 'BRIGHT', 'FAIRY'],
    'STAR': ['MOVIE', 'ROCK', 'POP', 'SHOOTING', 'MORNING', 'EVENING']
}


def detect_name_combinations(word: str) -> List[Tuple[str, str]]:
    """
    Check if a word can be split into two common names.
    
    Args:
        word: Word to analyze
        
    Returns:
        List of tuples (name1, name2) if valid splits found
    """
    word_upper = word.upper()
    results = []
    
    # Try all possible splits (minimum 2 chars per name)
    for split_point in range(2, len(word_upper) - 1):
        part1 = word_upper[:split_point]
        part2 = word_upper[split_point:]
        
        # Check if both parts are in common names
        if part1 in COMMON_NAMES and part2 in COMMON_NAMES:
            results.append((part1, part2))
    
    return results


def find_fill_in_blank_patterns(words: List[str]) -> Dict[str, Any]:
    """
    Find ___ [WORD] or [WORD] ___ patterns.
    
    Args:
        words: List of words to analyze
        
    Returns:
        Dictionary with pattern matches
    """
    patterns = {
        'suffixes': {},  # Words that go before common suffix
        'prefixes': {}   # Words that go after common prefix
    }
    
    words_upper = [w.upper() for w in words]
    
    # Check suffixes
    for suffix, common_words in COMMON_COMPOUNDS.items():
        matches = []
        for word in words_upper:
            if word + suffix in common_words or word in common_words:
                # Check if word can precede the suffix
                potential_compound = word + suffix
                if potential_compound in common_words or word in common_words:
                    matches.append(word)
        
        if len(matches) >= 2:  # At least 2 words share this pattern
            patterns['suffixes'][suffix] = matches
    
    # Check prefixes
    for prefix, common_words in COMMON_COMPOUNDS.items():
        matches = []
        for word in words_upper:
            potential_compound = prefix + word
            if potential_compound in common_words or word in common_words:
                matches.append(word)
        
        if len(matches) >= 2:
            patterns['prefixes'][prefix] = matches
    
    return patterns


def detect_compound_patterns(words: List[str]) -> List[Dict[str, Any]]:
    """
    Find words that combine with the same word.
    
    Args:
        words: List of words to analyze
        
    Returns:
        List of compound pattern matches
    """
    words_upper = [w.upper() for w in words]
    results = []
    
    # Check each common compound pattern
    for compound_word, common_prefixes in COMMON_COMPOUNDS.items():
        # Check if words can precede this compound
        matches = []
        for word in words_upper:
            if word in common_prefixes:
                matches.append(word)
        
        if len(matches) >= 3:  # At least 3 words share this pattern
            results.append({
                'pattern': f"___ {compound_word}",
                'words': matches,
                'compound': compound_word
            })
        
        # Check if words can follow this compound (as prefix)
        matches = []
        for word in words_upper:
            potential = compound_word + word
            if potential in common_prefixes or word in common_prefixes:
                matches.append(word)
        
        if len(matches) >= 3:
            results.append({
                'pattern': f"{compound_word} ___",
                'words': matches,
                'compound': compound_word
            })
    
    return results


def check_homophones(words: List[str]) -> List[List[str]]:
    """
    Find words that sound like other words (simple phonetic check).
    
    Args:
        words: List of words to analyze
        
    Returns:
        List of groups of homophones
    """
    # Simple phonetic mapping (soundex-like)
    def simple_soundex(word: str) -> str:
        """Simple phonetic code"""
        word = word.upper()
        if not word:
            return ""
        
        # Keep first letter
        code = word[0]
        
        # Map similar sounds
        sound_map = {
            'B': '1', 'F': '1', 'P': '1', 'V': '1',
            'C': '2', 'G': '2', 'J': '2', 'K': '2', 'Q': '2', 'S': '2', 'X': '2', 'Z': '2',
            'D': '3', 'T': '3',
            'L': '4',
            'M': '5', 'N': '5',
            'R': '6'
        }
        
        for char in word[1:]:
            if char in sound_map:
                code += sound_map[char]
            if len(code) >= 4:
                break
        
        return code.ljust(4, '0')
    
    # Group words by phonetic code
    phonetic_groups = {}
    for word in words:
        code = simple_soundex(word)
        if code not in phonetic_groups:
            phonetic_groups[code] = []
        phonetic_groups[code].append(word.upper())
    
    # Return groups with 2+ words
    return [group for group in phonetic_groups.values() if len(group) >= 2]


def analyze_all_wordplay(words: List[str]) -> Dict[str, Any]:
    """
    Run all wordplay detection checks.
    
    Args:
        words: List of 16 puzzle words
        
    Returns:
        Comprehensive wordplay analysis
    """
    findings = {
        'name_combinations': {},
        'fill_in_blank': find_fill_in_blank_patterns(words),
        'compounds': detect_compound_patterns(words),
        'homophones': check_homophones(words)
    }
    
    # Check each word for name combinations
    for word in words:
        name_splits = detect_name_combinations(word)
        if name_splits:
            findings['name_combinations'][word.upper()] = name_splits
    
    # Find groups of 4+ words with name combinations
    words_with_names = list(findings['name_combinations'].keys())
    if len(words_with_names) >= 4:
        findings['name_combination_group'] = words_with_names[:4]
    
    return findings


def format_wordplay_findings(findings: Dict[str, Any]) -> str:
    """
    Format wordplay findings for GPT-4 prompt.
    
    Args:
        findings: Wordplay analysis results
        
    Returns:
        Formatted string for prompt
    """
    lines = []
    
    # Name combinations
    if findings.get('name_combinations'):
        lines.append("NAME COMBINATIONS DETECTED:")
        for word, splits in findings['name_combinations'].items():
            for name1, name2 in splits:
                lines.append(f"  - {word} = {name1} + {name2}")
        lines.append("")
    
    # Fill-in-blank patterns
    if findings.get('fill_in_blank', {}).get('suffixes'):
        lines.append("FILL-IN-BLANK PATTERNS (___ + suffix):")
        for suffix, words_list in findings['fill_in_blank']['suffixes'].items():
            if len(words_list) >= 2:
                lines.append(f"  - {', '.join(words_list)} + {suffix}")
        lines.append("")
    
    if findings.get('fill_in_blank', {}).get('prefixes'):
        lines.append("FILL-IN-BLANK PATTERNS (prefix + ___):")
        for prefix, words_list in findings['fill_in_blank']['prefixes'].items():
            if len(words_list) >= 2:
                lines.append(f"  - {prefix} + {', '.join(words_list)}")
        lines.append("")
    
    # Compound patterns
    if findings.get('compounds'):
        lines.append("COMPOUND WORD PATTERNS:")
        for pattern in findings['compounds']:
            lines.append(f"  - {pattern['pattern']}: {', '.join(pattern['words'])}")
        lines.append("")
    
    # Homophones
    if findings.get('homophones'):
        lines.append("HOMOPHONES DETECTED:")
        for group in findings['homophones']:
            lines.append(f"  - {', '.join(group)}")
        lines.append("")
    
    return "\n".join(lines) if lines else "No obvious wordplay patterns detected."


if __name__ == "__main__":
    # Test the wordplay detector
    test_words = ["JACKAL", "LEVITATE", "MELTED", "PATRON", "BASKET", "FOOT", "SNOW", "EYE"]
    
    print("Testing wordplay detector...")
    findings = analyze_all_wordplay(test_words)
    
    print("\nFindings:")
    print(format_wordplay_findings(findings))

