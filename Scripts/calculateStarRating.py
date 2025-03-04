import pandas as pd
import numpy as np
from starThresholdParsing import get_star_rating

def calculate_star_ratings(scores_df: pd.DataFrame, 
                         thresholds: dict, 
                         measure_weights: dict) -> tuple:
    """
    Calculate star ratings and distances to next threshold for each measure
    
    Args:
        scores_df: DataFrame with measure scores
        thresholds: Dictionary of measure thresholds from create_measure_thresholds()
        measure_weights: Dictionary mapping measure names to their weights
        
    Returns:
        tuple: (star_ratings_df, distance_to_next_df, weighted_average)
    """
    # Initialize output DataFrames with same index as input
    star_ratings = pd.DataFrame(index=scores_df.index)
    distances = pd.DataFrame(index=scores_df.index)
    
    # Process each measure
    for measure in scores_df.columns:
        if measure not in measure_weights:
            continue
            
        # Get the measure's star ratings and distances
        stars = []
        next_thresholds = []
        
        for score in scores_df[measure]:
            if pd.isna(score):
                stars.append(np.nan)
                next_thresholds.append(np.nan)
                continue
                
            try:
                # Get star rating
                star = get_star_rating(measure, score, thresholds)
                stars.append(star)
                
                # Calculate distance to next threshold
                measure_ranges = thresholds[measure]
                current_range = [r for r in measure_ranges if r[2] == star][0]
                
                if star < 5:
                    next_range = [r for r in measure_ranges if r[2] == star + 1][0]
                    distance = next_range[0] - score
                else:
                    distance = 0
                    
                next_thresholds.append(distance)
                
            except (KeyError, ValueError):
                stars.append(np.nan)
                next_thresholds.append(np.nan)
        
        star_ratings[measure] = stars
        distances[measure] = next_thresholds
    
    # Calculate weighted average
    weighted_scores = []
    for idx in star_ratings.index:
        total_weight = 0
        total_score = 0
        
        for measure, weight in measure_weights.items():
            if measure in star_ratings.columns:
                star = star_ratings.loc[idx, measure]
                if not pd.isna(star):
                    total_score += star * weight
                    total_weight += weight
        
        if total_weight > 0:
            weighted_scores.append(total_score / total_weight)
        else:
            weighted_scores.append(np.nan)
    
    return star_ratings, distances, pd.Series(weighted_scores, index=scores_df.index)

def format_results(star_ratings: pd.DataFrame, 
                  distances: pd.DataFrame, 
                  weighted_avg: pd.Series,
                  measure_weights: dict) -> pd.DataFrame:
    """
    Format the results into a readable summary DataFrame
    """
    summary = pd.DataFrame()
    
    for measure in star_ratings.columns:
        if measure in measure_weights:
            summary[f"{measure} (Weight: {measure_weights[measure]})"] = star_ratings[measure].map(str) + \
                " stars (+" + distances[measure].round(3).map(str) + " to next)"
            
    summary['Weighted Average'] = weighted_avg.round(3).map(str) + " stars"
    
    return summary
