.PHONY: build up up-detach logs test lint clean backtest2 install-rg

build:
	docker compose build

up:
	docker compose up --build

up-detach:
	docker compose up --build -d

logs:
	docker compose logs -f

test:
	source .venv/bin/activate && pytest -q

lint:
	source .venv/bin/activate && ruff check . && black --check .

clean:
	docker compose down --volumes --remove-orphans

backtest2:
	source .venv/bin/activate && python -m ats.backtester2.run $(ARGS)

install-rg:
	bash tools/install_ripgrep.sh
