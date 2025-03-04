from HelperObjects.measureWeights import measures_2025
from fileCleaning import clean_medicare_advantage_data, create_measure_thresholds, prep_for_beta_regression
from HelperObjects.measureWeights import measures_2025
from analyzeImprovmentStrategies import analyze_improvement_strategies
from storeBetaRegressionModels import store_beta_regression_models
from monteCarloSimulation import run_monte_carlo_simulation
from calculateStarRating import calculate_star_ratings
from improvementPath import calculate_improvement_path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def analyze_star_rating_improvements(folder_path, file_paths, contract_id, analysis_year, 
                                   star_values, cost_per_point=10000, n_simulations=1000):
    """
    Complete workflow for analyzing STAR rating improvement strategies.
    
    Args:
        folder_path: Path to the folder containing measure data files
        file_paths: List of file paths for measure data CSVs
        contract_id: CONTRACT_ID to analyze
        analysis_year: Year to analyze (e.g., '2025')
        star_values: Dictionary mapping star ratings to dollar values
        cost_per_point: Estimated cost per percentage point improvement
        n_simulations: Number of Monte Carlo simulations to run
        
    Returns:
        Dictionary containing analysis results
    """
    import pandas as pd
    import matplotlib.pyplot as plt
    
    # Step 1: Load and clean data
    print("Loading and cleaning data...")
    df = clean_medicare_advantage_data(folder_path, file_paths)

    df, feature_cols = prep_for_beta_regression(df)
    
    # Step 2: Load thresholds
    print("Loading threshold data...")
    threshold_df = pd.read_csv('Data/Cutpoints/2025 Star Ratings Part C Cut Points.csv', 
                              encoding='cp1252', skiprows=2)
    formatted_thresholds = {}
    thresholds = create_measure_thresholds(threshold_df)
    
    # Format thresholds to match column names in data
    for key in thresholds.keys():
        formatted_key = key.split(':')[0][0] + ':' + key.split(':')[1]
        formatted_thresholds[formatted_key] = thresholds[key]
    
    # Step 3: Analyze improvement strategies
    print(f"Analyzing improvement strategies for contract {contract_id} in {analysis_year}...")
    improvement_analysis = analyze_improvement_strategies(
        df, formatted_thresholds, measures_2025, 
        contract_id, analysis_year, star_values,
        cost_per_point, n_simulations
    )
    
    # Step 4: Basic Monte Carlo without improvements
    print("Running baseline Monte Carlo simulation...")
    measure_cols = [col for col in df.columns if col.startswith("C:")]
    models = store_beta_regression_models(df, measure_cols)
    baseline_simulation = run_monte_carlo_simulation(
        df, models, formatted_thresholds, measures_2025,
        contract_id, analysis_year, n_simulations
    )
    
    # Step 5: Calculate improvement path
    contract_df = df[(df["CONTRACT_ID"] == contract_id) & (df["Year"] == analysis_year)]
    if len(contract_df) > 0:
        print("Calculating improvement path...")
        star_ratings, distances, weighted_avg = calculate_star_ratings(
            contract_df[[col for col in contract_df.columns if 'C:' in col]], 
            formatted_thresholds, 
            measures_2025
        )
        
        # Get the next highest cutoff
        rating_cutoffs = [2.75, 3.25, 3.75, 4.25, 4.75]
        current_rating = weighted_avg.iloc[0]
        next_cutoff = next((cutoff for cutoff in rating_cutoffs if cutoff > current_rating), None)
        
        if next_cutoff:
            # Calculate points needed
            points_needed = next_cutoff - current_rating
            
            # Get improvement path
            results = [star_ratings, distances]
            improvement_path = calculate_improvement_path(
                star_ratings, 
                distances,
                measures_2025,
                current_rating,
                next_cutoff
            )
        else:
            improvement_path = pd.DataFrame()
            points_needed = 0
    else:
        improvement_path = pd.DataFrame()
        points_needed = 0
        current_rating = None
    
    # Create some visualizations
    if len(baseline_simulation["simulated_ratings"]) > 0:
        plt.figure(figsize=(10, 6))
        plt.hist(baseline_simulation["simulated_ratings"], bins=30, alpha=0.7)
        plt.title(f"Distribution of Simulated Star Ratings for {contract_id}")
        plt.xlabel("Star Rating")
        plt.ylabel("Frequency")
        
        # Add vertical lines for cutoffs
        for cutoff in [2.75, 3.25, 3.75, 4.25, 4.75]:
            plt.axvline(cutoff, color='red', linestyle='--', alpha=0.5)
            
        # Save the plot
        plt.savefig(f"{contract_id}_rating_distribution.png")
    
    # Return all results
    return {
        "improvement_analysis": improvement_analysis,
        "baseline_simulation": baseline_simulation,
        "improvement_path": improvement_path,
        "current_rating": current_rating,
        "next_cutoff": next_cutoff if 'next_cutoff' in locals() else None,
        "points_needed": points_needed
    }