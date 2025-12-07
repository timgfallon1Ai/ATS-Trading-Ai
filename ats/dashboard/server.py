import os

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


class ATSDashboard:
    """Provides live dashboard for ATS state."""

    def __init__(self, results_folder="data/backtest_results"):
        self.results_folder = results_folder
        self.app = FastAPI()

        # Mount static files (JS/CSS)
        self.app.mount(
            "/static", StaticFiles(directory="ats/dashboard/static"), name="static"
        )

        # Templates
        self.templates = Jinja2Templates(directory="ats/dashboard/templates")

        # Routes
        self._define_routes()

    # ------------------------------------------------------------------
    def _define_routes(self):
        @self.app.get("/", response_class=HTMLResponse)
        async def index(request: Request):
            return self.templates.TemplateResponse("index.html", {"request": request})

        @self.app.get("/equity", response_class=HTMLResponse)
        async def equity(request: Request):
            df = self._load_equity()
            return self.templates.TemplateResponse(
                "equity.html",
                {
                    "request": request,
                    "timestamps": df.timestamp.tolist(),
                    "values": df.portfolio_value.tolist(),
                },
            )

        @self.app.get("/executions", response_class=HTMLResponse)
        async def executions(request: Request):
            df = self._load_executions()
            return self.templates.TemplateResponse(
                "executions.html",
                {"request": request, "rows": df.to_dict(orient="records")},
            )

        @self.app.get("/posture", response_class=HTMLResponse)
        async def posture(request: Request):
            df = self._load_posture()
            return self.templates.TemplateResponse(
                "posture.html",
                {"request": request, "rows": df.to_dict(orient="records")},
            )

        @self.app.get("/governance", response_class=HTMLResponse)
        async def governance(request: Request):
            path = f"{self.results_folder}/governance.csv"
            if not os.path.exists(path):
                return HTMLResponse("<h2>No governance log found.</h2>")
            df = pd.read_csv(path)
            return self.templates.TemplateResponse(
                "governance.html",
                {"request": request, "rows": df.to_dict(orient="records")},
            )

    # ------------------------------------------------------------------
    def _load_equity(self):
        return pd.read_csv(f"{self.results_folder}/equity_curve.csv")

    def _load_executions(self):
        path = f"{self.results_folder}/executions.csv"
        return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

    def _load_posture(self):
        path = f"{self.results_folder}/posture.csv"
        return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()


# Entry point
def create_app():
    dashboard = ATSDashboard()
    return dashboard.app
