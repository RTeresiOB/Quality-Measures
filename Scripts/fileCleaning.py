import pandas as pd
import glob
import re
from typing import List, Dict


def clean_medicare_advantage_data(folder_path: str, file_paths: List[str]) -> Dict[str, pd.DataFrame]:
    """
    Clean and standardize Medicare Advantage Star Ratings data from multiple years.
    
    Args:
        file_paths: List of paths to Star Ratings CSV files
        
    Returns:
        Dictionary containing cleaned DataFrames for different aspects of the data:
        - 'contract_info': Basic contract information
        - 'measures': Detailed measure scores
        - 'domain_scores': Domain-level scores
    """
    
    all_contract_info = []
    all_measures = []
    all_domain_scores = []
    
    for file_path in file_paths:
        # Extract year from filename
        year_match = re.search(r'(\d{4})\s+Star\s+Ratings', file_path)
        if not year_match:
            raise ValueError(f"Could not extract year from filename: {file_path}")
        year = year_match.group(1)
        
        # Read the CSV file
        df = pd.read_csv(folder_path + file_path, encoding='cp1252')
        
        # Get the base column name (first column) which contains the year
        base_col = df.columns[0]
        
        # Rename unnamed columns to their index position
        df.columns = [base_col] + [f'col_{i}' for i in range(1, len(df.columns))]
        
        # First few rows contain header information
        # Find the row with CONTRACT_ID
        contract_row_idx = df[df[base_col] == 'CONTRACT_ID'].index[0]
        
        # Use this row as headers and skip rows above it
        headers = df.iloc[contract_row_idx]
        df = df.iloc[contract_row_idx + 1:].reset_index(drop=True)
        df.columns = headers
        
        # Basic contract information
        contract_info = df[[
            'CONTRACT_ID', 
            'Organization Type',
            'Contract Name',
            'Organization Marketing Name',
            'Parent Organization'
        ]].copy()
        contract_info['year'] = year
        all_contract_info.append(contract_info)
        
        # Extract measure scores
        # Measures are typically numeric values or start with numbers (like "4 out of 5 stars")
        measure_cols = ['CONTRACT_ID'] + [
            col for col in df.columns 
            if any(char.isdigit() for char in str(df[col].iloc[0]))
        ]
        measures = df[measure_cols].copy()
        measures['year'] = year
        all_measures.append(measures)
        
        # Extract domain scores
        domain_patterns = [
            'HD1:', 'HD2:', 'HD3:', 'HD4:', 'HD5:',
            'DD1:', 'DD2:', 'DD3:', 'DD4:'
        ]
        
        domain_cols = ['CONTRACT_ID'] + [
            col for col in df.columns 
            if any(pattern in str(col) for pattern in domain_patterns)
        ]
        
        domain_scores = df[domain_cols].copy()
        domain_scores['year'] = year
        all_domain_scores.append(domain_scores)
    
    # Combine data from all years
    combined_data = {
        'contract_info': pd.concat(all_contract_info, ignore_index=True),
        'measures': pd.concat(all_measures, ignore_index=True),
        'domain_scores': pd.concat(all_domain_scores, ignore_index=True)
    }
    
    # Clean up the data
    for key in combined_data:
        df = combined_data[key]
        # Convert year to integer
        df['year'] = df['year'].astype(int)
        # Remove leading/trailing whitespace
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()
    
    return combined_data

def extract_star_rating(value: str) -> float:
    """
    Extract numeric star rating from string.
    Examples:
        "4 out of 5 stars" -> 4.0
        "4.5 stars" -> 4.5
    """
    if pd.isna(value):
        return None
    
    value = str(value).lower()
    match = re.search(r'(\d+\.?\d*)\s*(?:out of \d+\s*)?stars?', value)
    if match:
        return float(match.group(1))
    return None

def calculate_yoy_changes(data: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Calculate year-over-year changes for measures and domain scores.
    
    Args:
        data: Dictionary containing cleaned DataFrames
        
    Returns:
        Dictionary containing DataFrames with YoY changes
    """
    yoy_changes = {}
    
    for key in ['measures', 'domain_scores']:
        df = data[key].copy()
        
        # Convert star ratings to numeric values
        numeric_cols = [col for col in df.columns if col not in ['CONTRACT_ID', 'year']]
        for col in numeric_cols:
            df[col] = df[col].apply(extract_star_rating)
        
        # Calculate YoY changes
        df_sorted = df.sort_values(['CONTRACT_ID', 'year'])
        
        # Calculate differences
        yoy_diff = df_sorted.groupby('CONTRACT_ID').diff()
        
        # Add year and CONTRACT_ID back
        yoy_diff['year'] = df_sorted['year']
        yoy_diff['CONTRACT_ID'] = df_sorted['CONTRACT_ID']
        
        # Remove rows where we don't have previous year data
        yoy_diff = yoy_diff.dropna(subset=['year'])
        
        yoy_changes[key] = yoy_diff
    
    return yoy_changes

# Example usage:
if __name__ == "__main__":
    # List of file paths
    folder = "Data/Measure Data/"
    files = [
        "2023 Star Ratings Measure Data.csv",
        "2024 Star Ratings Measure Data.csv"
    ]
    
    # Clean the data
    cleaned_data = clean_medicare_advantage_data(folder, files)
    
    # Calculate YoY changes
    yoy_changes = calculate_yoy_changes(cleaned_data)
    
    # Example: Print summary statistics
    for key in cleaned_data:
        print(f"\nSummary for {key}:")
        print(f"Number of records: {len(cleaned_data[key])}")
        print(f"Number of unique contracts: {cleaned_data[key]['CONTRACT_ID'].nunique()}")
        print(f"Years covered: {sorted(cleaned_data[key]['year'].unique())}")
