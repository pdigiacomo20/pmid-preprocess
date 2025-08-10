import requests
import time
import os
from typing import Optional, Dict
import logging
from urllib.parse import urljoin
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class ContentDownloader:
    def __init__(self):
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
        self.pmc_base_url = "https://www.ncbi.nlm.nih.gov/pmc/"
        self.last_request_time = 0
        self.rate_limit_delay = 0.34  # Just over 1/3 second to ensure max 3 requests per second
        
        # Create directories if they don't exist
        self.txt_dir = os.path.join(os.path.dirname(__file__), '..', 'corpus', 'txt')
        self.pdf_dir = os.path.join(os.path.dirname(__file__), '..', 'corpus', 'pdf')
        os.makedirs(self.txt_dir, exist_ok=True)
        os.makedirs(self.pdf_dir, exist_ok=True)
    
    def _rate_limit(self):
        """Ensure we don't exceed 3 requests per second as per PubMed guidelines."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def download_fulltext(self, pmid: str, filename: str) -> bool:
        """
        Attempt to download full text for a given PMID.
        Returns True if successful, False otherwise.
        """
        try:
            # Check if PMC ID is available for this PMID
            pmc_id = self._get_pmc_id(pmid)
            if not pmc_id:
                logger.info(f"No PMC ID found for PMID {pmid}")
                return False
            
            # Try to get full text from PMC
            full_text = self._download_pmc_fulltext(pmc_id)
            if not full_text:
                logger.info(f"Could not download full text for PMC {pmc_id}")
                return False
            
            # Save to file
            txt_path = os.path.join(self.txt_dir, f"{filename}.txt")
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            
            logger.info(f"Successfully downloaded full text for PMID {pmid} to {txt_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading full text for PMID {pmid}: {str(e)}")
            return False
    
    def download_pdf(self, pmid: str, filename: str) -> bool:
        """
        Attempt to download PDF for a given PMID.
        Returns True if successful, False otherwise.
        """
        try:
            # Check if PMC ID is available for this PMID
            pmc_id = self._get_pmc_id(pmid)
            if not pmc_id:
                logger.info(f"No PMC ID found for PMID {pmid}")
                return False
            
            # Try to download PDF from PMC
            pdf_content = self._download_pmc_pdf(pmc_id)
            if not pdf_content:
                logger.info(f"Could not download PDF for PMC {pmc_id}")
                return False
            
            # Save to file
            pdf_path = os.path.join(self.pdf_dir, f"{filename}.pdf")
            with open(pdf_path, 'wb') as f:
                f.write(pdf_content)
            
            logger.info(f"Successfully downloaded PDF for PMID {pmid} to {pdf_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading PDF for PMID {pmid}: {str(e)}")
            return False
    
    def _get_pmc_id(self, pmid: str) -> Optional[str]:
        """
        Get PMC ID for a given PMID using elink.
        """
        self._rate_limit()
        
        link_url = f"{self.base_url}elink.fcgi"
        params = {
            'dbfrom': 'pubmed',
            'db': 'pmc',
            'id': pmid,
            'retmode': 'xml'
        }
        
        try:
            response = requests.get(link_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Parse XML response
            root = ET.fromstring(response.content)
            
            # Look for PMC links
            for link_set in root.findall('.//LinkSet'):
                for link_set_db in link_set.findall('LinkSetDb'):
                    db_to = link_set_db.find('DbTo')
                    if db_to is not None and db_to.text == 'pmc':
                        for link in link_set_db.findall('Link/Id'):
                            pmc_id = link.text
                            logger.info(f"Found PMC ID {pmc_id} for PMID {pmid}")
                            return pmc_id
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Request error getting PMC ID for PMID {pmid}: {str(e)}")
            return None
        except ET.ParseError as e:
            logger.error(f"XML parsing error getting PMC ID for PMID {pmid}: {str(e)}")
            return None
    
    def _download_pmc_fulltext(self, pmc_id: str) -> Optional[str]:
        """
        Download full text content from PMC.
        """
        self._rate_limit()
        
        # Try to get full text XML from PMC
        fetch_url = f"{self.base_url}efetch.fcgi"
        params = {
            'db': 'pmc',
            'id': pmc_id,
            'retmode': 'xml'
        }
        
        try:
            response = requests.get(fetch_url, params=params, timeout=60)
            response.raise_for_status()
            
            # Parse XML and extract text content
            root = ET.fromstring(response.content)
            
            # Extract text from various elements
            text_parts = []
            
            # Title
            title_elem = root.find('.//article-title')
            if title_elem is not None:
                text_parts.append(f"TITLE: {title_elem.text or ''}")
            
            # Abstract
            for abstract in root.findall('.//abstract'):
                abstract_text = self._extract_text_from_element(abstract)
                if abstract_text:
                    text_parts.append(f"ABSTRACT: {abstract_text}")
            
            # Body sections
            for sec in root.findall('.//body//sec'):
                sec_text = self._extract_text_from_element(sec)
                if sec_text:
                    # Get section title if available
                    title_elem = sec.find('title')
                    section_title = title_elem.text if title_elem is not None else "SECTION"
                    text_parts.append(f"{section_title.upper()}: {sec_text}")
            
            # Combine all text parts
            full_text = '\n\n'.join(text_parts)
            
            if len(full_text.strip()) < 100:  # Too short, probably not full text
                return None
            
            return full_text
            
        except requests.RequestException as e:
            logger.error(f"Request error downloading full text for PMC {pmc_id}: {str(e)}")
            return None
        except ET.ParseError as e:
            logger.error(f"XML parsing error for PMC {pmc_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading full text for PMC {pmc_id}: {str(e)}")
            return None
    
    def _download_pmc_pdf(self, pmc_id: str) -> Optional[bytes]:
        """
        Attempt to download PDF from PMC.
        Note: PDF availability is limited and may require special access.
        """
        self._rate_limit()
        
        # PMC PDF URLs typically follow this pattern
        pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/"
        
        try:
            response = requests.get(pdf_url, timeout=60, stream=True)
            
            # Check if we got a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' in content_type and response.status_code == 200:
                return response.content
            else:
                # Try alternative URL pattern
                alt_pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/main.pdf"
                alt_response = requests.get(alt_pdf_url, timeout=60)
                
                if alt_response.status_code == 200:
                    alt_content_type = alt_response.headers.get('content-type', '').lower()
                    if 'pdf' in alt_content_type:
                        return alt_response.content
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Request error downloading PDF for PMC {pmc_id}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading PDF for PMC {pmc_id}: {str(e)}")
            return None
    
    def _extract_text_from_element(self, element) -> str:
        """
        Recursively extract text content from an XML element.
        """
        text_parts = []
        
        if element.text:
            text_parts.append(element.text)
        
        for child in element:
            child_text = self._extract_text_from_element(child)
            if child_text:
                text_parts.append(child_text)
            if child.tail:
                text_parts.append(child.tail)
        
        return ' '.join(text_parts).strip()