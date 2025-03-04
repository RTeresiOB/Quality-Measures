def evaluate_measure_improvement_value(df, models, thresholds, measure_weights,
                                     contract_id, year, improvements,
                                     star_values, n_simulations=1000):
    """
    Evaluate the economic value of measure improvements.
    
    Args:
        df: DataFrame with historical data
        models: Dictionary of beta regression models
        thresholds: Dictionary of measure thresholds
        measure_weights: Dictionary of measure weights
        contract_id: CONTRACT_ID to analyze
        year: Year to analyze
        improvements: Dictionary mapping measures to improvement values
        star_values: Dictionary mapping star ratings to dollar values
        n_simulations: Number of simulations to run
        
    Returns:
        Dictionary with economic value analysis
    """
    # Baseline simulation (no improvements)
    baseline = run_monte_carlo_simulation(
        df, models, thresholds, measure_weights,
        contract_id, year, n_simulations
    )
    
    # Simulation with improvements
    improved = run_monte_carlo_simulation(
        df, models, thresholds, measure_weights,
        contract_id, year, n_simulations, adjustments=improvements
    )
    
    # Calculate baseline economic value
    baseline_value = 0
    for rating, prob in baseline["rating_probabilities"].items():
        baseline_value += prob * star_values.get(rating, 0)
    
    # Calculate improved economic value
    improved_value = 0
    for rating, prob in improved["rating_probabilities"].items():
        improved_value += prob * star_values.get(rating, 0)
    
    # Calculate change in star rating probability
    prob_changes = {}
    for rating in baseline["rating_probabilities"].keys():
        prob_changes[rating] = improved["rating_probabilities"][rating] - baseline["rating_probabilities"][rating]
    
    return {
        "baseline": {
            "expected_rating": baseline["expected_rating"],
            "rating_probabilities": baseline["rating_probabilities"],
            "economic_value": baseline_value
        },
        "improved": {
            "expected_rating": improved["expected_rating"],
            "rating_probabilities": improved["rating_probabilities"],
            "economic_value": improved_value
        },
        "changes": {
            "expected_rating": improved["expected_rating"] - baseline["expected_rating"],
            "probability_changes": prob_changes,
            "economic_value": improved_value - baseline_value
        }
    }