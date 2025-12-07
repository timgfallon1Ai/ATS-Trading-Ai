from typing import Any, Dict

from ib_insync import IB, Stock

from ats.config.config_loader import Config


class IBKRFeed:
    """IBKR TWS Real-Time Prices"""

    def __init__(self):
        cfg = Config()
        self.ib = IB()
        self.ib.connect(cfg.ibkr_host(), cfg.ibkr_port(), clientId=cfg.ibkr_client_id())

    def get_price(self, symbol: str) -> Dict[str, Any]:
        contract = Stock(symbol, "SMART", "USD")
        self.ib.qualifyContracts(contract)
        ticker = self.ib.reqMktData(contract, snapshot=True)

        self.ib.sleep(1)

        return {
            "price": float(ticker.last) if ticker.last else float(ticker.close),
            "timestamp": self.ib.reqCurrentTime().isoformat(),
            "source": "ibkr",
            "raw": ticker.__dict__,
        }
