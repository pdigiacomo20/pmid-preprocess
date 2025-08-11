import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './ReferenceInput.css';

interface Job {
  job_id: string;
  status: string;
  total_refs: number;
  completed_refs: number;
  failed_refs: number;
  progress_percentage: number;
  processed_refs: number;
  created_at: string;
  updated_at: string;
}

interface JobResult {
  job_id: string;
  reference_index: number;
  status: string;
  pmid?: string;
  extracted_title?: string;
  error_message?: string;
  processed_at: string;
}

const ReferenceInput: React.FC = () => {
  const [referencesText, setReferencesText] = useState('');
  const [currentJob, setCurrentJob] = useState<Job | null>(null);
  const [jobResults, setJobResults] = useState<JobResult[]>([]);
  const [error, setError] = useState('');
  const pollingInterval = useRef<NodeJS.Timeout | null>(null);

  // Clean up polling on component unmount
  useEffect(() => {
    return () => {
      if (pollingInterval.current) {
        clearInterval(pollingInterval.current);
      }
    };
  }, []);

  const startPolling = (jobId: string) => {
    // Clear any existing polling
    if (pollingInterval.current) {
      clearInterval(pollingInterval.current);
    }

    // Poll every 2 seconds
    pollingInterval.current = setInterval(async () => {
      try {
        const [jobResponse, resultsResponse] = await Promise.all([
          axios.get(`http://localhost:5000/api/jobs/${jobId}`),
          axios.get(`http://localhost:5000/api/jobs/${jobId}/results`)
        ]);

        const job = jobResponse.data;
        const results = resultsResponse.data.results;

        setCurrentJob(job);
        setJobResults(results);

        // Stop polling if job is completed
        if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
          if (pollingInterval.current) {
            clearInterval(pollingInterval.current);
            pollingInterval.current = null;
          }
        }
      } catch (err) {
        console.error('Error polling job status:', err);
      }
    }, 2000);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!referencesText.trim()) {
      setError('Please enter some references to process.');
      return;
    }

    setError('');
    setCurrentJob(null);
    setJobResults([]);

    try {
      const response = await axios.post('http://localhost:5000/api/process-references', {
        references: referencesText
      });

      const jobData = response.data;
      setCurrentJob({
        job_id: jobData.job_id,
        status: jobData.status,
        total_refs: jobData.total_references,
        completed_refs: 0,
        failed_refs: 0,
        progress_percentage: 0,
        processed_refs: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      });

      // Start polling for job status
      startPolling(jobData.job_id);

    } catch (err: any) {
      setError(err.response?.data?.error || 'An error occurred while creating processing job.');
      console.error('Job creation error:', err);
    }
  };

  const handleClear = () => {
    setReferencesText('');
    setCurrentJob(null);
    setJobResults([]);
    setError('');
    
    // Stop any active polling
    if (pollingInterval.current) {
      clearInterval(pollingInterval.current);
      pollingInterval.current = null;
    }
  };

  const handleCancelJob = async () => {
    if (!currentJob) return;

    try {
      await axios.delete(`http://localhost:5000/api/jobs/${currentJob.job_id}`);
      // Polling will automatically detect the cancelled status
    } catch (err: any) {
      console.error('Error cancelling job:', err);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success': return '#4CAF50';
      case 'duplicate': return '#FF9800';
      case 'failed': return '#F44336';
      case 'error': return '#F44336';
      case 'processing': return '#2196F3';
      case 'pending': return '#FF9800';
      case 'completed': return '#4CAF50';
      case 'cancelled': return '#757575';
      default: return '#757575';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return '✓';
      case 'duplicate': return '⚠';
      case 'failed': return '✗';
      case 'error': return '⚠';
      case 'processing': return '⏳';
      case 'pending': return '⏳';
      case 'completed': return '✓';
      case 'cancelled': return '⚪';
      default: return '?';
    }
  };

  const isJobActive = currentJob && (currentJob.status === 'pending' || currentJob.status === 'processing');

  return (
    <div className="reference-input">
      <h2>Process Academic References</h2>
      <p>Paste your reference section below. References will be processed asynchronously with real-time progress updates.</p>
      
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
            disabled={isJobActive}
          />
        </div>
        
        <div className="button-group">
          <button type="submit" disabled={isJobActive || !referencesText.trim()}>
            {isJobActive ? 'Processing...' : 'Process References'}
          </button>
          <button type="button" onClick={handleClear} disabled={isJobActive}>
            Clear
          </button>
          {isJobActive && (
            <button type="button" onClick={handleCancelJob} className="cancel-button">
              Cancel Job
            </button>
          )}
        </div>
      </form>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {currentJob && (
        <div className="job-status-section">
          <h3>Processing Status</h3>
          <div className="job-info">
            <div className="job-header">
              <span className="job-status" style={{ color: getStatusColor(currentJob.status) }}>
                {getStatusIcon(currentJob.status)} {currentJob.status.toUpperCase()}
              </span>
              <span className="job-id">Job ID: {currentJob.job_id.substring(0, 8)}...</span>
            </div>
            
            <div className="progress-section">
              <div className="progress-bar">
                <div 
                  className="progress-fill" 
                  style={{ 
                    width: `${currentJob.progress_percentage || 0}%`,
                    backgroundColor: getStatusColor(currentJob.status)
                  }}
                />
              </div>
              <div className="progress-text">
                {currentJob.status === 'processing' ? (
                  <span>Processing reference {currentJob.processed_refs} of {currentJob.total_refs}... ({currentJob.progress_percentage}%)</span>
                ) : currentJob.status === 'pending' ? (
                  <span>Starting job with {currentJob.total_refs} references...</span>
                ) : (
                  <span>
                    Completed: {currentJob.completed_refs} | Failed: {currentJob.failed_refs} | Total: {currentJob.total_refs}
                  </span>
                )}
              </div>
            </div>
          </div>

          {jobResults.length > 0 && (
            <div className="results-section">
              <h4>Results ({jobResults.length} processed)</h4>
              <div className="results-summary">
                <ul>
                  <li>✓ Successful: {jobResults.filter(r => r.status === 'success').length}</li>
                  <li>✗ Failed: {jobResults.filter(r => r.status === 'failed' || r.status === 'error').length}</li>
                </ul>
              </div>
              
              <div className="results-list">
                {jobResults.map((result) => (
                  <div key={result.reference_index} className="result-item" style={{ borderLeftColor: getStatusColor(result.status) }}>
                    <div className="result-header">
                      <span className="result-icon" style={{ color: getStatusColor(result.status) }}>
                        {getStatusIcon(result.status)}
                      </span>
                      <span className="result-status">#{result.reference_index + 1} - {result.status.toUpperCase()}</span>
                      {result.pmid && <span className="result-pmid">PMID: {result.pmid}</span>}
                    </div>
                    
                    <div className="result-details">
                      {result.extracted_title && (
                        <p><strong>Title:</strong> {result.extracted_title}</p>
                      )}
                      {result.error_message && (
                        <p><strong>Error:</strong> {result.error_message}</p>
                      )}
                      <p><strong>Processed:</strong> {new Date(result.processed_at).toLocaleTimeString()}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ReferenceInput;