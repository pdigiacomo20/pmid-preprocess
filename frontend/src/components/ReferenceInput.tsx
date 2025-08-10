import React, { useState } from 'react';
import axios from 'axios';
import './ReferenceInput.css';

interface ProcessingResult {
  status: string;
  pmid?: string;
  filename?: string;
  txt_available?: boolean;
  pdf_available?: boolean;
  message?: string;
  step?: string;
  extracted_title?: string;
}

const ReferenceInput: React.FC = () => {
  const [referencesText, setReferencesText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<ProcessingResult[]>([]);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!referencesText.trim()) {
      setError('Please enter some references to process.');
      return;
    }

    setIsProcessing(true);
    setError('');
    setResults([]);

    try {
      const response = await axios.post('http://localhost:5000/api/process-references', {
        references: referencesText
      });

      setResults(response.data.results);
    } catch (err: any) {
      setError(err.response?.data?.error || 'An error occurred while processing references.');
      console.error('Processing error:', err);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleClear = () => {
    setReferencesText('');
    setResults([]);
    setError('');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return '#4CAF50';
      case 'duplicate': return '#FF9800';
      case 'failed': return '#F44336';
      case 'error': return '#F44336';
      default: return '#757575';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return '✓';
      case 'duplicate': return '⚠';
      case 'failed': return '✗';
      case 'error': return '⚠';
      default: return '?';
    }
  };

  return (
    <div className="reference-input">
      <h2>Process Academic References</h2>
      <p>Paste your reference section below. Each reference will be processed to extract article titles, search PubMed for PMIDs, and download available content.</p>
      
      <form onSubmit={handleSubmit}>
        <div className="input-group">
          <label htmlFor="references">References Section:</label>
          <textarea
            id="references"
            value={referencesText}
            onChange={(e) => setReferencesText(e.target.value)}
            placeholder="1. Author, A. B. (2023). Title of the article. Journal Name, 12(3), 456-789.
2. Smith, J. D., & Johnson, M. K. (2022). Another article title. Different Journal, 8(1), 123-145.
3. ..."
            rows={12}
            cols={80}
            disabled={isProcessing}
          />
        </div>
        
        <div className="button-group">
          <button type="submit" disabled={isProcessing || !referencesText.trim()}>
            {isProcessing ? 'Processing...' : 'Process References'}
          </button>
          <button type="button" onClick={handleClear} disabled={isProcessing}>
            Clear
          </button>
        </div>
      </form>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {isProcessing && (
        <div className="processing-indicator">
          <div className="spinner"></div>
          <p>Processing references... This may take a few minutes.</p>
        </div>
      )}

      {results.length > 0 && (
        <div className="results-section">
          <h3>Processing Results</h3>
          <div className="results-summary">
            <p>Processed {results.length} references:</p>
            <ul>
              <li>✓ Successful: {results.filter(r => r.status === 'success').length}</li>
              <li>⚠ Duplicates: {results.filter(r => r.status === 'duplicate').length}</li>
              <li>✗ Failed: {results.filter(r => r.status === 'failed' || r.status === 'error').length}</li>
            </ul>
          </div>
          
          <div className="results-list">
            {results.map((result, index) => (
              <div key={index} className="result-item" style={{ borderLeftColor: getStatusColor(result.status) }}>
                <div className="result-header">
                  <span className="result-icon" style={{ color: getStatusColor(result.status) }}>
                    {getStatusIcon(result.status)}
                  </span>
                  <span className="result-status">{result.status.toUpperCase()}</span>
                  {result.pmid && <span className="result-pmid">PMID: {result.pmid}</span>}
                </div>
                
                <div className="result-details">
                  {result.status === 'success' && (
                    <>
                      <p><strong>Filename:</strong> {result.filename}</p>
                      <p><strong>Content Downloaded:</strong></p>
                      <ul>
                        <li>Full Text: {result.txt_available ? '✓ Yes' : '✗ No'}</li>
                        <li>PDF: {result.pdf_available ? '✓ Yes' : '✗ No'}</li>
                      </ul>
                    </>
                  )}
                  
                  {result.status === 'duplicate' && (
                    <p><strong>Message:</strong> {result.message}</p>
                  )}
                  
                  {(result.status === 'failed' || result.status === 'error') && (
                    <>
                      {result.step && <p><strong>Failed at:</strong> {result.step}</p>}
                      {result.extracted_title && <p><strong>Extracted title:</strong> {result.extracted_title}</p>}
                      {result.message && <p><strong>Error:</strong> {result.message}</p>}
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default ReferenceInput;