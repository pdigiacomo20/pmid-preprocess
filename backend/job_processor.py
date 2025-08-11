import threading
import time
import logging
from typing import Dict, List
from datetime import datetime
from reference_parser import ReferenceParser
from pubmed_search import PubMedSearcher
from content_downloader import ContentDownloader
from database import DatabaseManager

logger = logging.getLogger(__name__)

class JobProcessor:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.reference_parser = ReferenceParser()
        self.pubmed_searcher = PubMedSearcher()
        self.content_downloader = ContentDownloader()
        self.processing_jobs = set()  # Track currently processing job IDs
        self.stop_event = threading.Event()
    
    def process_job_async(self, job_id: str):
        """Start processing a job in a background thread."""
        if job_id in self.processing_jobs:
            logger.warning(f"Job {job_id} is already being processed")
            return
        
        self.processing_jobs.add(job_id)
        thread = threading.Thread(target=self._process_job, args=(job_id,))
        thread.daemon = True
        thread.start()
        logger.info(f"Started background processing for job {job_id}")
    
    def _process_job(self, job_id: str):
        """Process a job in the background."""
        try:
            # Get job details
            job = self.db_manager.get_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            # Update status to processing
            self.db_manager.update_job_status(job_id, 'processing')
            
            # Parse references using GPT
            references_text = job['references_text']
            logger.info(f"Job {job_id}: Parsing references with GPT...")
            
            try:
                references = self.reference_parser.parse_references(references_text)
                logger.info(f"Job {job_id}: GPT parsed {len(references)} references")
            except Exception as e:
                logger.error(f"Job {job_id}: GPT parsing failed: {str(e)}")
                self.db_manager.update_job_status(job_id, 'failed')
                self.db_manager.add_job_result(
                    job_id, 0, 'error', 
                    error_message=f"GPT parsing failed: {str(e)}"
                )
                return
            
            # Process each reference
            completed_refs = 0
            failed_refs = 0
            
            for i, ref_data in enumerate(references):
                if self.stop_event.is_set():
                    logger.info(f"Job {job_id}: Processing stopped")
                    break
                
                logger.info(f"Job {job_id}: Processing reference {i+1}/{len(references)}")
                
                try:
                    result = self._process_single_reference(ref_data)
                    
                    if result['status'] == 'success':
                        completed_refs += 1
                        self.db_manager.add_job_result(
                            job_id, i, 'success', 
                            pmid=result.get('pmid'),
                            extracted_title=ref_data.get('title')
                        )
                    else:
                        failed_refs += 1
                        self.db_manager.add_job_result(
                            job_id, i, 'failed',
                            extracted_title=ref_data.get('title'),
                            error_message=result.get('message', 'Unknown error')
                        )
                        
                except Exception as e:
                    logger.error(f"Job {job_id}: Error processing reference {i+1}: {str(e)}")
                    failed_refs += 1
                    self.db_manager.add_job_result(
                        job_id, i, 'error',
                        extracted_title=ref_data.get('title'),
                        error_message=str(e)
                    )
                
                # Update job progress
                self.db_manager.update_job_status(
                    job_id, 'processing', 
                    completed_refs=completed_refs, 
                    failed_refs=failed_refs
                )
                
                # Brief pause to avoid overwhelming APIs
                time.sleep(0.1)
            
            # Mark job as completed
            final_status = 'completed' if completed_refs > 0 else 'failed'
            self.db_manager.update_job_status(
                job_id, final_status,
                completed_refs=completed_refs,
                failed_refs=failed_refs
            )
            
            logger.info(f"Job {job_id}: Completed with {completed_refs} successful, {failed_refs} failed")
            
        except Exception as e:
            logger.error(f"Job {job_id}: Critical error during processing: {str(e)}")
            self.db_manager.update_job_status(job_id, 'failed')
            
        finally:
            self.processing_jobs.discard(job_id)
    
    def _process_single_reference(self, ref_data: Dict) -> Dict:
        """Process a single reference (similar to existing process_single_reference)."""
        try:
            # Check for duplicate PMID
            if ref_data.get('pmid') and self.db_manager.pmid_exists(ref_data['pmid']):
                return {
                    'status': 'duplicate',
                    'pmid': ref_data['pmid'],
                    'message': 'PMID already exists in database'
                }
            
            # Search PubMed
            pubmed_result = self.pubmed_searcher.search_article(ref_data['title'])
            
            if not pubmed_result:
                # Save failed extraction
                self.db_manager.add_entry({
                    'pmid': None,
                    'filename': None,
                    'extraction_status': 'pubmed_search_failed',
                    'txt_available': False,
                    'pdf_available': False,
                    'ref_available': False,
                    'original_reference': ref_data['original_text'],
                    'extracted_title': ref_data['title'],
                    'found_title': None,
                    'first_author': ref_data.get('first_author', '')
                })
                return {
                    'status': 'failed',
                    'step': 'pubmed_search',
                    'message': f"PubMed search failed for: {ref_data['title']}"
                }
            
            # Download content if available
            pmid = pubmed_result['pmid']
            filename = f"{ref_data['first_author']}_{pmid}"
            
            txt_downloaded = self.content_downloader.download_fulltext(pmid, filename)
            pdf_downloaded = self.content_downloader.download_pdf(pmid, filename)
            ref_downloaded = self.content_downloader.download_references(pmid, filename)
            
            # Save to database
            entry_data = {
                'pmid': pmid,
                'filename': filename,
                'extraction_status': 'success',
                'txt_available': txt_downloaded,
                'pdf_available': pdf_downloaded,
                'ref_available': ref_downloaded,
                'original_reference': ref_data['original_text'],
                'extracted_title': ref_data['title'],
                'found_title': pubmed_result.get('title', ''),
                'first_author': ref_data.get('first_author', ''),
                'journal': pubmed_result.get('journal', ''),
                'year': pubmed_result.get('year', ''),
                'doi': pubmed_result.get('doi', '')
            }
            
            self.db_manager.add_entry(entry_data)
            
            return {
                'status': 'success',
                'pmid': pmid,
                'title': pubmed_result.get('title', ''),
                'txt_downloaded': txt_downloaded,
                'pdf_downloaded': pdf_downloaded,
                'ref_downloaded': ref_downloaded
            }
            
        except Exception as e:
            logger.error(f"Error processing single reference: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def stop_processing(self):
        """Signal all background threads to stop."""
        self.stop_event.set()
        logger.info("Signaled all job processors to stop")
    
    def get_processing_jobs(self) -> List[str]:
        """Get list of currently processing job IDs."""
        return list(self.processing_jobs)