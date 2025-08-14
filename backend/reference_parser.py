import os
import re
import openai
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ReferenceParser:
    def __init__(self, api_key=None):
        # Try to get API key from parameter or environment
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY must be provided as parameter or set as environment variable")
    
    def parse_references(self, references_text: str) -> List[Dict]:
        """
        Parse a references section and extract individual references using GPT.
        Returns a list of dictionaries with extracted information.
        """
        try:
            return self._parse_all_references_with_gpt(references_text)
            
        except Exception as e:
            logger.error(f"Error parsing references: {str(e)}")
            raise
    
    def _parse_all_references_with_gpt(self, references_text: str) -> List[Dict]:
        """
        Use GPT to identify, split, and extract all references in a single call.
        """
        try:
            prompt = f"""
You are tasked with parsing academic reference citations. Given a block of text containing multiple references, you need to:

1. Identify and separate individual references
2. Extract key information from each reference

Input text:
```
{references_text}
```

For each reference you find, extract:
- title: The main title of the paper/article
- first_author: The surname (last name) of the first author only
- journal: The journal name if available
- year: The publication year (4-digit number)

CRITICAL JSON FORMATTING RULES:
- ALL string values MUST be properly escaped for JSON
- Replace all " (double quotes) with \\" in string values
- Replace all \\ (backslashes) with \\\\ in string values  
- Replace all newlines with \\n in string values
- Remove or replace any control characters
- If any field cannot be determined, use null (not "null")
- References may be numbered (like "66 Author..." or "[1] Author...") - ignore these numbers
- The first author surname comes after any reference number
- Extract only the surname, not initials or first names
- Be careful not to confuse reference numbers with author names

Return ONLY a valid JSON array where each object represents one reference:

[
  {{
    "title": "extracted title or null",
    "first_author": "author surname or null", 
    "journal": "journal name or null",
    "year": "4-digit year or null",
    "original_text": "the original reference text as you found it"
  }},
  ...
]

CRITICAL: Return ONLY valid JSON with no additional text, explanations, or markdown formatting.
"""

            # Use modern OpenAI client
            client = openai.OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a precise academic reference parser. Return valid JSON arrays only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=2000  # Increased for multiple references
            )

            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            try:
                references_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.error(f"Initial JSON parsing failed: {e}")
                # Fallback: try to extract JSON from response
                json_match = re.search(r'\[.*\]', content, re.DOTALL)
                if json_match:
                    try:
                        references_data = json.loads(json_match.group())
                    except json.JSONDecodeError as e2:
                        logger.error(f"Extracted JSON parsing also failed: {e2}")
                        # Try to fix common JSON issues
                        json_content = json_match.group()
                        # Fix unescaped quotes and newlines
                        json_content = self._fix_json_content(json_content)
                        try:
                            references_data = json.loads(json_content)
                        except json.JSONDecodeError as e3:
                            logger.error(f"Fixed JSON parsing still failed: {e3}")
                            logger.error(f"Problematic content: {content[:1000]}...")
                            raise ValueError(f"Could not parse JSON from GPT response: {e3}")
                else:
                    logger.error(f"No JSON array found in content: {content[:500]}...")
                    raise ValueError("Could not find JSON array in GPT response")
            
            # Clean and validate the extracted data
            cleaned_refs = []
            for ref_data in references_data:
                cleaned_ref = {
                    'title': ref_data.get('title', '').strip() if ref_data.get('title') else None,
                    'first_author': self._clean_author_name(ref_data.get('first_author', '')),
                    'journal': ref_data.get('journal', '').strip() if ref_data.get('journal') else None,
                    'year': ref_data.get('year', '').strip() if ref_data.get('year') else None,
                    'original_text': ref_data.get('original_text', '').strip() if ref_data.get('original_text') else ''
                }
                cleaned_refs.append(cleaned_ref)
            
            return cleaned_refs
            
        except Exception as e:
            logger.error(f"Error parsing references with GPT: {str(e)}")
            # Fallback to old method if GPT fails
            return self._fallback_to_old_parsing(references_text)
    
    def _fix_json_content(self, json_content: str) -> str:
        """
        Fix common JSON parsing issues in GPT responses, particularly unescaped newlines.
        """
        try:
            # Remove any markdown code block markers
            json_content = re.sub(r'```json\s*|\s*```', '', json_content)
            
            # Remove any leading/trailing whitespace
            json_content = json_content.strip()
            
            # The main issue is unescaped newlines in string values
            # We need to fix these by escaping them properly
            
            # First, let's fix the most common issue: newlines in string values
            # Look for patterns like "key": "value with\nnewline"
            
            import json
            
            # Try a different approach: parse character by character and fix as we go
            fixed_content = ""
            in_string = False
            escape_next = False
            quote_char = None
            
            i = 0
            while i < len(json_content):
                char = json_content[i]
                
                if escape_next:
                    fixed_content += char
                    escape_next = False
                elif char == '\\':
                    fixed_content += char
                    escape_next = True
                elif char == '"' and not in_string:
                    # Starting a string
                    in_string = True
                    quote_char = char
                    fixed_content += char
                elif char == '"' and in_string:
                    # Ending a string
                    in_string = False
                    quote_char = None
                    fixed_content += char
                elif in_string and char == '\n':
                    # Found unescaped newline in string - fix it
                    fixed_content += '\\n'
                elif in_string and char == '\r':
                    # Found unescaped carriage return in string - fix it
                    fixed_content += '\\r'
                elif in_string and char == '\t':
                    # Found unescaped tab in string - fix it
                    fixed_content += '\\t'
                else:
                    fixed_content += char
                
                i += 1
            
            return fixed_content
            
        except Exception as e:
            logger.error(f"Error in _fix_json_content: {e}")
            return json_content

    def _fallback_to_old_parsing(self, references_text: str) -> List[Dict]:
        """Fallback method - returns empty list since old parsing is removed."""
        logger.error("GPT parsing failed and fallback is not available")
        return []

    def _clean_author_name(self, author_name: str) -> str:
        """Clean and format author name."""
        if not author_name:
            return "Unknown"
        
        # Replace spaces with dashes and clean up
        cleaned = re.sub(r'\s+', '-', author_name.strip())
        # Remove any punctuation except dashes
        cleaned = re.sub(r'[^\w\-]', '', cleaned)
        
        return cleaned if cleaned else "Unknown"