# mintmaker-schedule-calculator

This repo contains the backend side of MintMaker's schedule timers in the UI.

### What it does
This module fetches CronJob schedules from OpenShift clusters and parses
Renovate configuration to extract manager schedules. It calculates the
next `n` scheduled runs and writes results to `.txt` files:
- general schedule to `general_scheduled_times.txt`
- one file per manager to `<manager>_scheduled_times.txt`

## Requirements

- Python **3.12**
- [`uv`](https://docs.astral.sh/uv/)
- `oc` CLI (only required if you want to fetch the CronJob schedule from an OpenShift cluster)

## Setup (with uv)

From the repo root:

```bash
uv python install 3.12
uv venv --python 3.12
uv sync
```

Verify:

```bash
uv run python -V
```

## Run

The recommended way to run is as a module.

### Basic usage

```bash
uv run python -m mintmaker_schedule_calculator -n 5 -c renovate.json
```

- `-n / --count`: number of upcoming runs to calculate (default: `5`)
- `-c / --config`: path to a `renovate.json` file (default: `renovate.json`)

To show help/usage hint with options, run:

```bash
uv run python -m mintmaker_schedule_calculator -h
```

### Notes

- The script shells out to `oc` to read the `create-dependencyupdatecheck` CronJob schedule from the `mintmaker` namespace. Make sure you are logged in (`oc login ...`) and have access to that cluster/namespace.
