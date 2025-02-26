import pandas as pd
import numpy as np
from tabulate import tabulate

def calculate_improvement_path(star_ratings: pd.DataFrame, 
                            distances: pd.DataFrame,
                            measure_weights: dict,
                            current_weighted_avg: float,
                            target_rating: float) -> pd.DataFrame:
    """
    Calculate the most efficient path to reach the next star rating level
    
    Args:
        star_ratings: DataFrame with current star ratings
        distances: DataFrame with distances to next star level
        measure_weights: Dictionary of measure weights
        current_weighted_avg: Current weighted average star rating
        target_rating: Target star rating to reach
        
    Returns:
        DataFrame with ordered improvement opportunities
    """
    # Get the first row since we're analyzing one plan
    current_stars = star_ratings.iloc[0]
    current_distances = distances.iloc[0]
    
    # Calculate total weight for measures that have ratings
    total_weight = sum([measure_weights[col] for col in current_stars.dropna().index])
    
    # Create list of improvement opportunities
    opportunities = []
    
    for measure in current_stars.index:
        if measure not in measure_weights:
            continue
            
        star = current_stars[measure]
        distance = current_distances[measure]
        weight = measure_weights[measure]
        
        # Skip measures that are NA, already 5 stars, or have no distance data
        if pd.isna(star) or star == 5 or pd.isna(distance):
            continue
            
        # Calculate impact of improving this measure by one star
        rating_impact = weight / total_weight
            
        opportunities.append({
            'Measure': measure,
            'Current_Stars': star,
            'Weight': weight,
            'Distance_to_Next': distance,
            'Distance_per_Weight': abs(distance) / weight,
            'Single_Measure_Impact': rating_impact
        })
    
    # Convert to DataFrame and sort by efficiency (absolute distance per weight)
    path_df = pd.DataFrame(opportunities)
    if len(path_df) == 0:
        return pd.DataFrame()
        
    path_df = path_df.sort_values('Distance_per_Weight')
    
    # Calculate cumulative weights and rating impacts
    path_df['Cumulative_Weight'] = path_df['Weight'].cumsum()
    path_df['Cumulative_Rating_Impact'] = current_weighted_avg + path_df['Single_Measure_Impact'].cumsum()
    
    # Format the final output
    output_df = path_df[[
        'Measure', 
        'Weight', 
        'Distance_to_Next',
        'Distance_per_Weight',
        'Cumulative_Weight',
        'Cumulative_Rating_Impact'
    ]].round(3)
    
    # Add how many measures needed to reach target
    target_idx = (output_df['Cumulative_Rating_Impact'] >= target_rating).idxmax() \
        if any(output_df['Cumulative_Rating_Impact'] >= target_rating) else None
    
    if target_idx is not None:
        measures_needed = output_df.iloc[:target_idx + 1]
        print(f"\nTo reach {target_rating} stars, improve these {len(measures_needed)} measures:")
        for _, row in measures_needed.iterrows():
            print(f"- {row['Measure']}: {row['Distance_to_Next']:.3f} points needed (weight: {row['Weight']})")
    
    return output_df

def main(results, measures_2025, current_weighted_avg, target_rating):
    """
    Main function to analyze improvement path
    """
    star_ratings, distances = results[0], results[1]
    
    improvement_path = calculate_improvement_path(
        star_ratings,
        distances,
        measures_2025,
        current_weighted_avg,
        target_rating
    )
    
    return improvement_path


def generate_improvement_report(improvement_path: pd.DataFrame, 
                             current_rating: float,
                             target_rating: float,
                             points_needed: float) -> str:
    """
    Generate a formatted report of the star rating improvement path
    
    Args:
        improvement_path: DataFrame from calculate_improvement_path
        current_rating: Current star rating
        target_rating: Target star rating
        points_needed: Points needed to reach target rating
        
    Returns:
        Formatted string report
    """
    report = []
    
    # Header section
    report.append("=" * 80)
    report.append("STAR RATING IMPROVEMENT ANALYSIS")
    report.append("=" * 80)
    
    # Summary section
    report.append("\nCURRENT STATUS:")
    report.append(f"Current Rating: {current_rating:.2f} stars")
    report.append(f"Target Rating:  {target_rating:.2f} stars")
    report.append(f"Points Needed: {points_needed:.2f}")
    
    # Format the improvement path table
    table_data = improvement_path.copy()
    
    # Rename columns for clarity
    table_data.columns = [
        'Measure',
        'Weight',
        'Points to Next ★',
        'Points/Weight',
        'Cumulative Weight',
        'Projected Rating'
    ]
    
    # Add star improvement indicator
    table_data['Improvement'] = '★ → ★★'
    
    # Format numeric columns
    for col in ['Points to Next ★', 'Points/Weight', 'Projected Rating']:
        table_data[col] = table_data[col].round(3)
    
    # Create the main table
    report.append("\nIMPROVEMENT OPPORTUNITIES (Ordered by Efficiency):")
    report.append(tabulate(
        table_data, 
        headers='keys',
        tablefmt='grid',
        showindex=False
    ))
    
    # Add recommendations section
    target_idx = (improvement_path['Cumulative_Rating_Impact'] >= target_rating).idxmax() \
        if any(improvement_path['Cumulative_Rating_Impact'] >= target_rating) else None
    
    if target_idx is not None:
        measures_needed = improvement_path.iloc[:target_idx + 1]
        report.append("\nRECOMMENDED IMPROVEMENT PATH:")
        report.append(f"To reach {target_rating} stars, focus on these {len(measures_needed)} measures:")
        
        for idx, row in measures_needed.iterrows():
            impact = row['Cumulative_Rating_Impact'] - \
                    (measures_needed.iloc[idx-1]['Cumulative_Rating_Impact'] if idx > 0 else current_rating)
            report.append(
                f"\n{idx + 1}. {row['Measure']}"
                f"\n   → Improvement needed: {abs(row['Distance_to_Next']):.3f} points"
                f"\n   → Weight: {row['Weight']}"
                f"\n   → Rating impact: +{impact:.3f} stars"
                f"\n   → Projected rating after improvement: {row['Cumulative_Rating_Impact']:.3f} stars"
            )
    else:
        report.append("\nNOTE: Target rating cannot be reached by improving all available measures by one star.")
    
    # Footer
    report.append("\n" + "=" * 80)
    report.append("Note: This analysis assumes sequential improvements of one star level per measure.")
    report.append("=" * 80)
    
    return "\n".join(report)

# Example usage:
def create_improvement_report(results, measures_2025, current_rating, target_rating, points_needed):
    """
    Create and display the improvement report
    """
    improvement_path = main(
        results=results,
        measures_2025=measures_2025,
        current_weighted_avg=current_rating,
        target_rating=target_rating
    )
    
    report = generate_improvement_report(
        improvement_path=improvement_path,
        current_rating=current_rating,
        target_rating=target_rating,
        points_needed=points_needed
    )
    
    return report