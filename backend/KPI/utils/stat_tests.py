from scipy.stats import norm
import numpy as np
import math

def compare_to_historical_single_point(yesterday_val: float, historical_values: list[float], alpha=0.05) -> dict:
    """
    Perform z-test and prediction interval check to compare yesterday's value to historical distribution.
    """
    # Filter out any NaNs from the historical list
    historical_values = [x for x in historical_values if isinstance(x, (int, float)) and not math.isnan(x)]

    n = len(historical_values)
    if n < 2:
        return {
            "z_score": None,
            "p_value": None,
            "mean": None,
            "std": None,
            "is_significant": False,
            "insight": "Not enough valid historical data to compare."
        }

    mean = np.mean(historical_values)
    std = np.std(historical_values, ddof=1) 

    if std == 0:
        return {
            "z_score": None,
            "p_value": None,
            "mean": round(mean, 2),
            "std": round(std, 2),
            "is_significant": False,
            "insight": "No variation in historical data."
        }

    z = (yesterday_val - mean) / std

    # Check for NaN or infinite z-scores
    if not np.isfinite(z):
        return {
            "z_score": None,
            "p_value": None,
            "mean": round(mean, 2),
            "std": round(std, 2),
            "is_significant": False,
            "insight": "Invalid z-score due to problematic input values."
        }

    p = 2 * norm.sf(abs(z)) 

    # Prediction interval check
    t_multiplier = 1.96 
    pred_margin = t_multiplier * std * np.sqrt(1 + 1/n)
    lower_bound = mean - pred_margin
    upper_bound = mean + pred_margin
    is_outlier = yesterday_val < lower_bound or yesterday_val > upper_bound

    summary = (
        f"Yesterday’s payment method diversity was {'unusually high' if z > 0 else 'unusually low'} "
        f"compared to the historical average ({mean:.2f}, p = {p:.4f})."
    ) if is_outlier else "Yesterday’s payment method diversity was within the expected range."

    return {
        "z_score": round(z, 2),
        "p_value": round(float(p), 4),
        "mean": round(mean, 2),
        "std": round(std, 2),
        "is_significant": is_outlier,
        "insight": summary,
    }
