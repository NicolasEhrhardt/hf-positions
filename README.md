# HF Positions Timeseries

This project generates a Dash application analyzing market value timeseries data from Google Sheets and exports it as a static HTML file.

## Prerequisites

- Python 3.11+
- `uv` package manager
- Google Service Account credentials (`positionsdownloader-b257900bcaa5.json`) in the project root.

## Setup

1. Install dependencies:
   ```bash
   uv sync
   ```

## Usage

Run the script to generate the website:

```bash
uv run main.py
```

The output will be generated at `./website/index.html`.
