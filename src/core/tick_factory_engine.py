import numpy as np
import pandas as pd
from collections import deque

class StatefulKalman:
    def __init__(self, params):
        self.R = params.get('kalman_R', 0.05)
        self.x = None
        self.P = 1.0
        self.last_price = None
        self.returns = deque(maxlen=50)

    def update_tick(self, price):
        if self.x is None:
            self.x = price
            self.last_price = price
            return price

        # Calculate trailing variance for adaptive Q
        ret = price - self.last_price
        self.returns.append(ret)
        self.last_price = price
        
        var = np.var(self.returns) if len(self.returns) > 1 else 0.001
        Q = var * 0.1

        # Kalman equations
        Pm = self.P + Q
        K = Pm / (Pm + self.R)
        self.x = self.x + K * (price - self.x)
        self.P = (1 - K) * Pm
        
        return self.x

class StatefulMAD:
    def __init__(self, params):
        self.win = params.get('window', 50)
        self.k = params.get('mad_threshold', 3.0)
        self.tolerance = params.get('tolerance', 0.05)
        self.history = deque(maxlen=self.win)

    def update_tick(self, price):
        self.history.append(price)
        if len(self.history) < 2:
            return price
            
        # Trailing median and MAD
        w = np.array(self.history)
        med = np.median(w)
        mad = np.median(np.abs(w - med))
        safe = max(mad, self.tolerance)
        
        # Clip
        return float(np.clip(price, med - self.k * safe, med + self.k * safe))

class StatefulEMAZScore:
    def __init__(self, params):
        self.span = params.get('ema_span', 50)
        self.thresh = params.get('threshold', 3.0)
        self.alpha = 2.0 / (self.span + 1)
        self.ema = None
        self.ema_var = None

    def update_tick(self, price):
        if self.ema is None:
            self.ema = price
            self.ema_var = 0.0
            return price
            
        diff = price - self.ema
        self.ema += self.alpha * diff
        self.ema_var = (1 - self.alpha) * (self.ema_var + self.alpha * diff**2)
        std = np.sqrt(self.ema_var)
        
        upper = self.ema + self.thresh * std
        lower = self.ema - self.thresh * std
        return float(np.clip(price, lower, upper))

class StatefulHampel:
    def __init__(self, params):
        self.win = params.get('half_window', 15) * 2  # trailing window size
        self.k = params.get('k_sigma', 3.0)
        self.history = deque(maxlen=self.win)
        
    def update_tick(self, price):
        self.history.append(price)
        if len(self.history) < self.win:
            return price
            
        w = np.array(self.history)
        # Exclude the current point for computing local median/mad to avoid self-bias
        w_past = w[:-1]
        med = np.median(w_past)
        mad = np.median(np.abs(w_past - med))
        sigma = 1.4826 * mad
        
        if sigma > 1e-8 and abs(price - med) > self.k * sigma:
            return float(med)
        return price

def vectorized_mad_filter(prices, window=50, threshold=3.0, tolerance=0.05):
    """Vectorized, C-speed MAD filter for backtesting and plotting."""
    s = pd.Series(prices)
    rolling_med = s.rolling(window=window, min_periods=1).median()
    abs_deviation = (s - rolling_med).abs()
    rolling_mad = abs_deviation.rolling(window=window, min_periods=1).median()
    
    safe_mad = np.maximum(rolling_mad, tolerance)
    upper_bound = rolling_med + threshold * safe_mad
    lower_bound = rolling_med - threshold * safe_mad
    
    return np.clip(prices, lower_bound, upper_bound).values

def verify_tick_by_tick(df, filter_type, params):
    """
    Feeds the raw DataFrame through the stateful tick engine sequentially.
    Returns the array of cleaned prices.
    """
    prices = df['Bid'].values
    
    if filter_type == 'MAD':
        return vectorized_mad_filter(
            prices,
            window=params.get('window', 50),
            threshold=params.get('mad_threshold', 3.0),
            tolerance=params.get('tolerance', 0.05)
        )
        
    cleaned = np.zeros(len(prices))
    
    if filter_type == 'ADAPTIVE_KALMAN':
        engine = StatefulKalman(params)
    elif filter_type == 'EMA_ZSCORE':
        engine = StatefulEMAZScore(params)
    elif filter_type == 'HAMPEL':
        engine = StatefulHampel(params)
    elif filter_type == 'DEEP_DENOISE_HAMPEL_KALMAN':
        # Nuclear recovery runs sequentially
        e1 = StatefulHampel({'half_window': 5, 'k_sigma': 2.5}) # win=10
        e2 = StatefulKalman({'kalman_R': 0.1})
        for i in range(len(prices)):
            p1 = e1.update_tick(prices[i])
            cleaned[i] = e2.update_tick(p1)
        return cleaned
    else:
        raise ValueError(f"Unknown filter type for tick engine: {filter_type}")
        
    for i in range(len(prices)):
        cleaned[i] = engine.update_tick(prices[i])
        
    return cleaned
