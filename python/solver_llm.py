"""
NYT Connections Solver using GPT-4

Uses OpenAI GPT-4 with Chain of Thought prompting to solve puzzles.
"""

import json
import openai
from typing import List, Dict, Any, Optional
import time


def solve_with_llm(words: List[str], api_key: str) -> List[Dict[str, Any]]:
    """
    Solve NYT Connections puzzle using GPT-4.
    
    Args:
        words: List of 16 puzzle words
        api_key: OpenAI API key
        
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
    
    # System prompt explaining Connections rules
    system_prompt = """You are an expert at solving NYT Connections puzzles.

Rules:
- There are 4 groups of 4 words each (16 words total)
- Each group shares a common theme or connection
- Categories can be:
  * Semantic: Words that share a meaning (e.g., synonyms, related concepts)
  * Wordplay: Words that share a linguistic pattern (e.g., all start with same letter, all compound words)
  * Fill-in-blank: Words that complete a phrase (e.g., "SILENT ___")
  * Compounds: Words that can be combined with another word
- Difficulty levels: Yellow (easiest), Green, Blue, Purple (trickiest)
- Think step-by-step to identify the connections

Your task is to analyze the 16 words and identify the 4 groups of 4 words each.
For each group, provide:
1. The 4 words that belong together
2. The category/theme name
3. An explanation of why they're connected
4. Your confidence level (0.0-1.0) for this grouping

Return your response as a JSON array with 4 objects, one for each group."""

    # User prompt with the words
    user_prompt = f"""Analyze these 16 words and find the 4 groups of 4 words each:

{', '.join(words)}

Think step-by-step:
1. Look for obvious semantic connections (synonyms, related concepts)
2. Check for wordplay patterns (shared prefixes, suffixes, compound words)
3. Consider fill-in-blank patterns
4. Identify the trickiest connections last

Return a JSON object with a "groups" key containing an array of exactly 4 groups in this format:
{{
  "groups": [
    {{
      "words": ["WORD1", "WORD2", "WORD3", "WORD4"],
      "category": "CATEGORY_NAME",
      "explanation": "Why these words belong together",
      "confidence": 0.95
    }},
    ...
  ]
}}

Make sure all 16 words are used exactly once across the 4 groups."""

    try:
        print("Calling GPT-4 to solve puzzle...")
        
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
                temperature=0.3,  # Lower temperature for consistency
                response_format={"type": "json_object"},  # Request JSON output
                max_tokens=2000
            )
        except Exception as e:
            # Fallback to gpt-4 without JSON mode
            if "json_object" in str(e).lower() or "response_format" in str(e).lower():
                print("JSON mode not supported, using gpt-4 without JSON mode...")
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,  # Lower temperature for consistency
                    max_tokens=2000
                )
            else:
                raise
        
        # Extract the response content
        content = response.choices[0].message.content
        
        print("GPT-4 response received, parsing...")
        
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
                print(f"Warning: Expected 4 groups, got {len(results)}")
            
            if len(used_words) != 16:
                missing = set(words) - used_words
                print(f"Warning: Not all words used. Missing: {missing}")
            
            print(f"Successfully parsed {len(results)} groups from GPT-4")
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

