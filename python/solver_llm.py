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
    
    # System prompt explaining Connections rules with detailed category types
    category_examples = """
CATEGORY TYPES (in order of difficulty):

YELLOW (Easiest - Direct semantic):
- Clear categorical relationships
- Example: "GARDENING TOOLS: rake, shovel, spade, hose"
- Example: "SYNONYMS FOR FAST: quick, rapid, speedy, swift"
- High semantic similarity, obvious connection

GREEN (Moderate - Thematic):
- Shared characteristics or themes
- Example: "THINGS THAT ARE RED: apple, rose, fire truck, tomato"
- Example: "WINTER WORDS: snow, ice, cold, frost"
- Medium semantic similarity, thematic grouping

BLUE (Tricky - Wordplay or fill-in-blank):
- Fill in the blank: "_____ ring: boxing, wedding, onion, earring"
- Compound words: Words that go before/after common word
- Example: "WORDS BEFORE 'BALL': basket, foot, snow, eye"
- Example: "WORDS AFTER 'FIRE': place, fighter, works, escape"
- Lower semantic similarity, pattern-based

PURPLE (Hardest - Obscure wordplay):
- Hidden patterns, homophones, word fragments
- Words split into parts: "JACK + AL = JACKAL"
- Rhymes, anagrams, or cultural references
- Example: "WORDS FORMED BY TWO MEN'S NAMES: Jackal (Jack+Al), Patron (Pat+Ron), Levitate (Levi+Tate), Melted (Mel+Ted)"
- Very low semantic similarity, requires wordplay analysis
"""

    system_prompt = f"""You are an expert at solving NYT Connections puzzles.

CRITICAL: Purple categories often use WORDPLAY, not just meaning:
- Names hidden in words (JACKAL = JACK + AL)
- Fill-in-blank patterns (___ button, ___ code)
- Homophones or rhymes
- Word fragments or compound words

For each word, ask:
1. Can it be split into two parts that are names/words?
2. Does it fit a ___ [WORD] or [WORD] ___ pattern?
3. Is there wordplay beyond literal meaning?

{category_examples}

Think step-by-step:
1. List all 16 words
2. Check each word for wordplay patterns FIRST (names, compounds, fill-in-blank)
3. Look for fill-in-blank patterns
4. Find name combinations (e.g., LEVITATE = LEVI + TATE)
5. Then find semantic groups
6. Rank by confidence (Purple is usually lowest confidence, Yellow highest)

CRITICAL RULES:
- There are EXACTLY 4 groups of 4 words each (16 words total)
- Each word is used EXACTLY ONCE across all 4 groups
- Each group shares a STRONG, CLEAR connection
- Be skeptical of weak connections - lower confidence if unsure
- Purple categories are often the trickiest - look for wordplay first!"""

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

Rules:
- Find exactly 4 groups
- Each group has exactly 4 words  
- Every word used exactly once
- Groups should have clear connections

Example of a tricky purple category:
Words: JACKAL, LEVITATE, MELTED, PATRON
Answer: "WORDS FORMED BY TWO MEN'S NAMES"
- JACKAL = JACK + AL
- LEVITATE = LEVI + TATE  
- MELTED = MEL + TED
- PATRON = PAT + RON

Think step-by-step:
1. Check for wordplay FIRST (names in words, fill-in-blank, compounds)
2. Find thematic connections (colors, tools, types of X)
3. Find semantic connections (synonyms, related concepts)
4. Verify: All 16 words used exactly once across 4 groups

Return JSON:
{{
  "reasoning": {{
    "wordplay_analysis": "Checked for name combinations, found: ...",
    "fill_in_blank_check": "Looked for ___ patterns, found: ...",
    "semantic_groups": "Found these thematic connections: ..."
  }},
  "groups": [
    {{
      "words": ["WORD1", "WORD2", "WORD3", "WORD4"],
      "category": "CATEGORY_NAME",
      "explanation": "Detailed explanation of why these words belong together",
      "confidence": 0.95
    }},
    {{
      "words": ["WORD5", "WORD6", "WORD7", "WORD8"],
      "category": "CATEGORY_NAME",
      "explanation": "...",
      "confidence": 0.90
    }},
    {{
      "words": ["WORD9", "WORD10", "WORD11", "WORD12"],
      "category": "CATEGORY_NAME",
      "explanation": "...",
      "confidence": 0.85
    }},
    {{
      "words": ["WORD13", "WORD14", "WORD15", "WORD16"],
      "category": "CATEGORY_NAME",
      "explanation": "...",
      "confidence": 0.80
    }}
  ]
}}

CRITICAL: 
- Return exactly 4 groups
- Use all 16 words exactly once
- Only use high confidence (0.8+) if you're very certain
- Purple categories usually have lower confidence (0.6-0.8)
- Yellow categories should have high confidence (0.85+)
- Be honest about uncertainty"""

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
            parsed = json.loads(content)
            
            # Handle different response formats
            if isinstance(parsed, dict):
                # If it's a dict, look for 'groups' or use the dict itself
                if 'groups' in parsed:
                    groups = parsed['groups']
                elif 'result' in parsed:
                    groups = parsed['result']
                else:
                    # Assume the dict contains the groups as values
                    groups = list(parsed.values()) if len(parsed) == 4 else [parsed]
            elif isinstance(parsed, list):
                groups = parsed
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
                if any(word in used_words for word in group_words):
                    continue
                
                used_words.update(group_words)
                
                # Extract other fields
                category = group.get('category', 'Unknown')
                explanation = group.get('explanation', 'No explanation provided')
                confidence = float(group.get('confidence', 0.8))
                
                # Clamp confidence to 0-1 range
                confidence = max(0.0, min(1.0, confidence))
                
                results.append({
                    "words": group_words,
                    "confidence": confidence,
                    "category": category,
                    "explanation": explanation,
                    "method": "llm"
                })
            
            # Validate we have exactly 4 groups and all words are used
            if len(results) != 4:
                print(f"Warning: Expected 4 groups, got {len(results)}", file=sys.stderr)
            
            if len(used_words) != 16:
                missing = set(words) - used_words
                print(f"Warning: Not all words used. Missing: {missing}", file=sys.stderr)
            
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

