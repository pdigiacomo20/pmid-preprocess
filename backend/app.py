from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from reference_parser import ReferenceParser
from pubmed_search import PubMedSearcher
from content_downloader import ContentDownloader
from database import DatabaseManager
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

@app.route('/api/process-references', methods=['POST'])
def process_references():
    try:
        data = request.get_json()
        references_text = data.get('references', '')
        
        if not references_text:
            return jsonify({'error': 'No references provided'}), 400
        
        # Parse references and process each one
        results = []
        references = reference_parser.parse_references(references_text)
        
        for ref_data in references:
            result = process_single_reference(ref_data)
            results.append(result)
        
        return jsonify({'results': results})
    
    except Exception as e:
        logger.error(f"Error processing references: {str(e)}")
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
        
        # Save to database
        entry_data = {
            'pmid': pmid,
            'filename': filename,
            'extraction_status': 'success',
            'txt_available': txt_downloaded,
            'pdf_available': pdf_downloaded,
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
            'pdf_available': pdf_downloaded
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)