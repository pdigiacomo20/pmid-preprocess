import pandas as pd
import os
from typing import List, Dict, Optional
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, csv_file: str = None):
        if csv_file is None:
            # Default to entries.csv in the project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            csv_file = os.path.join(project_root, 'entries.csv')
        
        self.csv_file = csv_file
        
        # Job system CSV files
        project_root = os.path.dirname(os.path.dirname(__file__))
        self.jobs_csv = os.path.join(project_root, 'jobs.csv')
        self.job_results_csv = os.path.join(project_root, 'job_results.csv')
        self.columns = [
            'pmid',
            'filename',
            'extraction_status',
            'txt_available',
            'pdf_available',
            'ref_available',
            'original_reference',
            'extracted_title',
            'found_title',
            'first_author',
            'journal',
            'year',
            'doi',
            'created_at'
        ]
        
        # Initialize CSV file if it doesn't exist
        self._initialize_csv()
    
    def _initialize_csv(self):
        """Create CSV file with headers if it doesn't exist."""
        if not os.path.exists(self.csv_file):
            df = pd.DataFrame(columns=self.columns)
            df.to_csv(self.csv_file, index=False)
            logger.info(f"Created new CSV database at {self.csv_file}")
    
    def add_entry(self, entry_data: Dict) -> bool:
        """
        Add a new entry to the database.
        Returns True if successful, False otherwise.
        """
        try:
            # Read existing data
            df = pd.read_csv(self.csv_file)
            
            # Prepare entry data with all columns
            new_entry = {}
            for col in self.columns:
                if col == 'created_at':
                    import datetime
                    new_entry[col] = datetime.datetime.now().isoformat()
                else:
                    new_entry[col] = entry_data.get(col, None)
            
            # Add the new entry
            new_df = pd.DataFrame([new_entry])
            df = pd.concat([df, new_df], ignore_index=True)
            
            # Save back to CSV
            df.to_csv(self.csv_file, index=False)
            
            logger.info(f"Added entry for PMID: {entry_data.get('pmid', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding entry to database: {str(e)}")
            return False
    
    def pmid_exists(self, pmid: str) -> bool:
        """
        Check if a PMID already exists in the database.
        Returns True if exists, False otherwise.
        """
        try:
            if not pmid:
                return False
                
            df = pd.read_csv(self.csv_file)
            return pmid in df['pmid'].astype(str).values
            
        except Exception as e:
            logger.error(f"Error checking PMID existence: {str(e)}")
            return False
    
    def get_entry_by_pmid(self, pmid: str) -> Optional[Dict]:
        """
        Get a specific entry by PMID.
        Returns dictionary with entry data or None if not found.
        """
        try:
            df = pd.read_csv(self.csv_file)
            # Handle both integer and float PMIDs
            pmid_str = str(pmid)
            pmid_float_str = f"{float(pmid)}"
            
            matching_rows = df[(df['pmid'].astype(str) == pmid_str) | 
                              (df['pmid'].astype(str) == pmid_float_str)]
            
            if matching_rows.empty:
                return None
            
            # Convert to dictionary and handle NaN values
            entry = matching_rows.iloc[0].to_dict()
            # Replace NaN with None for JSON serialization
            for key, value in entry.items():
                if pd.isna(value):
                    entry[key] = None
            
            return entry
            
        except Exception as e:
            logger.error(f"Error retrieving entry by PMID {pmid}: {str(e)}")
            return None
    
    def delete_entry_by_pmid(self, pmid: str) -> bool:
        """
        Delete an entry by PMID.
        Returns True if successful, False otherwise.
        """
        try:
            df = pd.read_csv(self.csv_file)
            initial_len = len(df)
            
            # Handle both integer and float PMIDs
            pmid_str = str(pmid)
            pmid_float_str = f"{float(pmid)}"
            
            # Remove matching rows
            df = df[~((df['pmid'].astype(str) == pmid_str) | 
                     (df['pmid'].astype(str) == pmid_float_str))]
            
            if len(df) == initial_len:
                logger.warning(f"No entry found with PMID {pmid} to delete")
                return False
            
            # Save updated dataframe
            df.to_csv(self.csv_file, index=False)
            logger.info(f"Deleted entry with PMID {pmid}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting entry by PMID {pmid}: {str(e)}")
            return False
    
    def delete_entry_by_timestamp(self, created_at: str) -> bool:
        """
        Delete an entry by its created_at timestamp.
        Returns True if successful, False otherwise.
        """
        try:
            df = pd.read_csv(self.csv_file)
            initial_len = len(df)
            
            # Remove matching rows by created_at
            df = df[df['created_at'] != created_at]
            
            if len(df) == initial_len:
                logger.warning(f"No entry found with created_at {created_at} to delete")
                return False
            
            # Save updated dataframe
            df.to_csv(self.csv_file, index=False)
            logger.info(f"Deleted entry with created_at {created_at}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting entry by created_at {created_at}: {str(e)}")
            return False
    
    def fix_filename_format(self) -> bool:
        """
        Fix filename format for entries that have numeric first_author values.
        Extract proper author names from original_reference.
        """
        try:
            df = pd.read_csv(self.csv_file)
            modified = False
            
            for index, row in df.iterrows():
                # Check if first_author is numeric
                first_author = str(row.get('first_author', ''))
                if first_author.isdigit():
                    # Extract author from original_reference
                    original_ref = str(row.get('original_reference', ''))
                    if original_ref and original_ref != 'nan':
                        # Pattern to find author name after number
                        import re
                        match = re.search(r'\d+\s+([A-Z][a-z]+)', original_ref)
                        if match:
                            author_name = match.group(1)
                            pmid = row.get('pmid')
                            
                            # Update first_author and filename
                            df.at[index, 'first_author'] = author_name
                            if pmid and not pd.isna(pmid):
                                new_filename = f"{author_name}_{int(float(pmid))}"
                                df.at[index, 'filename'] = new_filename
                                
                                # Rename actual files if they exist
                                old_filename = row.get('filename', '')
                                if old_filename:
                                    old_txt = os.path.join('corpus', 'txt', f'{old_filename}.txt')
                                    new_txt = os.path.join('corpus', 'txt', f'{new_filename}.txt')
                                    old_pdf = os.path.join('corpus', 'pdf', f'{old_filename}.pdf')
                                    new_pdf = os.path.join('corpus', 'pdf', f'{new_filename}.pdf')
                                    
                                    if os.path.exists(old_txt):
                                        os.rename(old_txt, new_txt)
                                        logger.info(f"Renamed {old_txt} to {new_txt}")
                                    
                                    if os.path.exists(old_pdf):
                                        os.rename(old_pdf, new_pdf)
                                        logger.info(f"Renamed {old_pdf} to {new_pdf}")
                                
                                modified = True
                                logger.info(f"Fixed entry for PMID {pmid}: {first_author} -> {author_name}")
            
            if modified:
                df.to_csv(self.csv_file, index=False)
                logger.info("Fixed filename format for entries with numeric first_author")
            
            return True
            
        except Exception as e:
            logger.error(f"Error fixing filename format: {str(e)}")
            return False
    
    def get_entries_without_references(self) -> List[Dict]:
        """
        Get all entries that don't have references yet (ref_available is null or false).
        """
        try:
            df = pd.read_csv(self.csv_file)
            
            # Add ref_available column if it doesn't exist
            if 'ref_available' not in df.columns:
                df['ref_available'] = False
                df.to_csv(self.csv_file, index=False)
            
            # Filter entries without references and with valid PMIDs
            entries_without_refs = df[
                (df['ref_available'].isna() | (df['ref_available'] == False)) & 
                (df['pmid'].notna()) & 
                (df['extraction_status'] == 'success')
            ]
            
            # Convert to list of dictionaries
            entries = []
            for _, row in entries_without_refs.iterrows():
                entry = row.to_dict()
                # Replace NaN with None for JSON serialization
                for key, value in entry.items():
                    if pd.isna(value):
                        entry[key] = None
                entries.append(entry)
            
            return entries
            
        except Exception as e:
            logger.error(f"Error getting entries without references: {str(e)}")
            return []
    
    def update_ref_availability(self, pmid: str, ref_available: bool) -> bool:
        """
        Update the ref_available status for a specific PMID.
        """
        try:
            df = pd.read_csv(self.csv_file)
            
            # Add ref_available column if it doesn't exist
            if 'ref_available' not in df.columns:
                df['ref_available'] = False
            
            # Handle both integer and float PMIDs
            pmid_str = str(pmid)
            pmid_float_str = f"{float(pmid)}"
            
            # Update matching rows
            mask = (df['pmid'].astype(str) == pmid_str) | (df['pmid'].astype(str) == pmid_float_str)
            df.loc[mask, 'ref_available'] = ref_available
            
            if mask.any():
                df.to_csv(self.csv_file, index=False)
                logger.info(f"Updated ref_available to {ref_available} for PMID {pmid}")
                return True
            else:
                logger.warning(f"No entry found with PMID {pmid} to update")
                return False
                
        except Exception as e:
            logger.error(f"Error updating ref_availability for PMID {pmid}: {str(e)}")
            return False
    
    def search_entries(self, search_query: str = '') -> List[Dict]:
        """
        Search entries by title, author, or PMID.
        Returns list of matching entries.
        """
        try:
            df = pd.read_csv(self.csv_file)
            
            if not search_query:
                # Return all entries
                matching_df = df
            else:
                # Search in multiple columns
                search_query = search_query.lower()
                mask = (
                    df['extracted_title'].astype(str).str.lower().str.contains(search_query, na=False) |
                    df['found_title'].astype(str).str.lower().str.contains(search_query, na=False) |
                    df['first_author'].astype(str).str.lower().str.contains(search_query, na=False) |
                    df['pmid'].astype(str).str.contains(search_query, na=False)
                )
                matching_df = df[mask]
            
            # Convert to list of dictionaries
            entries = []
            for _, row in matching_df.iterrows():
                entry = row.to_dict()
                # Replace NaN with None for JSON serialization
                for key, value in entry.items():
                    if pd.isna(value):
                        entry[key] = None
                entries.append(entry)
            
            logger.info(f"Found {len(entries)} entries for search query: '{search_query}'")
            return entries
            
        except Exception as e:
            logger.error(f"Error searching entries: {str(e)}")
            return []
    
    def get_failed_entries(self) -> List[Dict]:
        """
        Get all entries where processing failed.
        Returns list of failed entries.
        """
        try:
            df = pd.read_csv(self.csv_file)
            
            # Filter for failed entries
            failed_mask = df['extraction_status'] != 'success'
            failed_df = df[failed_mask]
            
            # Convert to list of dictionaries
            entries = []
            for _, row in failed_df.iterrows():
                entry = row.to_dict()
                # Replace NaN with None for JSON serialization
                for key, value in entry.items():
                    if pd.isna(value):
                        entry[key] = None
                entries.append(entry)
            
            logger.info(f"Found {len(entries)} failed entries")
            return entries
            
        except Exception as e:
            logger.error(f"Error retrieving failed entries: {str(e)}")
            return []
    
    def get_all_entries(self) -> List[Dict]:
        """
        Get all entries from the database.
        Returns list of all entries.
        """
        return self.search_entries('')
    
    def update_entry(self, pmid: str, update_data: Dict) -> bool:
        """
        Update an existing entry by PMID.
        Returns True if successful, False otherwise.
        """
        try:
            df = pd.read_csv(self.csv_file)
            mask = df['pmid'].astype(str) == str(pmid)
            
            if not mask.any():
                logger.warning(f"No entry found with PMID {pmid} to update")
                return False
            
            # Update the matching row(s)
            for key, value in update_data.items():
                if key in df.columns:
                    df.loc[mask, key] = value
            
            # Save back to CSV
            df.to_csv(self.csv_file, index=False)
            
            logger.info(f"Updated entry for PMID: {pmid}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating entry for PMID {pmid}: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict:
        """
        Get database statistics.
        Returns dictionary with various statistics.
        """
        try:
            df = pd.read_csv(self.csv_file)
            
            stats = {
                'total_entries': len(df),
                'successful_extractions': len(df[df['extraction_status'] == 'success']),
                'failed_extractions': len(df[df['extraction_status'] != 'success']),
                'txt_available': len(df[df['txt_available'] == True]),
                'pdf_available': len(df[df['pdf_available'] == True]),
                'both_available': len(df[(df['txt_available'] == True) & (df['pdf_available'] == True)])
            }
            
            # Success rate
            if stats['total_entries'] > 0:
                stats['success_rate'] = stats['successful_extractions'] / stats['total_entries']
            else:
                stats['success_rate'] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {}
    
    def delete_entry(self, pmid: str) -> bool:
        """
        Delete an entry by PMID.
        Returns True if successful, False otherwise.
        """
        try:
            df = pd.read_csv(self.csv_file)
            initial_count = len(df)
            
            # Remove entries with matching PMID
            df = df[df['pmid'].astype(str) != str(pmid)]
            
            if len(df) == initial_count:
                logger.warning(f"No entry found with PMID {pmid} to delete")
                return False
            
            # Save back to CSV
            df.to_csv(self.csv_file, index=False)
            
            logger.info(f"Deleted entry for PMID: {pmid}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting entry for PMID {pmid}: {str(e)}")
            return False
    
    # Job Management Methods
    
    def _init_jobs_csv(self):
        """Initialize jobs.csv if it doesn't exist."""
        if not os.path.exists(self.jobs_csv):
            jobs_df = pd.DataFrame(columns=[
                'job_id', 'status', 'total_refs', 'completed_refs', 'failed_refs', 
                'created_at', 'updated_at', 'references_text'
            ])
            jobs_df.to_csv(self.jobs_csv, index=False)
    
    def _init_job_results_csv(self):
        """Initialize job_results.csv if it doesn't exist.""" 
        if not os.path.exists(self.job_results_csv):
            results_df = pd.DataFrame(columns=[
                'job_id', 'reference_index', 'status', 'pmid', 'extracted_title', 
                'error_message', 'processed_at'
            ])
            results_df.to_csv(self.job_results_csv, index=False)
    
    def create_job(self, references_text: str, total_refs: int) -> str:
        """
        Create a new processing job.
        Returns the job_id.
        """
        try:
            self._init_jobs_csv()
            
            job_id = str(uuid.uuid4())
            current_time = datetime.now().isoformat()
            
            # Read existing jobs
            if os.path.exists(self.jobs_csv):
                jobs_df = pd.read_csv(self.jobs_csv)
            else:
                jobs_df = pd.DataFrame(columns=[
                    'job_id', 'status', 'total_refs', 'completed_refs', 'failed_refs',
                    'created_at', 'updated_at', 'references_text'
                ])
            
            # Add new job
            new_job = pd.DataFrame([{
                'job_id': job_id,
                'status': 'pending',
                'total_refs': total_refs,
                'completed_refs': 0,
                'failed_refs': 0,
                'created_at': current_time,
                'updated_at': current_time,
                'references_text': references_text
            }])
            
            jobs_df = pd.concat([jobs_df, new_job], ignore_index=True)
            jobs_df.to_csv(self.jobs_csv, index=False)
            
            logger.info(f"Created job {job_id} with {total_refs} references")
            return job_id
            
        except Exception as e:
            logger.error(f"Error creating job: {str(e)}")
            raise
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """Get job details by job_id."""
        try:
            if not os.path.exists(self.jobs_csv):
                return None
                
            jobs_df = pd.read_csv(self.jobs_csv)
            job_row = jobs_df[jobs_df['job_id'] == job_id]
            
            if job_row.empty:
                return None
                
            job = job_row.iloc[0].to_dict()
            # Replace NaN with None
            for key, value in job.items():
                if pd.isna(value):
                    job[key] = None
                    
            return job
            
        except Exception as e:
            logger.error(f"Error getting job {job_id}: {str(e)}")
            return None
    
    def update_job_status(self, job_id: str, status: str, completed_refs: int = None, failed_refs: int = None) -> bool:
        """Update job status and progress."""
        try:
            if not os.path.exists(self.jobs_csv):
                return False
                
            jobs_df = pd.read_csv(self.jobs_csv)
            mask = jobs_df['job_id'] == job_id
            
            if not mask.any():
                logger.warning(f"Job {job_id} not found for status update")
                return False
            
            # Update fields
            jobs_df.loc[mask, 'status'] = status
            jobs_df.loc[mask, 'updated_at'] = datetime.now().isoformat()
            
            if completed_refs is not None:
                jobs_df.loc[mask, 'completed_refs'] = completed_refs
            if failed_refs is not None:
                jobs_df.loc[mask, 'failed_refs'] = failed_refs
                
            jobs_df.to_csv(self.jobs_csv, index=False)
            
            logger.info(f"Updated job {job_id}: status={status}, completed={completed_refs}, failed={failed_refs}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating job status for {job_id}: {str(e)}")
            return False
    
    def add_job_result(self, job_id: str, reference_index: int, status: str, pmid: str = None, 
                      extracted_title: str = None, error_message: str = None) -> bool:
        """Add a result for a specific reference in a job."""
        try:
            self._init_job_results_csv()
            
            if os.path.exists(self.job_results_csv):
                results_df = pd.read_csv(self.job_results_csv)
            else:
                results_df = pd.DataFrame(columns=[
                    'job_id', 'reference_index', 'status', 'pmid', 'extracted_title', 
                    'error_message', 'processed_at'
                ])
            
            new_result = pd.DataFrame([{
                'job_id': job_id,
                'reference_index': reference_index,
                'status': status,
                'pmid': pmid,
                'extracted_title': extracted_title,
                'error_message': error_message,
                'processed_at': datetime.now().isoformat()
            }])
            
            results_df = pd.concat([results_df, new_result], ignore_index=True)
            results_df.to_csv(self.job_results_csv, index=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding job result for {job_id}: {str(e)}")
            return False
    
    def get_job_results(self, job_id: str) -> List[Dict]:
        """Get all results for a specific job."""
        try:
            if not os.path.exists(self.job_results_csv):
                return []
                
            results_df = pd.read_csv(self.job_results_csv)
            job_results = results_df[results_df['job_id'] == job_id]
            
            results = []
            for _, row in job_results.iterrows():
                result = row.to_dict()
                # Replace NaN with None
                for key, value in result.items():
                    if pd.isna(value):
                        result[key] = None
                results.append(result)
                
            return sorted(results, key=lambda x: x['reference_index'])
            
        except Exception as e:
            logger.error(f"Error getting job results for {job_id}: {str(e)}")
            return []