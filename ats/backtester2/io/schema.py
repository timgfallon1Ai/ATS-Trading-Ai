from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(slots=True)
class Bar:
    """UBF Unified Bar Format (v1.0)

    All bars are 1-minute aligned but may come from any data source
    (Polygon, IBKR, Benzinga, Twitter sentiment, etc).
    """

    timestamp: int  # epoch ms
    open: float
    high: float
    low: float
    close: float
    volume: float

    # Optional extended fields
    vwap: Optional[float] = None
    sentiment: Optional[float] = None
    news_impact: Optional[float] = None
    volatility: Optional[float] = None
    symbol: Optional[str] = None

    extra: Optional[Dict[str, Any]] = None


class UBFSchema:
    """Ensures that an incoming dictionary conforms to Bar."""

    REQUIRED = ["timestamp", "open", "high", "low", "close", "volume"]

    @classmethod
    def validate(cls, raw: Dict[str, Any]) -> bool:
        return all(k in raw for k in cls.REQUIRED)

    @classmethod
    def to_bar(cls, raw: Dict[str, Any]) -> Bar:
        if not cls.validate(raw):
            raise ValueError(f"Malformed UBF bar: missing required fields {raw}")

        return Bar(
            timestamp=int(raw["timestamp"]),
            open=float(raw["open"]),
            high=float(raw["high"]),
            low=float(raw["low"]),
            close=float(raw["close"]),
            volume=float(raw["volume"]),
            vwap=raw.get("vwap"),
            sentiment=raw.get("sentiment"),
            news_impact=raw.get("news_impact"),
            volatility=raw.get("volatility"),
            symbol=raw.get("symbol"),
            extra=raw.get("extra"),
        )
