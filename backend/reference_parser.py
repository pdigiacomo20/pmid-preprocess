import os
import re
import openai
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class ReferenceParser:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
    
    def parse_references(self, references_text: str) -> List[Dict]:
        """
        Parse a references section and extract individual references.
        Returns a list of dictionaries with extracted information.
        """
        try:
            # Split references by common patterns (numbers, new lines, etc.)
            individual_refs = self._split_references(references_text)
            
            parsed_refs = []
            for i, ref_text in enumerate(individual_refs):
                if ref_text.strip():
                    parsed_ref = self._parse_single_reference(ref_text.strip())
                    parsed_ref['original_text'] = ref_text.strip()
                    parsed_refs.append(parsed_ref)
            
            return parsed_refs
            
        except Exception as e:
            logger.error(f"Error parsing references: {str(e)}")
            raise
    
    def _split_references(self, text: str) -> List[str]:
        """Split references text into individual references."""
        # Common patterns for reference numbering
        patterns = [
            r'\n\d+\.\s+',  # 1. Reference
            r'\n\[\d+\]\s*',  # [1] Reference
            r'\n\(\d+\)\s*',  # (1) Reference
            r'\n\d+\)\s+',   # 1) Reference
        ]
        
        # Try each pattern to split references
        for pattern in patterns:
            if re.search(pattern, text):
                refs = re.split(pattern, text)
                # Remove empty strings and clean up
                refs = [ref.strip() for ref in refs if ref.strip()]
                if len(refs) > 1:  # Successfully split
                    return refs
        
        # If no pattern works, split by double newlines or return as single reference
        refs = text.split('\n\n')
        return [ref.strip() for ref in refs if ref.strip()]
    
    def _parse_single_reference(self, reference_text: str) -> Dict:
        """
        Use GPT-4o to extract information from a single reference.
        """
        try:
            prompt = f"""
Extract the following information from this academic reference:
1. Article title (the main title of the paper/article)
2. First author's last name (just the surname, handle spaces by replacing with dashes)
3. Journal name (if available)
4. Publication year (if available)

Reference: "{reference_text}"

Please respond in JSON format:
{{
    "title": "extracted title or null if not found",
    "first_author": "last name of first author or first word if no author",
    "journal": "journal name or null if not found",
    "year": "publication year or null if not found"
}}

Guidelines:
- If the first author's last name contains spaces, replace them with dashes
- If there's no identifiable author (like an organization), use the first significant word
- Focus on extracting the main article title, not book titles or chapter titles
- Return null for any field that cannot be reliably extracted
"""
            
            # Handle different OpenAI library versions
            try:
                # Check if we have the newer OpenAI client (v1.0+)
                if hasattr(openai, 'OpenAI'):
                    try:
                        client = openai.OpenAI(api_key=self.api_key)
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": "You are a precise academic reference parser. Extract information accurately and return valid JSON."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0,
                            max_tokens=500
                        )
                    except Exception as e:
                        if "proxies" in str(e).lower():
                            # Try without any extra parameters
                            client = openai.OpenAI()
                            response = client.chat.completions.create(
                                model="gpt-4o",
                                messages=[
                                    {"role": "system", "content": "You are a precise academic reference parser. Extract information accurately and return valid JSON."},
                                    {"role": "user", "content": prompt}
                                ],
                                temperature=0,
                                max_tokens=500
                            )
                        else:
                            raise e
                else:
                    # Legacy OpenAI library (pre-1.0)
                    openai.api_key = self.api_key
                    response = openai.ChatCompletion.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are a precise academic reference parser. Extract information accurately and return valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0,
                        max_tokens=500
                    )
            except Exception as e:
                logger.error(f"Failed to call OpenAI API: {str(e)}")
                raise ValueError(f"OpenAI API call failed: {str(e)}")
            
            content = response.choices[0].message.content.strip()
            
            # Parse JSON response
            import json
            try:
                extracted_data = json.loads(content)
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from response
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    extracted_data = json.loads(json_match.group())
                else:
                    raise ValueError("Could not parse JSON from GPT response")
            
            # Clean and validate the extracted data
            cleaned_data = {
                'title': extracted_data.get('title', '').strip() if extracted_data.get('title') else None,
                'first_author': self._clean_author_name(extracted_data.get('first_author', '')),
                'journal': extracted_data.get('journal', '').strip() if extracted_data.get('journal') else None,
                'year': extracted_data.get('year', '').strip() if extracted_data.get('year') else None
            }
            
            return cleaned_data
            
        except Exception as e:
            logger.error(f"Error parsing single reference with GPT: {str(e)}")
            # Return basic parsed data as fallback
            return {
                'title': self._extract_title_fallback(reference_text),
                'first_author': self._extract_author_fallback(reference_text),
                'journal': None,
                'year': self._extract_year_fallback(reference_text)
            }
    
    def _clean_author_name(self, author_name: str) -> str:
        """Clean and format author name."""
        if not author_name:
            return "Unknown"
        
        # Replace spaces with dashes and clean up
        cleaned = re.sub(r'\s+', '-', author_name.strip())
        # Remove any punctuation except dashes
        cleaned = re.sub(r'[^\w\-]', '', cleaned)
        
        return cleaned if cleaned else "Unknown"
    
    def _extract_title_fallback(self, text: str) -> str:
        """Fallback method to extract title using regex patterns."""
        # Common patterns for titles in quotes or after author names
        patterns = [
            r'"([^"]+)"',  # Title in quotes
            r'[A-Z][^.]*\.[^A-Z]*([A-Z][^.]*\.)',  # Pattern after author
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        
        # Return first meaningful phrase
        words = text.split()[:10]  # First 10 words
        return ' '.join(words).rstrip('.,;')
    
    def _extract_author_fallback(self, text: str) -> str:
        """Fallback method to extract first author."""
        # Look for surname patterns at the beginning
        words = text.split()
        if words:
            first_word = re.sub(r'[^\w\s]', '', words[0])
            return self._clean_author_name(first_word)
        return "Unknown"
    
    def _extract_year_fallback(self, text: str) -> str:
        """Fallback method to extract publication year."""
        # Look for 4-digit years
        year_match = re.search(r'\b(19\d{2}|20\d{2})\b', text)
        return year_match.group(1) if year_match else None