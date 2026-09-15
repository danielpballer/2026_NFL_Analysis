PY ?= python3
WEEK ?= 2
export PYTHONPATH := src
export NFLSIM_WEEK := $(WEEK)

.PHONY: all fetch inputs run backtest test clean

all: inputs run

fetch:            ## download nflverse raw files into data/raw
	$(PY) -m nflsim.fetch_data

inputs:           ## rebuild injuries JSON from data/research + overrides
	$(PY) -m nflsim.build_manual

run:              ## build predictions for WEEK (make run WEEK=2) into output/
	$(PY) -m nflsim.run_week
	$(PY) -m nflsim.compare
	$(PY) -m nflsim.page

backtest:         ## score the method on 2025 Week 1 using 2024 data
	$(PY) -m nflsim.backtest

evaluate:         ## score a completed week (make evaluate WEEK=1)
	$(PY) -m nflsim.evaluate 2026 $(WEEK)

test:
	$(PY) -m pytest -q tests

clean:
	rm -rf output/*.csv output/*.json output/*.md output/*.html data/processed/*
