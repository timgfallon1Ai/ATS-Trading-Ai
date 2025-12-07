import random
from typing import Dict


class LatencyModel:
    """RM-5 Latency Model

    Simulates execution delay:
    - random jitter
    - volatility-based delay scaling
    - entropy-based delay uncertainty
    """

    def compute_latency(self, features: Dict) -> float:
        vol = features.get("rv_15", 0.01)
        entropy = features.get("entropy", 0.5)

        # Base latency (ms)
        base = 20

        # Volatility and entropy add execution delay risk
        delay = base + (vol * 200) + (entropy * 50)

        # Random jitter component
        jitter = random.uniform(0, 30)

        return float(delay + jitter)
