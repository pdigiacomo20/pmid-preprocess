import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './EntriesBrowser.css';

interface Entry {
  pmid: string;
  filename: string;
  extraction_status: string;
  txt_available: boolean;
  pdf_available: boolean;
  original_reference: string;
  extracted_title: string;
  found_title: string;
  first_author: string;
  journal: string;
  year: string;
  doi: string;
  created_at: string;
}

const EntriesBrowser: React.FC = () => {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [filteredEntries, setFilteredEntries] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [contentFilter, setContentFilter] = useState('all');

  useEffect(() => {
    fetchEntries();
  }, []);

  useEffect(() => {
    filterEntries();
  }, [entries, searchQuery, statusFilter, contentFilter]);

  const fetchEntries = async () => {
    try {
      setLoading(true);
      const response = await axios.get('http://localhost:5000/api/entries');
      setEntries(response.data.entries || []);
      setError('');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to fetch entries');
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const filterEntries = () => {
    let filtered = [...entries];

    // Search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(entry =>
        (entry.extracted_title || '').toLowerCase().includes(query) ||
        (entry.found_title || '').toLowerCase().includes(query) ||
        (entry.first_author || '').toLowerCase().includes(query) ||
        (entry.pmid || '').toLowerCase().includes(query) ||
        (entry.journal || '').toLowerCase().includes(query)
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(entry => {
        switch (statusFilter) {
          case 'success':
            return entry.extraction_status === 'success';
          case 'failed':
            return entry.extraction_status !== 'success';
          default:
            return true;
        }
      });
    }

    // Content filter
    if (contentFilter !== 'all') {
      filtered = filtered.filter(entry => {
        switch (contentFilter) {
          case 'txt':
            return entry.txt_available;
          case 'pdf':
            return entry.pdf_available;
          case 'both':
            return entry.txt_available && entry.pdf_available;
          case 'none':
            return !entry.txt_available && !entry.pdf_available;
          default:
            return true;
        }
      });
    }

    setFilteredEntries(filtered);
  };

  const handleRefresh = () => {
    fetchEntries();
  };

  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  const getStatusBadge = (status: string) => {
    const className = status === 'success' ? 'badge-success' : 'badge-error';
    return <span className={`status-badge ${className}`}>{status}</span>;
  };

  const getContentBadges = (entry: Entry) => {
    const badges = [];
    if (entry.txt_available) {
      badges.push(<span key="txt" className="content-badge txt">TXT</span>);
    }
    if (entry.pdf_available) {
      badges.push(<span key="pdf" className="content-badge pdf">PDF</span>);
    }
    if (badges.length === 0) {
      badges.push(<span key="none" className="content-badge none">No Content</span>);
    }
    return badges;
  };

  if (loading) {
    return (
      <div className="entries-browser">
        <div className="loading">
          <div className="spinner"></div>
          <p>Loading entries...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="entries-browser">
      <div className="header">
        <h2>Browse Entries</h2>
        <button onClick={handleRefresh} className="refresh-button">
          Refresh
        </button>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      <div className="filters">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search by title, author, PMID, or journal..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>
        
        <div className="filter-controls">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Status</option>
            <option value="success">Success Only</option>
            <option value="failed">Failed Only</option>
          </select>

          <select
            value={contentFilter}
            onChange={(e) => setContentFilter(e.target.value)}
            className="filter-select"
          >
            <option value="all">All Content</option>
            <option value="txt">Has TXT</option>
            <option value="pdf">Has PDF</option>
            <option value="both">Has Both</option>
            <option value="none">No Content</option>
          </select>
        </div>
      </div>

      <div className="results-summary">
        <p>
          Showing {filteredEntries.length} of {entries.length} entries
        </p>
      </div>

      {filteredEntries.length === 0 ? (
        <div className="no-results">
          {entries.length === 0 ? (
            <p>No entries found. Process some references to get started!</p>
          ) : (
            <p>No entries match your current filters.</p>
          )}
        </div>
      ) : (
        <div className="entries-table">
          <div className="table-header">
            <div className="col-pmid">PMID</div>
            <div className="col-title">Title</div>
            <div className="col-author">Author</div>
            <div className="col-journal">Journal</div>
            <div className="col-year">Year</div>
            <div className="col-status">Status</div>
            <div className="col-content">Content</div>
            <div className="col-date">Date Added</div>
          </div>
          
          {filteredEntries.map((entry, index) => (
            <div key={entry.pmid || index} className="table-row">
              <div className="col-pmid">
                {entry.pmid ? (
                  <a
                    href={`https://pubmed.ncbi.nlm.nih.gov/${entry.pmid}/`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="pmid-link"
                  >
                    {entry.pmid}
                  </a>
                ) : (
                  'N/A'
                )}
              </div>
              
              <div className="col-title">
                <div className="title-container">
                  {entry.found_title && (
                    <div className="found-title" title="Title found in PubMed">
                      {entry.found_title}
                    </div>
                  )}
                  {entry.extracted_title && entry.extracted_title !== entry.found_title && (
                    <div className="extracted-title" title="Title extracted from reference">
                      Original: {entry.extracted_title}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="col-author">{entry.first_author || 'N/A'}</div>
              <div className="col-journal">{entry.journal || 'N/A'}</div>
              <div className="col-year">{entry.year || 'N/A'}</div>
              <div className="col-status">{getStatusBadge(entry.extraction_status)}</div>
              <div className="col-content">{getContentBadges(entry)}</div>
              <div className="col-date">{formatDate(entry.created_at)}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default EntriesBrowser;