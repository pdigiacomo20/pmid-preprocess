#!/usr/bin/env python3

import os
import sys
sys.path.append('backend')

def test_imports():
    """Test all required imports."""
    print("🧪 Testing imports...")
    
    try:
        import openai
        print(f"✅ OpenAI version: {openai.__version__}")
        
        import re
        print("✅ re module imported")
        
        import requests
        print("✅ requests module imported")
        
        from reference_parser import ReferenceParser
        print("✅ ReferenceParser imported")
        
        from pubmed_search import PubMedSearcher
        print("✅ PubMedSearcher imported")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {str(e)}")
        return False

def test_pubmed_search():
    """Test PubMed search functionality."""
    print("\n🔍 Testing PubMed search...")
    
    try:
        from pubmed_search import PubMedSearcher
        searcher = PubMedSearcher()
        
        # Test the _extract_significant_words method
        test_title = "Risk of long COVID associated with delta versus omicron variants of SARS-CoV-2"
        words = searcher._extract_significant_words(test_title)
        print(f"✅ Significant words extracted: {words}")
        
        # Test building search strategies
        strategies = searcher._build_all_search_strategies(test_title)
        print(f"✅ Search strategies built: {len(strategies)} strategies")
        for i, strategy in enumerate(strategies[:3]):  # Show first 3
            print(f"   Strategy {i+1}: {strategy}")
        
        return True
    except Exception as e:
        print(f"❌ PubMed search error: {str(e)}")
        return False

def test_openai_client():
    """Test OpenAI client initialization."""
    print("\n🤖 Testing OpenAI client...")
    
    if not os.getenv('OPENAI_API_KEY'):
        print("⚠️  OPENAI_API_KEY not set, skipping OpenAI test")
        return True
    
    try:
        from reference_parser import ReferenceParser
        parser = ReferenceParser()
        print("✅ ReferenceParser initialized")
        
        # Test simple reference parsing
        test_ref = "Smith J. Test article title. Journal Name. 2023."
        result = parser._parse_single_reference(test_ref)
        print(f"✅ Reference parsed successfully: {result.get('title', 'No title')}")
        
        return True
    except Exception as e:
        print(f"❌ OpenAI error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Running diagnostic tests...\n")
    
    all_passed = True
    all_passed &= test_imports()
    all_passed &= test_pubmed_search()
    all_passed &= test_openai_client()
    
    print(f"\n{'🎉 All tests passed!' if all_passed else '❌ Some tests failed'}")
    sys.exit(0 if all_passed else 1)