class RM4StateMachine:
    """Defines posture transitions:

    NORMAL → HEIGHTENED → ALERT → HALT

    Transitions occur based on:
    - anomaly score
    - drift score
    - predictive risk (RM-2)
    """

    STATES = ["NORMAL", "HEIGHTENED", "ALERT", "HALT"]

    def __init__(self):
        self.state = "NORMAL"

    def transition(self, anomaly: float, drift: float, predictive_risk: float) -> str:
        """Compute next posture state."""
        # --- Transition to HALT ---
        if anomaly > 0.90 or predictive_risk > 0.80:
            self.state = "HALT"
            return self.state

        # --- Transition to ALERT ---
        if anomaly > 0.70 or drift > 0.75 or predictive_risk > 0.60:
            self.state = "ALERT"
            return self.state

        # --- Transition to HEIGHTENED ---
        if anomaly > 0.40 or drift > 0.50 or predictive_risk > 0.40:
            self.state = "HEIGHTENED"
            return self.state

        # --- Return to NORMAL ---
        self.state = "NORMAL"
        return self.state

    def get_state(self) -> str:
        return self.state
