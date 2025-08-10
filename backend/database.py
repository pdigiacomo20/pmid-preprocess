import pandas as pd
import os
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, csv_file: str = None):
        if csv_file is None:
            # Default to entries.csv in the project root
            project_root = os.path.dirname(os.path.dirname(__file__))
            csv_file = os.path.join(project_root, 'entries.csv')
        
        self.csv_file = csv_file
        self.columns = [
            'pmid',
            'filename',
            'extraction_status',
            'txt_available',
            'pdf_available',
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
            matching_rows = df[df['pmid'].astype(str) == str(pmid)]
            
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