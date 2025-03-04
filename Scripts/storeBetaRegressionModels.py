from fileCleaning import beta_regression
import pandas as pd

def store_beta_regression_models(df, measure_cols, feature_cols):
    """s
    Create and store beta regression models for each measure.
    
    Args:
        df: DataFrame with historical measure data
        measure_cols: List of measure column names to model
        
    Returns:
        Dictionary mapping measures to their beta regression models and metadata
    """
    models = {}
    
    for measure in measure_cols:
        try:
            # Skip if insufficient data
            if len(df.dropna(subset=[measure])) < 10:
                print(f"Insufficient data for {measure}, skipping")
                continue
                
            # Run the beta regression
            model = beta_regression(df, measure, feature_cols)
            models[measure] = {
                'model': model,
                'feature_cols': feature_cols,
                'target_col': measure
            }
            print(f"Fitted model for {measure}")
            
        except Exception as e:
            print(f"Failed to fit model for {measure}: {e}")
    
    return models
