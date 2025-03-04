import numpy as np
import pandas as pd
from fileCleaning import get_beta_regression_distribution
from calculateStarRating import calculate_star_ratings


def run_monte_carlo_simulation(df, models, thresholds, measure_weights, 
                             contract_id, year, n_simulations=1000, 
                             adjustments=None):
    """
    Run Monte Carlo simulation to estimate star rating distribution.
    
    Args:
        df: DataFrame with historical data
        models: Dictionary of beta regression models from store_beta_regression_models
        thresholds: Dictionary of measure thresholds
        measure_weights: Dictionary of measure weights
        contract_id: CONTRACT_ID to analyze
        year: Year to analyze (string)
        n_simulations: Number of simulations to run
        adjustments: Dictionary mapping measures to adjustment values (e.g., {'C: Breast Cancer Screening': 1.5})
        
    Returns:
        Dictionary with simulation results
    """

    
    # Get the contract data for the specified year
    contract_df = df[(df["CONTRACT_ID"] == contract_id) & (df["Year"] == year)]
    
    if len(contract_df) == 0:
        raise ValueError(f"No data found for contract {contract_id} in year {year}")
    
    # Get index of the contract row
    contract_idx = contract_df.index[0]
    
    # Extract measure columns
    measure_cols = [col for col in contract_df.columns if col.startswith("C:")]
    
    # Initialize arrays to store results
    simulated_ratings = np.zeros(n_simulations)
    simulated_measures = {measure: np.zeros(n_simulations) for measure in measure_cols if measure in models}
    
    # Run simulations
    for i in range(n_simulations):
        # Create a dictionary to store simulated measure values for this run
        sim_measures = {}
        
        # Generate simulated values for each measure
        for measure in measure_cols:
            if measure not in models:
                # Use actual value if no model is available
                if measure in contract_df.columns and not pd.isna(contract_df[measure].values[0]):
                    sim_measures[measure] = contract_df[measure].values[0]
                continue
                
            # Use the beta regression to sample a value
            model_info = models[measure]
            model = model_info['model']
            feature_cols = model_info['feature_cols']
            
            try:
                # Sample from the beta distribution
                distribution = get_beta_regression_distribution(
                    model, df, measure, feature_cols, contract_idx
                )
                
                # Choose a random sample - fixed number of samples (1638)
                sample_idx = np.random.randint(0, len(distribution))
                sampled_value = distribution[sample_idx] * 100
                
                # Apply adjustment if specified
                if adjustments and measure in adjustments:
                    sampled_value += adjustments[measure]
                    # Ensure value is between 0 and 100 for percentage measures
                    if sampled_value > 100:
                        sampled_value = 100
                    elif sampled_value < 0:
                        sampled_value = 0
                
                sim_measures[measure] = sampled_value
                simulated_measures[measure][i] = sampled_value
                
            except Exception as e:
                print(f"Error generating sample for {measure}: {e}")
                # Fallback to actual value if available
                if measure in contract_df.columns and not pd.isna(contract_df[measure].values[0]):
                    sim_measures[measure] = contract_df[measure].values[0]
                    simulated_measures[measure][i] = contract_df[measure].values[0]
        
        # Create a DataFrame for star rating calculation
        sim_df = pd.DataFrame([sim_measures])
        
        # Calculate star ratings
        star_ratings, _, weighted_avg = calculate_star_ratings(
            sim_df, thresholds, measure_weights
        )
        
        # Store the weighted average star rating
        simulated_ratings[i] = weighted_avg.iloc[0]
    
    # Calculate probability of each star rating level
    rating_levels = [1.0, 2.0, 3.0, 4.0, 5.0]
    rating_cutoffs = [1.75, 2.75, 3.25, 3.75, 4.25, 4.75]
    
    rating_probs = {}
    for i in range(len(rating_levels)):
        if i == 0:
            prob = np.mean(simulated_ratings < rating_cutoffs[i])
        elif i == len(rating_levels) - 1:
            prob = np.mean(simulated_ratings >= rating_cutoffs[i-1])
        else:
            prob = np.mean((simulated_ratings >= rating_cutoffs[i-1]) & 
                          (simulated_ratings < rating_cutoffs[i]))
        
        rating_probs[rating_levels[i]] = prob
    
    return {
        "simulated_ratings": simulated_ratings,
        "simulated_measures": simulated_measures,
        "rating_probabilities": rating_probs,
        "expected_rating": np.mean(simulated_ratings),
        "rating_std_dev": np.std(simulated_ratings)
    }