# PMID Preprocessor

A tool for processing academic reference sections to extract PMIDs and download associated content from PubMed.

## Features

- **Reference Parsing**: Uses GPT-4o to extract article titles from reference text
- **PubMed Search**: Searches PubMed database for matching articles and retrieves PMIDs
- **Content Download**: Downloads full-text and PDF files when available through PMC
- **Web Interface**: React-based frontend for easy reference processing and browsing
- **Duplicate Detection**: Prevents reprocessing of existing PMIDs
- **Rate Limiting**: Respects PubMed's API rate limits (3 requests per second)

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- Node.js and npm
- OpenAI API key

### Backend Setup

#### Quick Setup (Recommended)
1. **Run the automated setup script:**
   ```bash
   ./setup.sh
   ```

#### Manual Setup
1. **Create and activate virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Python dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   ```bash
   cp example.env .env
   # Edit .env and add your OpenAI API key
   ```

4. **Test OpenAI connection:**
   ```bash
   python test_openai.py
   ```

5. **Run the Flask backend:**
   ```bash
   cd backend
   source ../venv/bin/activate
   source ../.env  # Load environment variables
   python app.py
   ```

   The backend will start on `http://localhost:5000`

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

   The frontend will start on `http://localhost:3000`

## Usage

### Processing References

1. Navigate to the main page
2. Paste your academic reference section in the text area
3. Click "Process References"
4. View processing results and download status

### Browsing Entries

1. Go to "Browse Entries" page
2. Search by title, author, or PMID
3. Filter by processing status or content availability
4. Click PMID links to view articles on PubMed

### Failed Extractions

1. Visit "Failed Extractions" page
2. Review references that couldn't be processed
3. See available metadata and troubleshooting tips

## File Structure

```
pmid-preprocess/
├── backend/
│   ├── app.py                    # Flask application
│   ├── reference_parser.py       # GPT-4o reference parsing
│   ├── pubmed_search.py          # PubMed API integration
│   ├── content_downloader.py     # Content download from PMC
│   └── database.py              # CSV database management
├── frontend/
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── ReferenceInput.tsx
│   │   │   ├── EntriesBrowser.tsx
│   │   │   └── FailedExtractions.tsx
│   │   └── App.tsx              # Main application
│   └── package.json
├── corpus/
│   ├── txt/                     # Downloaded text files
│   └── pdf/                     # Downloaded PDF files
├── venv/                        # Python virtual environment
├── entries.csv                  # Database of processed entries
├── requirements.txt
├── example.env
└── README.md
```

## API Endpoints

- `POST /api/process-references` - Process reference text
- `GET /api/entries` - Retrieve all entries (with optional search)
- `GET /api/entries/<pmid>` - Get specific entry by PMID
- `GET /api/failed-extractions` - Get failed processing attempts

## Technical Details

### PubMed Integration

- Uses NCBI E-utilities API for searching and fetching
- Implements proper rate limiting (3 requests per second)
- Searches using title fields for better precision
- Downloads full-text from PMC when available

### Reference Processing Pipeline

1. **Parse References**: Split reference section into individual references
2. **Extract Titles**: Use GPT-4o to extract article titles and author information
3. **Search PubMed**: Query PubMed API with extracted titles
4. **Match Articles**: Verify title similarity between search and results
5. **Download Content**: Attempt to download full-text and PDF from PMC
6. **Store Metadata**: Save processing results and metadata to CSV

### File Naming Convention

Downloaded files follow the pattern: `{FirstAuthor}_{PMID}.{ext}`
- Spaces in author names are replaced with dashes
- If no author is found, uses the first word from the reference

## Troubleshooting

### Common Issues

1. **OpenAI API Issues**: 
   - Make sure your `.env` file contains a valid `OPENAI_API_KEY`
   - Run `python test_openai.py` to test the connection
   - If you get `proxies` error, run `pip install --upgrade openai`

2. **PubMed Search Fails**: 
   - The system tries multiple search strategies automatically
   - Check that the article exists in PubMed by searching manually
   - Some newer articles might not be indexed yet

3. **Content Not Available**: Not all articles have freely available full-text through PMC

4. **Title Extraction Failed**: Complex reference formats may not parse correctly - ensure references follow standard academic format

### Error Messages

- **"Title Extraction Failed"**: GPT-4o couldn't extract a clear title
- **"PubMed Search Failed"**: No matching articles found in PubMed
- **"Content Download Failed"**: Article found but content not available

## Development

### Adding New Features

1. Backend changes go in the `backend/` directory
2. Frontend components go in `frontend/src/components/`
3. Update the database schema in `database.py` if needed
4. Add new API endpoints in `app.py`

### Testing

Test the complete workflow:
1. Start both backend and frontend servers
2. Process a sample reference section
3. Verify results in the entries browser
4. Check failed extractions page for any errors

## License

This project is for research and educational purposes.