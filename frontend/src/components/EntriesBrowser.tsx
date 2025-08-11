import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './EntriesBrowser.css';
import ContentModal from './ContentModal';
import ConfirmDialog from './ConfirmDialog';

interface Entry {
  pmid: string;
  filename: string;
  extraction_status: string;
  txt_available: boolean;
  pdf_available: boolean;
  ref_available: boolean;
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
  const [modalOpen, setModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState('');
  const [modalTitle, setModalTitle] = useState('');
  const [modalContentType, setModalContentType] = useState<'txt' | 'pdf' | 'ref'>('txt');
  const [modalLoading, setModalLoading] = useState(false);
  const [modalError, setModalError] = useState('');
  const [confirmDialogOpen, setConfirmDialogOpen] = useState(false);
  const [entryToDelete, setEntryToDelete] = useState<Entry | null>(null);

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
    if (entry.ref_available) {
      badges.push(<span key="ref" className="content-badge ref">REF</span>);
    }
    if (badges.length === 0) {
      badges.push(<span key="none" className="content-badge none">No Content</span>);
    }
    return badges;
  };

  const handleViewTxt = async (entry: Entry) => {
    if (!entry.txt_available || !entry.pmid) return;
    
    setModalOpen(true);
    setModalTitle(`${entry.found_title || entry.extracted_title || 'Unknown Title'} - Full Text`);
    setModalContentType('txt');
    setModalLoading(true);
    setModalError('');
    setModalContent('');
    
    try {
      const response = await axios.get(`http://localhost:5000/api/content/txt/${entry.pmid}`);
      setModalContent(response.data.content);
    } catch (err: any) {
      setModalError(err.response?.data?.error || 'Failed to load content');
    } finally {
      setModalLoading(false);
    }
  };

  const handleViewPdf = async (entry: Entry) => {
    if (!entry.pdf_available || !entry.pmid) return;
    
    try {
      const url = `http://localhost:5000/api/content/pdf/${entry.pmid}`;
      window.open(url, '_blank');
    } catch (err: any) {
      alert('Failed to open PDF: ' + (err.response?.data?.error || 'Unknown error'));
    }
  };

  const handleViewRef = async (entry: Entry) => {
    if (!entry.ref_available || !entry.pmid) return;
    
    setModalOpen(true);
    setModalTitle(`${entry.found_title || entry.extracted_title || 'Unknown Title'} - References`);
    setModalContentType('ref');
    setModalLoading(true);
    setModalError('');
    setModalContent('');
    
    try {
      const response = await axios.get(`http://localhost:5000/api/content/ref/${entry.pmid}`);
      setModalContent(response.data.content);
    } catch (err: any) {
      setModalError(err.response?.data?.error || 'Failed to load references');
    } finally {
      setModalLoading(false);
    }
  };

  const closeModal = () => {
    setModalOpen(false);
    setModalContent('');
    setModalError('');
    setModalTitle('');
  };

  const handleDeleteClick = (entry: Entry) => {
    setEntryToDelete(entry);
    setConfirmDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (!entryToDelete) return;
    
    try {
      if (entryToDelete.pmid) {
        // Delete by PMID for successful entries
        await axios.delete(`http://localhost:5000/api/entries/${entryToDelete.pmid}`);
      } else {
        // Delete by timestamp for failed entries
        await axios.delete('http://localhost:5000/api/entries/delete-by-timestamp', {
          data: { created_at: entryToDelete.created_at }
        });
      }
      
      // Refresh the entries list
      await fetchEntries();
      setConfirmDialogOpen(false);
      setEntryToDelete(null);
    } catch (err: any) {
      alert('Failed to delete entry: ' + (err.response?.data?.error || 'Unknown error'));
    }
  };

  const cancelDelete = () => {
    setConfirmDialogOpen(false);
    setEntryToDelete(null);
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
            <div className="col-actions">Actions</div>
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
              <div className="col-actions">
                <div className="action-buttons">
                  {entry.txt_available && (
                    <button
                      className="action-btn view-txt"
                      onClick={() => handleViewTxt(entry)}
                      title="View full text"
                    >
                      View TXT
                    </button>
                  )}
                  {entry.pdf_available && (
                    <button
                      className="action-btn view-pdf"
                      onClick={() => handleViewPdf(entry)}
                      title="View PDF"
                    >
                      View PDF
                    </button>
                  )}
                  {entry.ref_available && (
                    <button
                      className="action-btn view-ref"
                      onClick={() => handleViewRef(entry)}
                      title="View References"
                    >
                      View REF
                    </button>
                  )}
                  {!entry.txt_available && !entry.pdf_available && !entry.ref_available && (
                    <span className="no-content">No content available</span>
                  )}
                  <button
                    className="action-btn delete-btn"
                    onClick={() => handleDeleteClick(entry)}
                    title="Delete entry"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
      
      <ContentModal
        isOpen={modalOpen}
        onClose={closeModal}
        title={modalTitle}
        content={modalContent}
        contentType={modalContentType}
        loading={modalLoading}
        error={modalError}
      />
      
      <ConfirmDialog
        isOpen={confirmDialogOpen}
        title="Delete Entry"
        message={`Are you sure you want to delete this entry? This will permanently remove "${entryToDelete?.found_title || entryToDelete?.extracted_title || 'this entry'}" and any associated files.`}
        onConfirm={confirmDelete}
        onCancel={cancelDelete}
        confirmText="Yes, Delete"
        cancelText="Cancel"
        isDestructive={true}
      />
    </div>
  );
};

export default EntriesBrowser;