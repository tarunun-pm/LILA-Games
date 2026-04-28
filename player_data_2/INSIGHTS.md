# INSIGHTS

These insights come from the bundled dataset in `data/raw/` and the processed index in `data/processed/index.json`.

## 1) The dataset is **heavily skewed** toward one map

- **AmbroseValley**: 566 / 796 matches (~71%)
- **Lockdown**: 171 / 796 matches (~22%)
- **GrandRift**: 59 / 796 matches (~7%)

**Evidence**: `data/processed/index.json` `matches[*].map_id` distribution.

## 2) The dataset is **player-journey centric**, not “full lobby” centric

- Total match records: **796**
- Total player-journey files: **1,243** (from README)
- Average players recorded per match: **1.56** (1242 total players across 796 matches)

This implies many matches are only partially observed (some players missing), which is expected when logs are collected per-player journey file.

**Evidence**: `index.json` fields `human_count`, `bot_count`, `total_players`.

## 3) Many matches are **extremely short** in the processed metadata

- **57.54%** of matches have `duration_s == 0`
- **100%** of matches have `duration_s < 30`

This strongly suggests the dataset’s `ts` normalization (or raw timestamps) often collapses into very small windows—use `duration_s` carefully and prefer event counts / event ordering within a match when analyzing timelines.

**Evidence**: `index.json` field `duration_s` across matches.

