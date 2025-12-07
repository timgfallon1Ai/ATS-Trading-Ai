from typing import Dict, List

from .drift_detector import DriftDetector
from .rm4_anomaly_detector import RM4AnomalyDetector
from .rm4_posture import RM4Posture
from .rm4_state_machine import RM4StateMachine


class RM4Agent:
    """Full RM-4 engine:
    - anomaly scoring
    - drift scoring
    - posture transitions
    - allocation adjustments
    """

    def __init__(self):
        self.state_machine = RM4StateMachine()
        self.anomaly = RM4AnomalyDetector()
        self.drift = DriftDetector()
        self.posture = RM4Posture()

    def process(
        self,
        allocations: List[Dict],
        predictive: Dict[str, Dict],
        features: Dict[str, Dict],
    ):
        """allocations: RM-3 outputs
        predictive: RM-2 outputs (dict: symbol -> predictive dict)
        features: Analyst features (dict: symbol -> feature vector)
        """
        # Step 1: compute anomaly score (aggregate across symbols)
        anomaly_scores = [self.anomaly.score(features[symbol]) for symbol in features]
        anomaly = max(anomaly_scores) if anomaly_scores else 0

        # Step 2: compute drift score
        # Use average across symbols
        drift_scores = [
            self.drift.score(features[symbol], predictive[symbol]["regime"])
            for symbol in predictive
        ]
        drift = sum(drift_scores) / len(drift_scores) if drift_scores else 0

        # Step 3: compute worst-case predictive risk
        prisk = (
            max(predictive[s]["predictive_risk"] for s in predictive)
            if predictive
            else 0
        )

        # Step 4: state machine transition
        posture = self.state_machine.transition(anomaly, drift, prisk)

        # Step 5: adjust allocations
        adjusted = self.posture.adjust_allocations(allocations, posture)

        return {
            "posture": posture,
            "anomaly": anomaly,
            "drift": drift,
            "predictive_risk": prisk,
            "adjusted_allocations": adjusted,
        }
