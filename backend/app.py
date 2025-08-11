from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from reference_parser import ReferenceParser
from pubmed_search import PubMedSearcher
from content_downloader import ContentDownloader
from database import DatabaseManager
from job_processor import JobProcessor
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components
db_manager = DatabaseManager()
reference_parser = ReferenceParser()
pubmed_searcher = PubMedSearcher()
content_downloader = ContentDownloader()
job_processor = JobProcessor(db_manager)

@app.route('/api/process-references', methods=['POST'])
def process_references():
    """Create a new processing job for references."""
    try:
        data = request.get_json()
        references_text = data.get('references', '')
        
        if not references_text:
            return jsonify({'error': 'No references provided'}), 400
        
        # Quick parse to count references for job tracking
        try:
            references = reference_parser.parse_references(references_text)
            total_refs = len(references)
        except Exception as e:
            logger.error(f"Error parsing references for job creation: {str(e)}")
            return jsonify({'error': f'Failed to parse references: {str(e)}'}), 400
        
        # Create job
        job_id = db_manager.create_job(references_text, total_refs)
        
        # Start async processing
        job_processor.process_job_async(job_id)
        
        # Return job info immediately
        return jsonify({
            'job_id': job_id,
            'status': 'pending',
            'total_references': total_refs,
            'message': f'Job created with {total_refs} references'
        })
    
    except Exception as e:
        logger.error(f"Error creating processing job: {str(e)}")
        return jsonify({'error': str(e)}), 500

def process_single_reference(ref_data):
    try:
        # Check for duplicate PMID
        if ref_data.get('pmid') and db_manager.pmid_exists(ref_data['pmid']):
            return {
                'status': 'duplicate',
                'pmid': ref_data['pmid'],
                'message': 'PMID already exists in database'
            }
        
        # Search PubMed
        pubmed_result = pubmed_searcher.search_article(ref_data['title'])
        
        if not pubmed_result:
            # Save failed extraction
            db_manager.add_entry({
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
                'extracted_title': ref_data['title']
            }
        
        # Download content if available
        pmid = pubmed_result['pmid']
        filename = f"{ref_data['first_author']}_{pmid}"
        
        txt_downloaded = content_downloader.download_fulltext(pmid, filename)
        pdf_downloaded = content_downloader.download_pdf(pmid, filename)
        ref_downloaded = content_downloader.download_references(pmid, filename)
        
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
            'found_title': pubmed_result['title'],
            'first_author': ref_data['first_author']
        }
        
        db_manager.add_entry(entry_data)
        
        return {
            'status': 'success',
            'pmid': pmid,
            'filename': filename,
            'txt_available': txt_downloaded,
            'pdf_available': pdf_downloaded,
            'ref_available': ref_downloaded
        }
    
    except Exception as e:
        logger.error(f"Error processing reference: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }

@app.route('/api/entries', methods=['GET'])
def get_entries():
    try:
        search_query = request.args.get('search', '')
        entries = db_manager.search_entries(search_query)
        return jsonify({'entries': entries})
    
    except Exception as e:
        logger.error(f"Error retrieving entries: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries/<pmid>', methods=['GET'])
def get_entry(pmid):
    try:
        entry = db_manager.get_entry_by_pmid(pmid)
        if entry:
            return jsonify({'entry': entry})
        else:
            return jsonify({'error': 'Entry not found'}), 404
    
    except Exception as e:
        logger.error(f"Error retrieving entry: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/failed-extractions', methods=['GET'])
def get_failed_extractions():
    try:
        failed_entries = db_manager.get_failed_entries()
        return jsonify({'entries': failed_entries})
    
    except Exception as e:
        logger.error(f"Error retrieving failed extractions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/content/txt/<pmid>', methods=['GET'])
def get_txt_content(pmid):
    try:
        entry = db_manager.get_entry_by_pmid(pmid)
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        if not entry.get('txt_available'):
            return jsonify({'error': 'TXT file not available for this entry'}), 404
        
        filename = entry.get('filename')
        if not filename:
            return jsonify({'error': 'Filename not found'}), 404
        
        txt_path = os.path.join('corpus', 'txt', f'{filename}.txt')
        
        if not os.path.exists(txt_path):
            return jsonify({'error': 'TXT file not found on disk'}), 404
        
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({'content': content})
    
    except Exception as e:
        logger.error(f"Error retrieving TXT content: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/content/pdf/<pmid>', methods=['GET'])
def get_pdf_content(pmid):
    try:
        entry = db_manager.get_entry_by_pmid(pmid)
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        if not entry.get('pdf_available'):
            return jsonify({'error': 'PDF file not available for this entry'}), 404
        
        filename = entry.get('filename')
        if not filename:
            return jsonify({'error': 'Filename not found'}), 404
        
        pdf_path = os.path.join('corpus', 'pdf', f'{filename}.pdf')
        
        if not os.path.exists(pdf_path):
            return jsonify({'error': 'PDF file not found on disk'}), 404
        
        from flask import send_file
        return send_file(pdf_path, as_attachment=False, mimetype='application/pdf')
    
    except Exception as e:
        logger.error(f"Error retrieving PDF content: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/content/ref/<pmid>', methods=['GET'])
def get_ref_content(pmid):
    try:
        entry = db_manager.get_entry_by_pmid(pmid)
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        if not entry.get('ref_available'):
            return jsonify({'error': 'Reference file not available for this entry'}), 404
        
        filename = entry.get('filename')
        if not filename:
            return jsonify({'error': 'Filename not found'}), 404
        
        ref_path = os.path.join('corpus', 'references', f'{filename}_ref.txt')
        
        if not os.path.exists(ref_path):
            return jsonify({'error': 'Reference file not found on disk'}), 404
        
        with open(ref_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({'content': content})
    
    except Exception as e:
        logger.error(f"Error retrieving reference content: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries/<pmid>', methods=['DELETE'])
def delete_entry(pmid):
    try:
        entry = db_manager.get_entry_by_pmid(pmid)
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        # Delete associated files if they exist
        filename = entry.get('filename')
        if filename:
            txt_path = os.path.join('corpus', 'txt', f'{filename}.txt')
            pdf_path = os.path.join('corpus', 'pdf', f'{filename}.pdf')
            ref_path = os.path.join('corpus', 'references', f'{filename}_ref.txt')
            
            if os.path.exists(txt_path):
                os.remove(txt_path)
                logger.info(f"Deleted TXT file: {txt_path}")
            
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
                logger.info(f"Deleted PDF file: {pdf_path}")
            
            if os.path.exists(ref_path):
                os.remove(ref_path)
                logger.info(f"Deleted reference file: {ref_path}")
        
        # Delete entry from database
        success = db_manager.delete_entry_by_pmid(pmid)
        
        if success:
            return jsonify({'message': 'Entry deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete entry from database'}), 500
    
    except Exception as e:
        logger.error(f"Error deleting entry: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/entries/delete-by-timestamp', methods=['DELETE'])
def delete_entry_by_timestamp():
    try:
        data = request.get_json()
        created_at = data.get('created_at')
        
        if not created_at:
            return jsonify({'error': 'created_at timestamp required'}), 400
        
        # Delete entry from database by timestamp
        success = db_manager.delete_entry_by_timestamp(created_at)
        
        if success:
            return jsonify({'message': 'Entry deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete entry from database or entry not found'}), 500
    
    except Exception as e:
        logger.error(f"Error deleting entry by timestamp: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/fix-filenames', methods=['POST'])
def fix_filenames():
    try:
        success = db_manager.fix_filename_format()
        if success:
            return jsonify({'message': 'Filename format fixed successfully'}), 200
        else:
            return jsonify({'error': 'Failed to fix filename format'}), 500
    
    except Exception as e:
        logger.error(f"Error fixing filename format: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/extract-references', methods=['POST'])
def extract_references():
    try:
        # Get all entries that don't have references yet
        entries = db_manager.get_entries_without_references()
        extracted_count = 0
        
        for entry in entries:
            pmid = entry.get('pmid')
            filename = entry.get('filename')
            
            if pmid and filename:
                try:
                    ref_downloaded = content_downloader.download_references(str(pmid), filename)
                    if ref_downloaded:
                        # Update database to mark references as available
                        db_manager.update_ref_availability(str(pmid), True)
                        extracted_count += 1
                        logger.info(f"Extracted references for PMID {pmid}")
                    else:
                        # Mark as not available to avoid retrying
                        db_manager.update_ref_availability(str(pmid), False)
                except Exception as e:
                    logger.error(f"Error extracting references for PMID {pmid}: {str(e)}")
                    db_manager.update_ref_availability(str(pmid), False)
        
        return jsonify({
            'message': f'Reference extraction completed. Extracted references for {extracted_count} entries.',
            'extracted_count': extracted_count
        }), 200
    
    except Exception as e:
        logger.error(f"Error extracting references: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Job Management Endpoints

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """Get job status and progress."""
    try:
        job = db_manager.get_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Add progress percentage
        total_refs = job.get('total_refs', 0)
        completed_refs = job.get('completed_refs', 0)
        failed_refs = job.get('failed_refs', 0)
        
        if total_refs > 0:
            progress_percentage = ((completed_refs + failed_refs) / total_refs) * 100
        else:
            progress_percentage = 0
        
        job['progress_percentage'] = round(progress_percentage, 1)
        job['processed_refs'] = completed_refs + failed_refs
        
        return jsonify(job)
    
    except Exception as e:
        logger.error(f"Error getting job status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<job_id>/results', methods=['GET'])
def get_job_results(job_id):
    """Get results for a specific job."""
    try:
        # Check if job exists
        job = db_manager.get_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        results = db_manager.get_job_results(job_id)
        return jsonify({'results': results})
    
    except Exception as e:
        logger.error(f"Error getting job results: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def cancel_job(job_id):
    """Cancel a job (if still processing)."""
    try:
        job = db_manager.get_job(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Update job status to cancelled
        success = db_manager.update_job_status(job_id, 'cancelled')
        
        if success:
            return jsonify({'message': 'Job cancelled successfully'})
        else:
            return jsonify({'error': 'Failed to cancel job'}), 500
    
    except Exception as e:
        logger.error(f"Error cancelling job: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    """List recent jobs."""
    try:
        # This is a simple implementation - you could add pagination/filtering
        if not os.path.exists(db_manager.jobs_csv):
            return jsonify({'jobs': []})
        
        import pandas as pd
        jobs_df = pd.read_csv(db_manager.jobs_csv)
        
        # Sort by created_at descending, limit to recent jobs
        jobs_df = jobs_df.sort_values('created_at', ascending=False).head(20)
        
        jobs = []
        for _, row in jobs_df.iterrows():
            job = row.to_dict()
            # Replace NaN with None
            for key, value in job.items():
                if pd.isna(value):
                    job[key] = None
            jobs.append(job)
        
        return jsonify({'jobs': jobs})
    
    except Exception as e:
        logger.error(f"Error listing jobs: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)