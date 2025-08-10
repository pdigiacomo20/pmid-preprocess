#!/usr/bin/env python3

import os
import sys
sys.path.append('backend')

from reference_parser import ReferenceParser

def test_openai_connection():
    """Test if OpenAI client works correctly."""
    try:
        # Make sure OPENAI_API_KEY is set
        if not os.getenv('OPENAI_API_KEY'):
            print("❌ OPENAI_API_KEY environment variable not set")
            print("Please set it in your .env file and run: source .env")
            return False
        
        print("✅ OPENAI_API_KEY is set")
        
        # Test parser initialization
        parser = ReferenceParser()
        print("✅ ReferenceParser initialized successfully")
        
        # Test with a simple reference
        test_reference = """1. Smith J, Doe A. Risk of long COVID associated with delta versus omicron variants of SARS-CoV-2. Nature Medicine. 2023;15(2):123-134."""
        
        print(f"🔍 Testing with reference: {test_reference}")
        
        result = parser._parse_single_reference(test_reference)
        print(f"✅ Parsing successful:")
        print(f"   Title: {result.get('title')}")
        print(f"   Author: {result.get('first_author')}")
        print(f"   Journal: {result.get('journal')}")
        print(f"   Year: {result.get('year')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing OpenAI connection...")
    success = test_openai_connection()
    sys.exit(0 if success else 1)