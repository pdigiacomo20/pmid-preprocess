import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './FailedExtractions.css';

interface FailedEntry {
  pmid: string | null;
  filename: string | null;
  extraction_status: string;
  txt_available: boolean;
  pdf_available: boolean;
  original_reference: string;
  extracted_title: string | null;
  found_title: string | null;
  first_author: string;
  journal: string | null;
  year: string | null;
  doi: string | null;
  created_at: string;
}

const FailedExtractions: React.FC = () => {
  const [failedEntries, setFailedEntries] = useState<FailedEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());

  useEffect(() => {
    fetchFailedEntries();
  }, []);

  const fetchFailedEntries = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:5000/api/failed-extractions');
      setFailedEntries(response.data.entries || []);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch failed extractions');
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpanded = (index: number) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedItems(newExpanded);
  };

  const getFailureReason = (status: string): { reason: string; description: string } => {
    switch (status) {
      case 'title_extraction_failed':
        return {
          reason: 'Title Extraction Failed',
          description: 'Could not extract a clear article title from the reference text using GPT-4o.'
        };
      case 'pubmed_search_failed':
        return {
          reason: 'PubMed Search Failed',
          description: 'No matching articles were found in PubMed for the extracted title.'
        };
      case 'content_download_failed':
        return {
          reason: 'Content Download Failed',
          description: 'Article was found in PubMed but full-text or PDF content could not be downloaded.'
        };
      case 'parsing_error':
        return {
          reason: 'Reference Parsing Error',
          description: 'The reference text could not be properly parsed or processed.'
        };
      default:
        return {
          reason: 'Unknown Failure',
          description: 'The processing failed for an unknown reason.'
        };
    }
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  const truncateText = (text: string, maxLength: number) => {
    if (!text || text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  if (loading) {
    return (
      <div className="failed-extractions">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading failed extractions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="failed-extractions">
      <div className="header">
        <h2>Failed Extractions</h2>
        <button onClick={fetchFailedEntries} className="refresh-button">
          Refresh
        </button>
      </div>

      <div className="info-box">
        <p>
          This page shows references that could not be successfully processed. 
          You can review the available metadata and identify where the extraction process failed.
        </p>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {failedEntries.length === 0 ? (
        <div className="no-failures">
          <h3>🎉 No Failed Extractions!</h3>
          <p>All processed references have been successfully extracted.</p>
        </div>
      ) : (
        <div className="failures-summary">
          <h3>Summary</h3>
          <p>Found {failedEntries.length} failed extraction{failedEntries.length !== 1 ? 's' : ''}:</p>
          
          <div className="failure-stats">
            {Object.entries(
              failedEntries.reduce((acc, entry) => {
                acc[entry.extraction_status] = (acc[entry.extraction_status] || 0) + 1;
                return acc;
              }, {} as Record<string, number>)
            ).map(([status, count]) => (
              <div key={status} className="stat-item">
                <span className="stat-count">{count}</span>
                <span className="stat-label">{getFailureReason(status).reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {failedEntries.length > 0 && (
        <div className="failures-list">
          {failedEntries.map((entry, index) => {
            const isExpanded = expandedItems.has(index);
            const failureInfo = getFailureReason(entry.extraction_status);

            return (
              <div key={index} className="failure-item">
                <div className="failure-header" onClick={() => toggleExpanded(index)}>
                  <div className="failure-info">
                    <div className="failure-reason">
                      <span className="failure-icon">⚠</span>
                      {failureInfo.reason}
                    </div>
                    <div className="failure-date">
                      {formatDate(entry.created_at)}
                    </div>
                  </div>
                  <div className="expand-icon">
                    {isExpanded ? '▼' : '▶'}
                  </div>
                </div>

                <div className="failure-preview">
                  <div className="reference-preview">
                    <strong>Reference:</strong> {truncateText(entry.original_reference, 150)}
                  </div>
                  {entry.extracted_title && (
                    <div className="extracted-title-preview">
                      <strong>Extracted Title:</strong> {entry.extracted_title}
                    </div>
                  )}
                </div>

                {isExpanded && (
                  <div className="failure-details">
                    <div className="failure-description">
                      <h4>What went wrong:</h4>
                      <p>{failureInfo.description}</p>
                    </div>

                    <div className="metadata-section">
                      <h4>Available Metadata:</h4>
                      <div className="metadata-grid">
                        <div className="metadata-item">
                          <label>Original Reference:</label>
                          <div className="metadata-value reference-text">
                            {entry.original_reference}
                          </div>
                        </div>

                        {entry.extracted_title && (
                          <div className="metadata-item">
                            <label>Extracted Title:</label>
                            <div className="metadata-value">{entry.extracted_title}</div>
                          </div>
                        )}

                        {entry.first_author && (
                          <div className="metadata-item">
                            <label>First Author:</label>
                            <div className="metadata-value">{entry.first_author}</div>
                          </div>
                        )}

                        {entry.journal && (
                          <div className="metadata-item">
                            <label>Journal:</label>
                            <div className="metadata-value">{entry.journal}</div>
                          </div>
                        )}

                        {entry.year && (
                          <div className="metadata-item">
                            <label>Year:</label>
                            <div className="metadata-value">{entry.year}</div>
                          </div>
                        )}

                        {entry.doi && (
                          <div className="metadata-item">
                            <label>DOI:</label>
                            <div className="metadata-value">
                              <a href={`https://doi.org/${entry.doi}`} target="_blank" rel="noopener noreferrer">
                                {entry.doi}
                              </a>
                            </div>
                          </div>
                        )}

                        {entry.found_title && (
                          <div className="metadata-item">
                            <label>Found Title (PubMed):</label>
                            <div className="metadata-value">{entry.found_title}</div>
                          </div>
                        )}

                        {entry.pmid && (
                          <div className="metadata-item">
                            <label>PMID:</label>
                            <div className="metadata-value">
                              <a
                                href={`https://pubmed.ncbi.nlm.nih.gov/${entry.pmid}/`}
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                {entry.pmid}
                              </a>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="troubleshooting-section">
                      <h4>Troubleshooting Tips:</h4>
                      <ul>
                        <li>Check if the reference format is standard (author, title, journal, year)</li>
                        <li>Ensure the article title is clearly identifiable</li>
                        <li>Verify the article exists in PubMed database</li>
                        <li>Consider manually searching PubMed with different keywords</li>
                        {entry.extraction_status === 'pubmed_search_failed' && (
                          <li>Try simplifying the title or using key terms from the title</li>
                        )}
                      </ul>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default FailedExtractions;