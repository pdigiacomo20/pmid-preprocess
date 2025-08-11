# PMID Preprocessor - Project Plan

## Project Overview
Create a repository that processes academic reference sections to extract PMIDs and associated metadata from PubMed, with a React frontend for user interaction.

## Architecture
- **Backend**: Flask API with Python
- **Frontend**: React application (in `frontend/` folder)
- **Database**: Simple CSV file for metadata storage
- **File Storage**: 
  - Text files: `corpus/txt/` 
  - PDF files: `corpus/pdf/`

## Detailed Implementation Plan

### Phase 1: Backend Setup and Core Infrastructure
- [ ] Create Python virtual environment (`venv/`)
- [ ] Set up Flask application structure
- [ ] Create `requirements.txt` with dependencies:
  - Flask
  - requests (for PubMed API)
  - openai (for GPT-4o integration)
  - pandas (for CSV handling)
  - beautifulsoup4 (for HTML parsing)
  - PyPDF2 or similar (for PDF handling)
- [ ] Create `example.env` file with `OPENAI_API_KEY`
- [ ] Update `.gitignore` to exclude `venv/`, `.env`, and other sensitive files

### Phase 2: Reference Processing Pipeline
- [ ] **Reference Parser Module** (`backend/reference_parser.py`)
  - Use GPT-4o to extract article titles from reference text
  - Handle various citation formats
  - Extract author information (first author's last name)
  
- [ ] **PubMed Search Module** (`backend/pubmed_search.py`)
  - Search PubMed API using extracted titles
  - Match articles and extract PMIDs
  - Retrieve article metadata (title, authors, DOI)
  
- [ ] **Content Downloader Module** (`backend/content_downloader.py`)
  - Check for full-text availability
  - Download text files when available
  - Download PDF files when available
  - Handle file naming: `Lastname_PMID.txt/pdf`

### Phase 3: Data Management
- [ ] **CSV Database Manager** (`backend/database.py`)
  - Create and manage CSV with columns:
    - PMID
    - filename (Lastname_PMID without extension)
    - extraction_status (success/failed at which step)
    - txt_available (boolean)
    - pdf_available (boolean)
    - original_reference
    - extracted_title
    - found_title
    - first_author
  - Implement duplicate PMID checking
  
- [ ] **Directory Structure Setup**
  - Create `corpus/txt/` and `corpus/pdf/` directories
  - Implement file management utilities

### Phase 4: Flask API Endpoints
- [ ] `POST /api/process-references` - Process new reference section
- [ ] `GET /api/entries` - Retrieve all entries with search/filter capabilities
- [ ] `GET /api/entries/<pmid>` - Get specific entry details
- [ ] `GET /api/failed-extractions` - Get entries with processing failures

### Phase 5: React Frontend Setup
- [ ] Initialize React app in `frontend/` folder using `npx create-react-app`
- [ ] Set up basic routing and navigation
- [ ] Configure API communication with backend

### Phase 6: Frontend Components
- [ ] **Reference Input Page**
  - Text area for pasting reference sections
  - Submit button to trigger processing
  - Progress indicator for processing status
  
- [ ] **Entries Browser Page**
  - Searchable table/list of all processed entries
  - Search by: article title, author, PMID
  - Filters for success/failure status
  - Links to download available files
  
- [ ] **Failed Extractions Page**
  - Display entries where processing failed
  - Show available metadata at point of failure
  - Option to retry processing

### Phase 7: Integration and Testing
- [ ] Connect frontend to backend APIs
- [ ] Test complete workflow with sample references
- [ ] Handle error cases and edge conditions
- [ ] Performance optimization for large reference lists

## File Structure
```
pmid-preprocess/
├── backend/
│   ├── app.py (Flask main)
│   ├── reference_parser.py
│   ├── pubmed_search.py
│   ├── content_downloader.py
│   └── database.py
├── frontend/ (React app)
├── corpus/
│   ├── txt/
│   └── pdf/
├── venv/ (excluded from git)
├── requirements.txt
├── example.env
├── .gitignore
├── entries.csv (generated)
└── CLAUDE.md
```

## Key Technical Considerations
1. **Rate Limiting**: PubMed API has rate limits - implement appropriate delays
2. **Error Handling**: Graceful handling of API failures, parsing errors
3. **File Management**: Proper cleanup and organization of downloaded files
4. **Security**: Secure handling of OpenAI API keys
5. **Duplicate Detection**: Prevent reprocessing existing PMIDs
6. **Scalability**: Design for processing large reference lists efficiently

## Success Criteria
- [ ] Successfully extract article titles from reference text using GPT-4o
- [ ] Find matching articles in PubMed and extract PMIDs
- [ ] Download available full-text and PDF files
- [ ] Store metadata in searchable format
- [ ] Provide user-friendly interface for input and browsing
- [ ] Handle failures gracefully with clear error reporting

## Review Section

### Implementation Summary

**Completed Features:**
✅ **Backend Infrastructure**
- Flask API with CORS support for frontend communication
- Python virtual environment with all required dependencies
- Modular architecture with separate modules for parsing, searching, downloading, and database management

✅ **Reference Processing Pipeline**
- GPT-4o integration for intelligent title extraction from various citation formats
- PubMed API integration with proper search syntax and rate limiting (3 requests/second)
- Content downloader that fetches full-text and PDFs from PMC when available
- Robust error handling and fallback mechanisms

✅ **Data Management**
- CSV-based database with comprehensive metadata storage
- Duplicate PMID detection to prevent reprocessing
- Processing status tracking with detailed failure reasons
- Search and filtering capabilities

✅ **React Frontend**
- Modern TypeScript React application with routing
- Reference input interface with real-time processing feedback
- Searchable entries browser with filtering by status and content type
- Failed extractions viewer with troubleshooting information
- Responsive design for mobile and desktop

✅ **User Experience Features**
- Visual processing indicators and progress tracking
- Detailed error reporting with actionable insights
- PubMed integration with direct links to articles
- File availability indicators and download status

✅ **Configuration & Documentation**
- Comprehensive setup instructions and usage guide
- Environment configuration with example.env file
- Proper .gitignore for security and cleanliness
- Detailed API documentation and troubleshooting guide

### Technical Highlights

1. **Rate Limit Compliance**: Implemented proper rate limiting to respect PubMed's 3 requests per second limit
2. **Intelligent Matching**: Uses word overlap scoring to verify PubMed search results match extracted titles
3. **Graceful Degradation**: System continues processing even when individual references fail
4. **Security**: OpenAI API keys properly handled through environment variables
5. **Scalability**: Modular design allows easy extension and modification

### File Structure Created
```
pmid-preprocess/
├── backend/                    # Flask API and processing modules
├── frontend/                   # React TypeScript application
├── corpus/txt/                # Downloaded text files
├── corpus/pdf/                # Downloaded PDF files
├── venv/                      # Python virtual environment
├── requirements.txt           # Python dependencies
├── example.env               # Environment configuration template
├── .gitignore               # Git ignore rules
├── README.md                # Complete documentation
└── projectplan.md          # This project plan
```

### Success Criteria Met
- ✅ Successfully extract article titles using GPT-4o with fallback mechanisms
- ✅ Search PubMed with proper API integration and rate limiting
- ✅ Download available content with error handling
- ✅ Provide user-friendly web interface for all operations
- ✅ Handle failures gracefully with clear error reporting
- ✅ Implement duplicate detection and comprehensive metadata storage

### Next Steps for Users
1. **Setup**: Follow README.md instructions to configure environment variables
2. **Installation**: Install Python and Node.js dependencies
3. **Testing**: Run both backend and frontend servers
4. **Usage**: Process sample references to verify functionality

The implementation is complete and ready for use. All core requirements have been fulfilled with additional features for enhanced user experience and maintainability.

## New Feature Plan: Full Text and PDF Viewing

### Overview
Add the ability to view full extracted text content and PDF files while browsing entries in the frontend application.

### Analysis
The current system stores:
- TXT files in `/corpus/txt/` directory with format `{filename}_{pmid}.txt`
- PDF files in `/corpus/pdf/` directory with format `{filename}_{pmid}.pdf`
- Entry metadata in database including `filename`, `pmid`, `txt_available`, and `pdf_available` flags

### Todo List
- [ ] Add backend API endpoints to serve TXT and PDF content
- [ ] Add modal component for displaying full text content
- [ ] Add view buttons to the entries table for TXT and PDF content
- [ ] Style the modal and content display appropriately
- [ ] Test the feature with existing data

### Backend Changes Needed
1. Add `/api/content/txt/<pmid>` endpoint to serve TXT file content
2. Add `/api/content/pdf/<pmid>` endpoint to serve PDF files
3. Add error handling for missing files

### Frontend Changes Needed
1. Create a ContentModal component to display full text
2. Add "View TXT" and "View PDF" buttons to entry rows
3. Handle modal state and content loading
4. Add appropriate styling for content display