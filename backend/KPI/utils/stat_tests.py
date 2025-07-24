from scipy.stats import norm
import numpy as np

def compare_to_historical_single_point(yesterday_val: float, historical_values: list[float], alpha=0.05) -> dict:
    """
    Perform z-test and prediction interval check to compare yesterday's value to historical distribution.
    """
    n = len(historical_values)
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


    # Z-test
    z = (yesterday_val - mean) / std
    p = 2 * norm.sf(abs(z)) 

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
        "p_value": round(p, 4),
        "mean": round(mean, 2),
        "std": round(std, 2),
        "is_significant": is_outlier,
        "insight": summary,
    }
