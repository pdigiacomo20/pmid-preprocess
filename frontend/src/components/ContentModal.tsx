import React from 'react';
import './ContentModal.css';

interface ContentModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  content: string;
  contentType: 'txt' | 'pdf' | 'ref';
  loading: boolean;
  error?: string;
}

const ContentModal: React.FC<ContentModalProps> = ({
  isOpen,
  onClose,
  title,
  content,
  contentType,
  loading,
  error
}) => {
  if (!isOpen) return null;

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-backdrop" onClick={handleBackdropClick}>
      <div className="modal-content">
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="close-button" onClick={onClose}>
            ×
          </button>
        </div>
        
        <div className="modal-body">
          {loading && (
            <div className="loading">
              <div className="spinner"></div>
              <p>Loading content...</p>
            </div>
          )}
          
          {error && (
            <div className="error-message">
              <strong>Error:</strong> {error}
            </div>
          )}
          
          {!loading && !error && content && (
            <div className="content-display">
              {contentType === 'txt' ? (
                <pre className="txt-content">{content}</pre>
              ) : contentType === 'ref' ? (
                <pre className="ref-content">{content}</pre>
              ) : (
                <div className="pdf-content">
                  <p>PDF content will be displayed in a new tab.</p>
                </div>
              )}
            </div>
          )}
        </div>
        
        <div className="modal-footer">
          <button onClick={onClose} className="close-modal-button">
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ContentModal;