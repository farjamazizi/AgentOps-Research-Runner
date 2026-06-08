PYTHON ?= /home/farjam/miniconda3/envs/agentops_research_agent/bin/python
CLI ?= /home/farjam/miniconda3/envs/agentops_research_agent/bin/agentops-research-agent

.PHONY: install test check run docker-build docker-run

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e ".[dev]"

test:
	$(PYTHON) -m pytest

check:
	$(PYTHON) -m py_compile research_agent.py src/agentops_research_agent/*.py
	$(PYTHON) -m pytest

run:
	$(CLI) run

docker-build:
	docker build -t agentops-research-agent:latest .

docker-run:
	docker compose run --rm research-agent
