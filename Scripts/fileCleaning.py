import pandas as pd
import re
from typing import List, Dict
from HelperObjects.measureWeights import measures_2025


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
    dfs = []
    for file_path in file_paths:
        year_match = re.search(r'(\d{4})\s+Star\s+Ratings', file_path)
        if not year_match:
            raise ValueError(f"Could not extract year from filename: {file_path}")
        year = year_match.group(1)
        print(year)
        # Read the CSV file
        df = pd.read_csv(folder_path + file_path, encoding='cp1252', skiprows=2)

        df = df.iloc[1:,:]

        # Drop columns that start with 'D'
        df = df.loc[:, ~df.columns.str.startswith('D')]

        # Add first 4 column names: CONTRACT_ID	Organization Type	Contract Name	Organization Marketing Name	Parent Organization
        df.columns = ["CONTRACT_ID", "Organization Type", "Contract Name", "Organization Marketing Name", "Parent Organization"] + list(df.columns[5:])

        # Remove the 'C\d{2}: ' prefix from the column names
        df.columns = [re.sub(r'^C\d{2}: ', 'C: ', col) for col in df.columns]

        # Remove the % sign from all columns
        df = df.replace('\%', '', regex=True)

        # For columns starting with 'C:', convert all non-numberic values to NaN
        df.loc[:, df.columns.str.startswith('C:')] = df.loc[:, df.columns.str.startswith('C:')].apply(pd.to_numeric, errors='coerce')

        # Add a column for the year
        df['Year'] = year

        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True, axis=0)

    # sort by plan then year
    df = df.sort_values(['CONTRACT_ID', 'Year'])
    df.loc[df[ 'C: Controlling Blood Pressure'].isna(), 'C: Controlling Blood Pressure'] = df['C: Controlling High Blood Pressure']
    df.drop(columns=['C: Controlling High Blood Pressure'], inplace=True)

    # trim whitespace from CONTRACT_ID
    df['CONTRACT_ID'] = df['CONTRACT_ID'].str.strip()

    df['Year'] = df['Year'].astype(int)
    
    return df

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

def prep_for_beta_regression(df):

    lag_1 = df[['CONTRACT_ID'] + list(measures_2025.keys())].groupby('CONTRACT_ID').shift(1).rename(columns={col: col + '_lag1' for col in measures_2025.keys()})
    diff_1 = df[['CONTRACT_ID'] + list(measures_2025.keys())].groupby('CONTRACT_ID').diff(1).rename(columns={col: col + '_diff1' for col in measures_2025.keys()})
    diff_2 = df[['CONTRACT_ID'] + list(measures_2025.keys())].groupby('CONTRACT_ID').diff(2).rename(columns={col: col + '_diff2' for col in measures_2025.keys()})
    # join on index
    df = pd.concat([df, lag_1, diff_1, diff_2], axis=1)
    # For columns with diff1, diff2, or _lag1, create a new column that is an indicator for whether that value is missing
    diff_1_cols = [col for col in df.columns if '_diff1' in col]
    diff_2_cols = [col for col in df.columns if '_diff2' in col]
    lag_1_cols = [col for col in df.columns if '_lag1' in col]

    for col in diff_1_cols + diff_2_cols + lag_1_cols:
        df[col + '_missing'] = df[col].isna().astype(int)
    # Replace NaNs with 0 for lag1, diff1, and diff2 columns
    df[diff_1.columns] = df[diff_1.columns].fillna(0)
    df[diff_2.columns] = df[diff_2.columns].fillna(0)
    df[lag_1.columns] = df[lag_1.columns].fillna(0)

    featureCols = list(diff_1.columns) + list(diff_2.columns) + list(lag_1.columns) + [col for col in df.columns if '_missing' in col] 

    return df, featureCols

def beta_regression(df, targetCol, featureCols):
    from statsmodels.othermod.betareg import BetaModel

    regDf = df.dropna(subset=[targetCol], axis=0)[[targetCol] + featureCols]

    precision_cols = [col for col in featureCols if targetCol in col]

    betaResult = BetaModel(regDf[targetCol].apply(lambda x: (x / 100)-.0001),
                            regDf.drop(columns=[targetCol]),
                            exog_precision=regDf[precision_cols]
                        ).fit()
    return betaResult

def get_beta_regression_distribution(betaResult, df, targetCol, featureCols, index):
    regDf = df.dropna(subset=[targetCol], axis=0)[[targetCol] + featureCols]
    precision_cols = [col for col in featureCols if targetCol in col]

    distribution = betaResult.get_distribution(
                            exog=df.drop(columns=[targetCol]).iloc[index], 
                           exog_precision=regDf[precision_cols].iloc[index])
    
    return distribution.rvs(1638) # I think this number of unique plans. Have to check. Might be the number of obs in the regression - slightly different w NA values


    