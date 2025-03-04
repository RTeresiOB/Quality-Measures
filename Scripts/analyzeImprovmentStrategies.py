import pandas as pd
from storeBetaRegressionModels import store_beta_regression_models
from monteCarloSimulation import run_monte_carlo_simulation
from measureImprovmentValuation import evaluate_measure_improvement_value

def analyze_improvement_strategies(df, thresholds, measure_weights, 
                                 contract_id, year, star_values,
                                 cost_per_point=10000,
                                 n_simulations=1000):
    """
    Analyze different measure improvement strategies.
    
    Args:
        df: DataFrame with historical data
        thresholds: Dictionary of measure thresholds
        measure_weights: Dictionary of measure weights
        contract_id: CONTRACT_ID to analyze
        year: Year to analyze
        star_values: Dictionary mapping star ratings to dollar values
        cost_per_point: Estimated cost per percentage point improvement
        n_simulations: Number of simulations to run
        
    Returns:
        DataFrame with analysis of different improvement strategies
    """
    
    # Extract measure columns
    measure_cols = [col for col in df.columns if col.startswith("C:")]
    
    # Create beta regression models
    models = store_beta_regression_models(df, measure_cols)
    
    # Define improvement scenarios to test
    scenarios = []
    
    # Individual measure improvements (1% each)
    for measure in measure_cols:
        if measure in models:
            scenarios.append({
                "name": f"Improve {measure} by 1%",
                "improvements": {measure: 1.0}
            })
    
    # Combined improvements for high-weight measures
    high_weight_measures = [m for m, w in measure_weights.items() 
                          if w >= 3 and m in models]
    if high_weight_measures:
        scenarios.append({
            "name": "Improve all high-weight measures by 1%",
            "improvements": {m: 1.0 for m in high_weight_measures}
        })
    
    # Evaluate each scenario
    results = []
    
    # First, calculate baseline (no improvements)
    baseline = run_monte_carlo_simulation(
        df, models, thresholds, measure_weights,
        contract_id, year, n_simulations
    )
    baseline_rating = baseline["expected_rating"]
    
    # Get the current weighted average for the contract
    contract_df = df[(df["CONTRACT_ID"] == contract_id) & (df["Year"] == year)]
    
    # For each scenario
    for scenario in scenarios:
        try:
            analysis = evaluate_measure_improvement_value(
                df, models, thresholds, measure_weights,
                contract_id, year, scenario["improvements"],
                star_values, n_simulations
            )
            
            # Calculate ROI
            total_improvement = sum(scenario["improvements"].values())
            cost = total_improvement * cost_per_point
            
            net_value = analysis["changes"]["economic_value"]
            roi = net_value / cost if cost > 0 else float('inf')
            
            results.append({
                "scenario": scenario["name"],
                "improvements": str(scenario["improvements"]),  # Convert to string for DataFrame display
                "baseline_rating": baseline_rating,
                "improved_rating": analysis["improved"]["expected_rating"],
                "rating_change": analysis["changes"]["expected_rating"],
                "economic_value_change": net_value,
                "estimated_cost": cost,
                "roi": roi
            })
        except Exception as e:
            print(f"Error evaluating scenario {scenario['name']}: {e}")
    
    # Convert to DataFrame and sort by ROI
    results_df = pd.DataFrame(results).sort_values("roi", ascending=False)
    
    return results_df