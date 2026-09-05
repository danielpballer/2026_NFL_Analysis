PY ?= python3
export PYTHONPATH := src

.PHONY: all fetch inputs run backtest test clean

all: inputs run

fetch:            ## download nflverse raw files into data/raw
	$(PY) -m nflsim.fetch_data

inputs:           ## rebuild injuries JSON from data/research + overrides
	$(PY) -m nflsim.build_manual

run:              ## build Week 1 predictions into output/
	$(PY) -m nflsim.run_week1
	$(PY) -m nflsim.compare
	$(PY) -m nflsim.page

backtest:         ## score the method on 2025 Week 1 using 2024 data
	$(PY) -m nflsim.backtest

test:
	$(PY) -m pytest -q tests

clean:
	rm -rf output/*.csv output/*.json output/*.md output/*.html data/processed/*
