import requests
import time
import xml.etree.ElementTree as ET
from typing import Dict, Optional, List
import logging
import urllib.parse
import re

logger = logging.getLogger(__name__)

class PubMedSearcher:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.last_request_time = 0
        self.rate_limit_delay = 0.34  # Just over 1/3 second to ensure max 3 requests per second
    
    def _rate_limit(self):
        """Ensure we don't exceed 3 requests per second as per PubMed guidelines."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def search_article(self, title: str, authors: str = None) -> Optional[Dict]:
        """
        Search PubMed for an article using title and optionally authors.
        Returns article information with PMID if found.
        """
        if not title:
            return None
        
        try:
            # Build all search query strategies
            search_strategies = self._build_all_search_strategies(title, authors)
            
            # Try each strategy until we find results
            for i, search_query in enumerate(search_strategies):
                logger.info(f"Trying search strategy {i+1}: {search_query}")
                
                search_results = self._search_pubmed(search_query)
                
                if search_results:
                    # Step 2: Get detailed information for the first result
                    pmid = search_results[0]
                    article_details = self._get_article_details(pmid)
                    
                    if article_details and self._is_good_match(title, article_details['title']):
                        logger.info(f"Found matching article with strategy {i+1}: PMID {pmid}")
                        return {
                            'pmid': pmid,
                            'title': article_details['title'],
                            'authors': article_details.get('authors', []),
                            'journal': article_details.get('journal', ''),
                            'year': article_details.get('year', ''),
                            'doi': article_details.get('doi', ''),
                            'abstract': article_details.get('abstract', '')
                        }
                    elif article_details:
                        logger.info(f"Found article but poor title match with strategy {i+1}: '{article_details['title']}'")
                else:
                    logger.info(f"No results with strategy {i+1}")
            
            logger.info(f"No matching articles found for title: {title}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching PubMed for title '{title}': {str(e)}")
            return None
    
    def _build_all_search_strategies(self, title: str, authors: str = None) -> List[str]:
        """Build all search strategies to try in order of preference."""
        title_clean = title.replace('"', '').replace(':', '').strip()
        
        strategies = []
        
        # Strategy 1: Exact title search (if long enough)
        if len(title_clean) > 10:
            strategies.append(f'"{title_clean}"[Title]')
        
        # Strategy 2: Title words without quotes (more flexible)
        strategies.append(f'{title_clean}[Title]')
        
        # Strategy 3: Significant words in title/abstract
        significant_words = self._extract_significant_words(title_clean)
        if len(significant_words) >= 3:
            word_query = ' AND '.join([f'{word}[Title/Abstract]' for word in significant_words])
            strategies.append(word_query)
        
        # Strategy 4: Key words only (top 5)
        if len(significant_words) >= 2:
            key_words = significant_words[:5]
            key_query = ' AND '.join(key_words)
            strategies.append(key_query)
        
        # Strategy 5: Simple keyword search
        strategies.append(title_clean)
        
        # Add author constraint to all strategies if provided
        if authors:
            author_clean = authors.replace(',', '').strip()
            strategies_with_author = [f'({query}) AND "{author_clean}"[Author]' for query in strategies]
            # Try with author first, then without
            return strategies_with_author + strategies
        
        return strategies
    
    
    def _extract_significant_words(self, title: str) -> list:
        """Extract significant words from title, removing common stop words."""
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 
            'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
        }
        
        words = re.findall(r'\b[a-zA-Z]{3,}\b', title.lower())
        significant = [word for word in words if word not in stop_words]
        return significant[:8]  # Limit to 8 most significant words
    
    def _search_pubmed(self, query: str, max_results: int = 5) -> List[str]:
        """
        Search PubMed and return list of PMIDs.
        """
        self._rate_limit()
        
        search_url = f"{self.base_url}esearch.fcgi"
        params = {
            'db': 'pubmed',
            'term': query,
            'retmax': max_results,
            'retmode': 'xml',
            'sort': 'relevance'
        }
        
        try:
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            pmids = []
            
            for id_elem in root.findall('.//Id'):
                pmids.append(id_elem.text)
            
            logger.info(f"Found {len(pmids)} PMIDs for query: {query}")
            return pmids
            
        except requests.RequestException as e:
            logger.error(f"Request error in PubMed search: {str(e)}")
            return []
        except ET.ParseError as e:
            logger.error(f"XML parsing error in PubMed search: {str(e)}")
            return []
    
    def _get_article_details(self, pmid: str) -> Optional[Dict]:
        """
        Get detailed article information using efetch.
        """
        self._rate_limit()
        
        fetch_url = f"{self.base_url}efetch.fcgi"
        params = {
            'db': 'pubmed',
            'id': pmid,
            'retmode': 'xml'
        }
        
        try:
            response = requests.get(fetch_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            article = root.find('.//PubmedArticle')
            
            if article is None:
                return None
            
            # Extract article details
            details = self._parse_article_xml(article)
            return details
            
        except requests.RequestException as e:
            logger.error(f"Request error fetching PMID {pmid}: {str(e)}")
            return None
        except ET.ParseError as e:
            logger.error(f"XML parsing error for PMID {pmid}: {str(e)}")
            return None
    
    def _parse_article_xml(self, article_elem) -> Dict:
        """
        Parse article XML and extract relevant information.
        """
        details = {}
        
        try:
            # Title
            title_elem = article_elem.find('.//ArticleTitle')
            details['title'] = title_elem.text if title_elem is not None else ''
            
            # Authors
            authors = []
            for author in article_elem.findall('.//Author'):
                last_name = author.find('LastName')
                fore_name = author.find('ForeName')
                if last_name is not None:
                    full_name = last_name.text
                    if fore_name is not None:
                        full_name = f"{fore_name.text} {full_name}"
                    authors.append(full_name)
            details['authors'] = authors
            
            # Journal
            journal_elem = article_elem.find('.//Journal/Title')
            if journal_elem is None:
                journal_elem = article_elem.find('.//Journal/ISOAbbreviation')
            details['journal'] = journal_elem.text if journal_elem is not None else ''
            
            # Publication year
            year_elem = article_elem.find('.//PubDate/Year')
            if year_elem is None:
                year_elem = article_elem.find('.//PubDate/MedlineDate')
                if year_elem is not None:
                    # Extract year from MedlineDate (e.g., "2020 Jan-Feb")
                    import re
                    year_match = re.search(r'\d{4}', year_elem.text)
                    details['year'] = year_match.group() if year_match else ''
                else:
                    details['year'] = ''
            else:
                details['year'] = year_elem.text
            
            # DOI
            doi_elem = article_elem.find('.//ELocationID[@EIdType="doi"]')
            details['doi'] = doi_elem.text if doi_elem is not None else ''
            
            # Abstract
            abstract_elem = article_elem.find('.//Abstract/AbstractText')
            details['abstract'] = abstract_elem.text if abstract_elem is not None else ''
            
        except Exception as e:
            logger.error(f"Error parsing article XML: {str(e)}")
        
        return details
    
    def _is_good_match(self, search_title: str, found_title: str, threshold: float = 0.5) -> bool:
        """
        Check if the found article title is a good match for the search title.
        Uses simple word overlap scoring.
        """
        if not search_title or not found_title:
            return False
        
        # Convert to lowercase and split into words
        search_words = set(search_title.lower().split())
        found_words = set(found_title.lower().split())
        
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        search_words = search_words - stop_words
        found_words = found_words - stop_words
        
        if not search_words:
            return False
        
        # Calculate overlap ratio
        overlap = len(search_words.intersection(found_words))
        ratio = overlap / len(search_words)
        
        logger.info(f"Title match ratio: {ratio:.2f} for '{search_title}' vs '{found_title}'")
        return ratio >= threshold