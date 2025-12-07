class RM4Posture:
    """Adjusts trading behavior based on posture:

    NORMAL:
        full trading

    HEIGHTENED:
        - reduce allocations by 30%
        - only top-scoring symbols allowed

    ALERT:
        - reduce allocations by 60%
        - block risky symbols entirely

    HALT:
        - block all trading
    """

    def adjust_allocations(self, allocations, posture: str):
        if posture == "NORMAL":
            return allocations

        adjusted = []

        for alloc in allocations:
            new_alloc = alloc.copy()

            if posture == "HEIGHTENED":
                new_alloc["alloc_dollars"] *= 0.70

            elif posture == "ALERT":
                new_alloc["alloc_dollars"] *= 0.40

            elif posture == "HALT":
                new_alloc["alloc_dollars"] = 0.0

            adjusted.append(new_alloc)

        return adjusted
