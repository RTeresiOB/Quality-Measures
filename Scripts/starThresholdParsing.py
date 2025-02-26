import pandas as pd
import re

def parse_threshold(threshold_str: str) -> tuple:
    """
    Parse threshold strings like '>= 53 % to < 67 %' or '< 53 %' into numeric bounds
    Also handles negative numbers and relative change metrics
    Returns tuple of (lower_bound, upper_bound)
    """
    if pd.isna(threshold_str):
        return None
        
    # Clean the string by removing '%' and extra spaces
    threshold_str = threshold_str.replace('%', '').strip()
    
    try:
        if 'to' in threshold_str:
            # Handle range case: '>= -0.179809 to < 0'
            lower_str, upper_str = threshold_str.split('to')
            # Updated regex to handle negative numbers
            lower_bound = float(re.findall(r'>=?\s*([-]?\d+\.?\d*)', lower_str)[0])
            upper_bound = float(re.findall(r'<=?\s*([-]?\d+\.?\d*)', upper_str)[0])
            return (lower_bound, upper_bound)
        elif threshold_str.startswith('<'):
            # Handle less than case: '< -0.179809'
            upper_bound = float(re.findall(r'<=?\s*([-]?\d+\.?\d*)', threshold_str)[0])
            return (-float('inf'), upper_bound)
        elif threshold_str.startswith('>='):
            # Handle greater than or equal case: '>= 0.421057'
            lower_bound = float(re.findall(r'>=\s*([-]?\d+\.?\d*)', threshold_str)[0])
            return (lower_bound, float('inf'))
        elif threshold_str.startswith('>'):
            # Handle greater than case: '> -0.5'
            lower_bound = float(re.findall(r'>\s*([-]?\d+\.?\d*)', threshold_str)[0])
            return (lower_bound, float('inf'))
        elif threshold_str.startswith('100'):
            return (100, 100)
        else:
            raise ValueError(f"Unexpected threshold format: {threshold_str}")
    except IndexError as e:
        raise ValueError(f"Could not parse threshold: {threshold_str}") from e


def create_measure_thresholds(df: pd.DataFrame) -> dict:
    """
    Transform the threshold dataframe into a dictionary of measure thresholds
    Returns dict with measure IDs as keys and lists of (lower_bound, upper_bound, star_rating) as values
    """
    measure_thresholds = {}
    
    # Get the actual star rating rows (skip header row)
    star_rows = df[df.iloc[:, 0].str.contains('star', na=False, case=False)]
    
    # Iterate through each measure (column)
    for measure in df.columns[1:]:  # Skip the star rating column
        thresholds = []
        # Iterate through each star rating level
        for idx, row in star_rows.iterrows():
            star_str = row.iloc[0]
            try:
                star_rating = int(star_str.lower().replace('star', '').strip())
            except (ValueError, AttributeError):
                continue
                
            threshold_str = row[measure]
            
            if pd.notna(threshold_str):
                try:
                    parsed = parse_threshold(threshold_str)
                    if parsed:
                        lower_bound, upper_bound = parsed
                        thresholds.append((lower_bound, upper_bound, star_rating))
                except ValueError as e:
                    print(f"Warning: Could not parse threshold '{threshold_str}' for {measure}: {e}")
                    continue
        
        if thresholds:  # Only add measures that have valid thresholds
            measure_thresholds[measure] = sorted(thresholds, key=lambda x: x[2])  # Sort by star rating
    
    return measure_thresholds

def get_star_rating(measure_id: str, score: float, thresholds: dict) -> int:
    """
    Get the star rating for a specific measure and score
    
    Args:
        measure_id: The measure identifier (e.g., 'C01: Breast Cancer Screening')
        score: The numeric score (e.g., 74)
        thresholds: Dictionary of measure thresholds
    
    Returns:
        int: Star rating (1-5)
        
    Raises:
        KeyError: If measure_id is not found in thresholds
        ValueError: If score doesn't fall into any threshold range
    """
    if measure_id not in thresholds:
        raise KeyError(f"Unknown measure ID: {measure_id}")
    
    measure_ranges = thresholds[measure_id]
    
    for lower_bound, upper_bound, star_rating in measure_ranges:
        if lower_bound <= score < upper_bound:
            return star_rating
            
    # Special case: check if score equals the highest threshold
    highest_range = max(measure_ranges, key=lambda x: x[2])
    if score >= highest_range[0]:
        return highest_range[2]
            
    raise ValueError(f"Score {score} does not fall into any defined range for measure {measure_id}")

import pandas as pd
import re

def parse_threshold(threshold_str: str) -> tuple:
    """
    Parse threshold strings like '>= 53 % to < 67 %' or '< 53 %' into numeric bounds
    Also handles negative numbers and relative change metrics
    Returns tuple of (lower_bound, upper_bound)
    """
    if pd.isna(threshold_str):
        return None
        
    # Clean the string by removing '%' and extra spaces
    threshold_str = threshold_str.replace('%', '').strip()
    
    try:
        if 'to' in threshold_str:
            # Handle range case: '>= -0.179809 to < 0'
            lower_str, upper_str = threshold_str.split('to')
            # Updated regex to handle negative numbers
            lower_bound = float(re.findall(r'>=?\s*([-]?\d+\.?\d*)', lower_str)[0])
            upper_bound = float(re.findall(r'<=?\s*([-]?\d+\.?\d*)', upper_str)[0])
            return (lower_bound, upper_bound)
        elif threshold_str.startswith('<'):
            # Handle less than case: '< -0.179809'
            upper_bound = float(re.findall(r'<=?\s*([-]?\d+\.?\d*)', threshold_str)[0])
            return (-float('inf'), upper_bound)
        elif threshold_str.startswith('>='):
            # Handle greater than or equal case: '>= 0.421057'
            lower_bound = float(re.findall(r'>=\s*([-]?\d+\.?\d*)', threshold_str)[0])
            return (lower_bound, float('inf'))
        elif threshold_str.startswith('>'):
            # Handle greater than case: '> -0.5'
            lower_bound = float(re.findall(r'>\s*([-]?\d+\.?\d*)', threshold_str)[0])
            return (lower_bound, float('inf'))
        elif threshold_str.startswith('100'):
            return (100, 100)
        else:
            raise ValueError(f"Unexpected threshold format: {threshold_str}")
    except IndexError as e:
        raise ValueError(f"Could not parse threshold: {threshold_str}") from e


def create_measure_thresholds(df: pd.DataFrame) -> dict:
    """
    Transform the threshold dataframe into a dictionary of measure thresholds
    Returns dict with measure IDs as keys and lists of (lower_bound, upper_bound, star_rating) as values
    """
    measure_thresholds = {}
    
    # Get the actual star rating rows (skip header row)
    star_rows = df[df.iloc[:, 0].str.contains('star', na=False, case=False)]
    
    # Iterate through each measure (column)
    for measure in df.columns[1:]:  # Skip the star rating column
        thresholds = []
        # Iterate through each star rating level
        for idx, row in star_rows.iterrows():
            star_str = row.iloc[0]
            try:
                star_rating = int(star_str.lower().replace('star', '').strip())
            except (ValueError, AttributeError):
                continue
                
            threshold_str = row[measure]
            
            if pd.notna(threshold_str):
                try:
                    parsed = parse_threshold(threshold_str)
                    if parsed:
                        lower_bound, upper_bound = parsed
                        thresholds.append((lower_bound, upper_bound, star_rating))
                except ValueError as e:
                    print(f"Warning: Could not parse threshold '{threshold_str}' for {measure}: {e}")
                    continue
        
        if thresholds:  # Only add measures that have valid thresholds
            measure_thresholds[measure] = sorted(thresholds, key=lambda x: x[2])  # Sort by star rating
    
    return measure_thresholds

def get_star_rating(measure_id: str, score: float, thresholds: dict) -> int:
    """
    Get the star rating for a specific measure and score
    
    Args:
        measure_id: The measure identifier (e.g., 'C01: Breast Cancer Screening')
        score: The numeric score (e.g., 74)
        thresholds: Dictionary of measure thresholds
    
    Returns:
        int: Star rating (1-5)
        
    Raises:
        KeyError: If measure_id is not found in thresholds
        ValueError: If score doesn't fall into any threshold range
    """
    if measure_id not in thresholds:
        raise KeyError(f"Unknown measure ID: {measure_id}")
    
    measure_ranges = thresholds[measure_id]
    
    for lower_bound, upper_bound, star_rating in measure_ranges:
        if lower_bound <= score < upper_bound:
            return star_rating
            
    # Special case: check if score equals the highest threshold
    highest_range = max(measure_ranges, key=lambda x: x[2])
    if score >= highest_range[0]:
        return highest_range[2]
            
    raise ValueError(f"Score {score} does not fall into any defined range for measure {measure_id}")

def main():
    # Read the thresholds CSV
    df = pd.read_csv('Data/Cutpoints/2025 Star Ratings Part C Cut Points.csv', encoding='cp1252', skiprows=2)
    
    # Create the thresholds dictionary
    thresholds = create_measure_thresholds(df)
    
    print(thresholds)
    # Example usage
    test_cases = [
        ('C01: Breast Cancer Screening', 74),
        ('C02: Colorectal Cancer Screening', 85),
        ('C03: Annual Flu Vaccine', 63)
    ]
    
    for measure_id, score in test_cases:
        try:
            stars = get_star_rating(measure_id, score, thresholds)
            print(f"{measure_id} score {score} = {stars} stars")
        except (KeyError, ValueError) as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    main()