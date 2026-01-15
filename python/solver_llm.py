"""
NYT Connections Solver using GPT-4

Uses OpenAI GPT-4 with Chain of Thought prompting to solve puzzles.
"""

import json
import openai
from typing import List, Dict, Any, Optional
import time
import sys


def solve_with_llm(words: List[str], api_key: str, wordplay_findings: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Solve NYT Connections puzzle using GPT-4.
    
    Args:
        words: List of 16 puzzle words
        api_key: OpenAI API key
        wordplay_findings: Optional wordplay analysis results
        
    Returns:
        List of 4 groups, each with:
        - words: List of 4 words
        - confidence: Confidence score (0-1)
        - category: Category name
        - explanation: Why these words belong together
        - method: "llm"
    """
    if len(words) != 16:
        raise ValueError(f"Expected 16 words, got {len(words)}")
    
    if not api_key:
        raise ValueError("OpenAI API key is required")
    
    # Set up OpenAI client
    client = openai.OpenAI(api_key=api_key)
    
    system_prompt = """You are an expert NYT Connections puzzle solver.

NYT Connections categories fall into these types (check ALL for every puzzle):

1. PHYSICAL PROPERTIES (common in easier categories):
   - Form/Shape: "comes in [form]" (bars, flakes, cubes, rings, balls, strips)
   - State: physical states (solid, liquid, frozen, melted)
   - Texture: (smooth, rough, soft, hard, sticky, dry)
   - Size: (small, large, tiny, massive)
   - NOT just "things that CAN BE X" - look for INHERENT properties

2. VISUAL/SENSORY (common in easier categories):
   - Color categories: "things that are [color]" (red, white, black, gold)
   - Sounds: (loud, quiet, musical, animal sounds)
   - Smell/Taste: (sweet, sour, bitter, fragrant)

3. CATEGORICAL (common in medium difficulty):
   - Types of X: "types of [noun]" (dogs, cars, trees, dances, sports)
   - Parts of X: "parts of [object]" (car parts, body parts, building parts)
   - Tools/Equipment: "used for [purpose]" (cleaning, cooking, gardening)
   - Professions, animals, foods, places, etc.

4. FUNCTIONAL (common in medium difficulty):
   - Actions: "things you can [verb]" (throw, eat, wear, ride)
   - Purpose: "used for [purpose]" (transportation, communication)
   - Location: "found in [place]" (kitchen, office, nature)

5. FILL-IN-BLANK (common in tricky categories):
   - Before: "[WORD] ___" (fire, water, snow, sun + truck/fall/board/etc)
   - After: "___ [WORD]" (various words + bar/ball/board/room)
   - Both: "___ [WORD] ___"

6. WORDPLAY (common in hardest categories):
   - Hidden names: word contains two names (JACKAL = JACK+AL, MATRIX = MAT+RIX)
   - Homophones: words that sound like other words
   - Anagrams: words that rearrange to form other words
   - Rhymes: words that rhyme with something specific
   - Word within word: larger word contains smaller word
   - Synonyms for the same homophone (words that sound like "see": sea, C, etc.)

7. LINGUISTIC PATTERNS (common in tricky categories):
   - Same prefix: words starting with same letters (UN-, RE-, PRE-)
   - Same suffix: words ending with same letters (-ING, -TION, -LY)
   - Letter patterns: words with double letters, palindromes
   - Length: words with same number of letters

8. ASSOCIATION/SEQUENCE (common in tricky categories):
   - "___ and ___" pairs: common word pairings (salt and ___, black and ___)
   - Sequences: (first, second, third), (Monday, Tuesday, etc.)
   - Pop culture: movie titles, song lyrics, famous quotes
   - Idioms: words that complete common phrases

9. ABSTRACT/THEMATIC (any difficulty):
   - Emotional: feelings, moods, attitudes
   - Temporal: related to time, seasons, eras
   - Mathematical: numbers, shapes, operations
   - Conceptual: abstract ideas with subtle connections

SOLVING PROCESS (follow for EVERY puzzle):

Step 1: ANALYZE EACH WORD
For each of the 16 words, consider:
- Physical form and properties
- Multiple meanings (literal vs. figurative)
- Can it be split into parts? (names, words, syllables)
- What words come before/after it commonly?
- What category does it belong to?
- Are there homophones or rhymes?

Step 2: CHECK ALL PATTERN TYPES
Go through ALL 9 category types above
Don't stop at first connection - explore all possibilities
A word like "STILL" could mean: unmoving (adjective), yet/nevertheless (adverb), photograph (noun), or distillery (noun)

Step 3: PRIORITIZE SPECIFIC OVER GENERAL
"Things that come in flakes" > "Things that can be white"
"Kitchen appliances" > "Things found in homes"
"Unmoving" > "Words related to motion"
Be as SPECIFIC and CONCRETE as possible

Step 4: VALIDATE CONNECTIONS
Each group must have ONE clear, specific connection
All 4 words should fit EQUALLY well (no forced inclusions)
Connection should be verifiable and objective

Step 5: RETURN 4 DISTINCT GROUPS
Each word used exactly once
Clear category name (1-3 words when possible)
Brief explanation of the connection

CRITICAL VALIDATION RULES:

1. WORD EXCLUSIVITY:
   - Each word belongs to EXACTLY ONE group
   - Do NOT use the same word in multiple groups
   - If a word could fit multiple categories, choose the BEST fit only

2. COMPLETE COVERAGE:
   - You must use ALL 16 words exactly once
   - After creating 4 groups, verify: 4 groups × 4 words = 16 total words
   - No word should be left out or duplicated

3. VERIFICATION CHECKLIST:
   Before returning your answer, verify:
   ☑ Each group has exactly 4 words
   ☑ All 16 words are used (no missing words)
   ☑ No word appears twice (no duplicates)
   ☑ Each group has a clear, specific connection
   
4. If you notice a word fits multiple groups:
   - Choose the MOST SPECIFIC connection
   - "FROZEN" fits "states of water" AND "unmoving" → Choose "unmoving" (more specific)
   - "SALT" fits "white things" AND "comes in flakes" → Choose "comes in flakes" (physical form)

5. Priority order for category selection:
   a) Wordplay patterns (names, compounds) - highest priority for purple
   b) Physical properties (form, state) - very concrete
   c) Fill-in-blank patterns - specific and verifiable
   d) Categorical (types of X) - clear membership
   e) Thematic/associative - use only when others don't work

Example of CORRECT solving process:

Words: FROZEN, STATIC, STILL, STATIONARY, SALT, SNOW, CEREAL, DANDRUFF, ...

Step 1: Identify FROZEN could mean:
- State of water (physical state)
- Unmoving (not moving)
→ Choose "unmoving" because it's alongside STATIC, STILL, STATIONARY

Step 2: Identify SALT could mean:
- White substance
- Comes in flakes/crystals
→ Choose "comes in flakes" because SNOW, CEREAL, DANDRUFF also come in flakes

Step 3: Verify final groups don't overlap
✓ Group 1: FROZEN, STATIC, STILL, STATIONARY (unmoving)
✓ Group 2: SALT, SNOW, CEREAL, DANDRUFF (comes in flakes)
✓ No word used twice"""

    # User prompt with the words and wordplay analysis
    wordplay_section = ""
    if wordplay_findings:
        try:
            from python.wordplay_detector import format_wordplay_findings
            formatted = format_wordplay_findings(wordplay_findings)
            if formatted and formatted != "No obvious wordplay patterns detected.":
                wordplay_section = f"""

WORDPLAY ANALYSIS DETECTED:
{formatted}

Consider these patterns when solving!"""
        except (ImportError, Exception) as e:
            # Wordplay detector not available or error, skip
            pass
    
    user_prompt = f"""Solve this NYT Connections puzzle by finding exactly 4 groups of 4 words each.

Words: {', '.join(words)}

{wordplay_section}

Follow the SOLVING PROCESS from the system prompt:
1. Analyze each word for ALL possible properties and meanings
2. Check ALL 9 category types systematically
3. Prioritize specific, concrete connections
4. Validate that all 4 words fit equally well
5. Return exactly 4 groups using all 16 words once

Return JSON format:
{{
  "groups": [
    {{
      "words": ["WORD1", "WORD2", "WORD3", "WORD4"],
      "category": "Specific Category Name",
      "explanation": "Why these 4 words connect",
      "category_type": "physical_property|categorical|fill_in_blank|wordplay|linguistic|association|abstract",
      "confidence": 0.95
    }},
    {{
      "words": ["WORD5", "WORD6", "WORD7", "WORD8"],
      "category": "Specific Category Name",
      "explanation": "...",
      "category_type": "...",
      "confidence": 0.90
    }},
    {{
      "words": ["WORD9", "WORD10", "WORD11", "WORD12"],
      "category": "Specific Category Name",
      "explanation": "...",
      "category_type": "...",
      "confidence": 0.85
    }},
    {{
      "words": ["WORD13", "WORD14", "WORD15", "WORD16"],
      "category": "Specific Category Name",
      "explanation": "...",
      "category_type": "...",
      "confidence": 0.80
    }}
  ]
}}

CRITICAL: 
- Return exactly 4 groups
- Use all 16 words exactly once
- Category names should be specific and concise (1-3 words)
- Only use high confidence (0.8+) if you're very certain
- Purple categories usually have lower confidence (0.6-0.8)
- Yellow categories should have high confidence (0.85+)"""

    try:
        print("Calling GPT-4 to solve puzzle...", file=sys.stderr)
        
        # Call GPT-4 with Chain of Thought prompting
        # Use gpt-4-turbo or gpt-4o which support JSON mode, fallback to gpt-4 without JSON mode
        try:
            # Try with JSON mode first (for newer models)
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.4,  # Slightly higher for creative wordplay detection
                response_format={"type": "json_object"},  # Request JSON output
                max_tokens=2500
            )
        except Exception as e:
            # Fallback to gpt-4 without JSON mode
            if "json_object" in str(e).lower() or "response_format" in str(e).lower():
                print("JSON mode not supported, using gpt-4 without JSON mode...", file=sys.stderr)
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.4,  # Slightly higher for creative wordplay detection
                    max_tokens=2000
                )
            else:
                raise
        
        # Extract the response content
        content = response.choices[0].message.content
        
        print("GPT-4 response received, parsing...", file=sys.stderr)
        
        # Parse JSON response
        try:
            # First, try to extract JSON from markdown code blocks if present
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            
            # Try to parse as JSON object first
            parsed_data = json.loads(content)
            
            # Handle different response formats
            if isinstance(parsed_data, dict):
                # If it's a dict, look for 'groups' or use the dict itself
                if 'groups' in parsed_data:
                    groups = parsed_data['groups']
                elif 'result' in parsed_data:
                    groups = parsed_data['result']
                else:
                    # Assume the dict contains the groups as values
                    groups = list(parsed_data.values()) if len(parsed_data) == 4 else [parsed_data]
            elif isinstance(parsed_data, list):
                groups = parsed_data
            else:
                raise ValueError("Unexpected response format")
            
            # Validate and format the response
            results = []
            used_words = set()
            
            for group in groups:
                if not isinstance(group, dict):
                    continue
                
                # Extract words
                group_words = group.get('words', [])
                if not isinstance(group_words, list) or len(group_words) != 4:
                    continue
                
                # Check for duplicates
                if any(w.upper() in used_words for w in group_words):
                    continue
                
                used_words.update(w.upper() for w in group_words)
                
                # Extract other fields
                category = group.get('category', 'Unknown')
                explanation = group.get('explanation', 'No explanation provided')
                confidence = float(group.get('confidence', 0.8))
                category_type = group.get('category_type', '')
                
                # Clamp confidence to 0-1 range
                confidence = max(0.0, min(1.0, confidence))
                
                results.append({
                    "words": group_words,
                    "confidence": confidence,
                    "category": category,
                    "explanation": explanation,
                    "category_type": category_type,
                    "method": "llm"
                })
            
            # Validate response
            validation = parsed_data.get('validation', {}) if isinstance(parsed_data, dict) else {}
            total_words = validation.get('total_words', 0)
            unique_words = validation.get('unique_words', 0)
            all_words_used = validation.get('all_words_used', False)
            no_duplicates = validation.get('no_duplicates', False)
            
            # Validate we have exactly 4 groups and all words are used
            if len(results) != 4:
                print(f"Warning: Expected 4 groups, got {len(results)}", file=sys.stderr)
            
            words_upper = set(w.upper() for w in words)
            if used_words != words_upper:
                missing = words_upper - used_words
                print(f"Warning: Not all words used. Missing: {missing}", file=sys.stderr)
            
            # Check for duplicates
            all_words_list = []
            for result in results:
                all_words_list.extend(w.upper() for w in result['words'])
            
            if len(all_words_list) != len(set(all_words_list)):
                duplicates = [w for w in all_words_list if all_words_list.count(w) > 1]
                print(f"Warning: Duplicate words found: {set(duplicates)}", file=sys.stderr)
            
            # Only accept if validation passes
            if not (all_words_used and no_duplicates and total_words == 16 and unique_words == 16):
                print(f"Warning: GPT-4 validation failed. all_words_used={all_words_used}, no_duplicates={no_duplicates}", file=sys.stderr)
                # Still return results but with warning
            
            print(f"Successfully parsed {len(results)} groups from GPT-4", file=sys.stderr)
            return results
            
        except json.JSONDecodeError as e:
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(1))
                # Process same as above
                results = []
                used_words = set()
                for group in parsed:
                    if isinstance(group, dict) and 'words' in group:
                        group_words = group['words']
                        if len(group_words) == 4 and not any(w in used_words for w in group_words):
                            used_words.update(group_words)
                            results.append({
                                "words": group_words,
                                "confidence": float(group.get('confidence', 0.8)),
                                "category": group.get('category', 'Unknown'),
                                "explanation": group.get('explanation', ''),
                                "method": "llm"
                            })
                return results
            else:
                raise Exception(f"Failed to parse JSON response: {str(e)}\nResponse: {content[:500]}")
        
    except openai.RateLimitError:
        raise Exception("OpenAI API rate limit exceeded. Please try again later.")
    except openai.AuthenticationError:
        raise Exception("Invalid OpenAI API key. Please check your API key.")
    except openai.APITimeoutError:
        raise Exception("OpenAI API request timed out. Please try again.")
    except openai.APIError as e:
        raise Exception(f"OpenAI API error: {str(e)}")
    except Exception as e:
        raise Exception(f"Error calling GPT-4: {str(e)}")


if __name__ == "__main__":
    """Test the solver"""
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Get API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Set it in .env.local file or export it:")
        print("  export OPENAI_API_KEY='your-key-here'")
        exit(1)
    
    # Test with sample words
    test_words = [
        "FAST", "FIRM", "SECURE", "TIGHT",
        "ACCOUNT", "CLIENT", "CONSUMER", "USER",
        "FROSTY", "MISTLETOE", "RAINMAKER", "SNOWMAN",
        "AUCTION", "MOVIE", "PARTNER", "TREATMENT"
    ]
    
    print("Testing GPT-4 solver with sample words...")
    print(f"Words: {test_words}\n")
    
    try:
        results = solve_with_llm(test_words, api_key)
        
        print(f"\n=== GPT-4 Solution ===")
        for i, result in enumerate(results, 1):
            print(f"\nGroup {i}:")
            print(f"  Words: {result['words']}")
            print(f"  Category: {result['category']}")
            print(f"  Confidence: {result['confidence']:.2f}")
            print(f"  Explanation: {result['explanation']}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

