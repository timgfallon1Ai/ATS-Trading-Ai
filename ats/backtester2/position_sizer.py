# ats/backtester2/position_sizer.py

from __future__ import annotations

from typing import Dict


class PositionSizer:
    """Converts normalized signals ([-1,1]) into portfolio target sizes.

    Core Logic:
    -----------
    - Base capital is assumed to be $1,000.
    - After equity grows by +$1,000:
        system enters 'AGGRESSIVE' mode (2× sizing multiplier by default).

    Output:
        { symbol: target_notional_dollars }
    """

    def __init__(
        self,
        base_capital: float = 1_000.0,
        aggressive_threshold: float = 2_000.0,  # base_capital + 1,000 profit
        aggressive_multiplier: float = 2.0,
        max_single_position_pct: float = 0.25,  # 25% portfolio cap per symbol
    ):
        self.base_capital = base_capital
        self.aggressive_threshold = aggressive_threshold
        self.aggressive_multiplier = aggressive_multiplier
        self.max_single_position_pct = max_single_position_pct

    # ------------------------------------------------------------------
    # Main API
    # ------------------------------------------------------------------
    def size_positions(
        self, cleaned_signals: Dict[str, float], equity: float
    ) -> Dict[str, float]:
        """cleaned_signals: { symbol: float } from PostRiskCombiner
        equity: current portfolio value
        """
        if not cleaned_signals:
            return {}

        # Determine sizing mode
        if equity >= self.aggressive_threshold:
            mode_multiplier = self.aggressive_multiplier
        else:
            mode_multiplier = 1.0

        # Allow only a portion of equity per symbol
        per_symbol_cap = equity * self.max_single_position_pct

        sized: Dict[str, float] = {}

        for symbol, signal_strength in cleaned_signals.items():
            # Convert signal strength into notional exposure
            # Example:
            #   signal = 0.4, equity = 1500 → target = 600
            raw_target = signal_strength * equity * mode_multiplier

            # Cap position size to avoid concentration
            if raw_target > per_symbol_cap:
                raw_target = per_symbol_cap
            elif raw_target < -per_symbol_cap:
                raw_target = -per_symbol_cap

            sized[symbol] = raw_target

        return sized
