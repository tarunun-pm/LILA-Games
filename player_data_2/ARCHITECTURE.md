# ARCHITECTURE

## What this repo does

This project turns **raw player-event parquet files** (`data/raw/`) into:

- **Per-match JSON**: `data/processed/matches/<match_id>.json`
- **Heatmap JSON**: `data/processed/heatmaps/<map_id>_heatmaps.json`
- **Index**: `data/processed/index.json` (match metadata used by the app)

Then the Streamlit app (`app.py`) renders trails/events on a **1024×1024 minimap** from `assets/minimaps/`.

## Data flow

- **Raw → Processed**: `scripts/process_data.py`
  - Reads `data/raw/<day>/*.nakama-0`
  - Decodes `event` bytes (e.g., `b'Position' → 'Position'`)
  - Classifies bots vs humans by `user_id` (UUID → human, numeric-ish → bot)
  - Converts world coordinates \((x,z)\) into minimap pixels \((pixel_x,pixel_y)\)
- **Processed → UI**: `app.py`
  - Reads `data/processed/index.json` to populate filters
  - Loads match JSON + heatmaps + minimap image and overlays traces

## Coordinate mapping (world → minimap pixels)

Each map has a configuration:

- **scale**: size of the playable world mapped into UV space
- **origin_x / origin_z**: world-space origin for the minimap mapping

Conversion for a world point \((x,z)\):

1) **World → UV** (0–1):

\[
u = \frac{x - origin_x}{scale}, \quad v = \frac{z - origin_z}{scale}
\]

2) **UV → pixels** on a 1024×1024 image:

\[
pixel_x = u \cdot 1024,\quad pixel_y = (1 - v)\cdot 1024
\]

**Why \(1 - v\)?** Image coordinates start at the **top-left**, while world coordinates typically treat “up” as increasing \(z\). The flip aligns world north/south with screen up/down.

## Important notes

- The `y` column in the parquet is **elevation** and is **not** used for 2D minimap plotting.
- The app expects processed data to exist; if `data/processed/index.json` is missing, run `scripts/process_data.py` first.

