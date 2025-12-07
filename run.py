from ats.orchestrator import ATSOrchestrator

if __name__ == "__main__":
    universe = ["AAPL", "MSFT", "TSLA", "NVDA"]

    ats = ATSOrchestrator(starting_capital=1000.0)

    result = ats.run_cycle(universe)

    print("\n=== ATS CYCLE COMPLETE ===")
    print("Timestamp:", result["timestamp"])
    print("Portfolio:", result["trader"]["portfolio"])
    print("Fills:", result["trader"]["fills"])
