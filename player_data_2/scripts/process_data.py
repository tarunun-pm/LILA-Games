import glob
import json
import os
import uuid

import numpy as np
import pandas as pd

# Map Configurations from README
MAP_CONFIG = {
    "AmbroseValley": {"scale": 900, "origin_x": -370, "origin_z": -473},
    "GrandRift": {"scale": 581, "origin_x": -290, "origin_z": -290},
    "Lockdown": {"scale": 1000, "origin_x": -500, "origin_z": -500},
}

GRID_SIZE = 64
PIXELS = 1024
DAY_FOLDERS = ["February_10", "February_11", "February_12", "February_13", "February_14"]

def is_valid_uuid(val):
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False

def world_to_pixel(x, z, map_id):
    if map_id not in MAP_CONFIG:
        return None, None
    
    config = MAP_CONFIG[map_id]
    scale = config["scale"]
    origin_x = config["origin_x"]
    origin_z = config["origin_z"]
    
    # Step 1: Convert world coords to UV (0-1 range)
    u = (x - origin_x) / scale
    v = (z - origin_z) / scale
    
    # Step 2: Convert UV to pixel coords (1024x1024 image)
    pixel_x = u * PIXELS
    pixel_y = (1 - v) * PIXELS  # Y is flipped (image origin is top-left)
    
    return pixel_x, pixel_y

def process_file(filepath):
    """Parses a single parquet file and applies transformations."""
    try:
        df = pd.read_parquet(filepath)
        
        # 1. Implement event decoder (bytes -> string)
        if 'event' in df.columns:
            df['event'] = df['event'].apply(lambda x: x.decode('utf-8') if isinstance(x, bytes) else str(x))
        
        # 2. Create human/bot classifier
        df['is_bot'] = df['user_id'].apply(lambda x: not is_valid_uuid(x))
        
        # 3. Implement coordinate transformation
        def transform(row):
            px, py = world_to_pixel(row['x'], row['z'], row['map_id'])
            return pd.Series({'pixel_x': px, 'pixel_y': py})
        
        coords = df.apply(transform, axis=1)
        df = pd.concat([df, coords], axis=1)
        
        return df
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return None

def compute_heatmap(df, event_types):
    filtered_df = df[df['event'].isin(event_types)].dropna(subset=['pixel_x', 'pixel_y'])
    if filtered_df.empty:
        return np.zeros((GRID_SIZE, GRID_SIZE)).tolist()
    
    # Use numpy histogram2d
    H, xedges, yedges = np.histogram2d(
        filtered_df['pixel_y'], filtered_df['pixel_x'], # y, x because rows, cols
        bins=GRID_SIZE, 
        range=[[0, PIXELS], [0, PIXELS]]
    )
    return H.tolist()

def aggregate_data(base_path):
    """Iterates through all files and aggregates data."""
    all_data = []
    raw_data_dir = os.path.join(base_path, "data", "raw")
    processed_data_dir = os.path.join(base_path, "data", "processed")
    matches_dir = os.path.join(processed_data_dir, "matches")
    heatmaps_dir = os.path.join(processed_data_dir, "heatmaps")
    
    os.makedirs(matches_dir, exist_ok=True)
    os.makedirs(heatmaps_dir, exist_ok=True)
    
    match_metadata = {}
    map_dfs = {}
    
    for day in DAY_FOLDERS:
        folder_path = os.path.join(raw_data_dir, day)
        if not os.path.exists(folder_path):
            continue
            
        print(f"Processing day: {day}...")
        files = glob.glob(os.path.join(folder_path, "*"))
        
        for f in files:
            # Skip hidden files like .DS_Store
            if os.path.basename(f).startswith('.'):
                continue
            df = process_file(f)
            if df is not None:
                df['date'] = day
                all_data.append(df)
    
    if not all_data:
        print("No data found!")
        return
    
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df = combined_df.sort_values(by=['match_id', 'ts'])
    
    print("Generating per-match files and index...")
    grouped = combined_df.groupby('match_id')
    
    for match_id, group in grouped:
        map_id = group['map_id'].iloc[0]
        date = group['date'].iloc[0]
        
        if map_id not in map_dfs:
            map_dfs[map_id] = []
        map_dfs[map_id].append(group)
        
        # Compute match start time for normalization
        raw_ts_values = []
        for _, row in group.iterrows():
            if hasattr(row['ts'], 'timestamp'):
                raw_ts_values.append(int(row['ts'].timestamp()))
            else:
                raw_ts_values.append(int(row['ts']))
        match_start_ts = min(raw_ts_values) if raw_ts_values else 0
        match_end_ts = max(raw_ts_values) if raw_ts_values else 0
        match_duration_s = match_end_ts - match_start_ts
        
        match_data = {
            "match_id": match_id,
            "map_id": map_id,
            "date": date,
            "match_duration_s": match_duration_s,
            "players": {}
        }
        
        human_count = 0
        bot_count = 0
        
        player_groups = group.groupby('user_id')
        for user_id, p_group in player_groups:
            is_bot = bool(p_group['is_bot'].iloc[0])
            if is_bot: 
                bot_count += 1
            else: 
                human_count += 1
                
            events = []
            for _, row in p_group.iterrows():
                if pd.notnull(row['pixel_x']) and pd.notnull(row['pixel_y']):
                    # Convert to epoch seconds then normalize to match-elapsed
                    if hasattr(row['ts'], 'timestamp'):
                        abs_ts = int(row['ts'].timestamp())
                    else:
                        abs_ts = int(row['ts'])
                    elapsed_s = abs_ts - match_start_ts
                    
                    events.append({
                        "ts": elapsed_s,
                        "event": row['event'],
                        "x": float(row['pixel_x']),
                        "y": float(row['pixel_y'])
                    })
            
            match_data["players"][user_id] = {
                "is_bot": is_bot,
                "events": events
            }
        
        # Save match file
        match_file = os.path.join(matches_dir, f"{match_id}.json")
        with open(match_file, 'w') as f:
            json.dump(match_data, f)
            
        # Add to index
        match_metadata[match_id] = {
            "map_id": map_id,
            "date": date,
            "human_count": human_count,
            "bot_count": bot_count,
            "total_players": human_count + bot_count,
            "duration_s": match_duration_s
        }

    # Generate index.json
    index_data = {
        "dates": DAY_FOLDERS,
        "matches": match_metadata
    }
    with open(os.path.join(processed_data_dir, "index.json"), 'w') as f:
        json.dump(index_data, f)
        
    print("Generating heatmaps...")
    for map_id, dfs in map_dfs.items():
        map_df = pd.concat(dfs, ignore_index=True)
        
        heatmaps = {
            "kill_density": compute_heatmap(map_df, ["Kill", "BotKill"]),
            "death_density": compute_heatmap(map_df, ["Killed", "BotKilled"]),
            "traffic_density": compute_heatmap(map_df, ["Position", "BotPosition"]),
            "storm_deaths": compute_heatmap(map_df, ["KilledByStorm"])
        }
        
        with open(os.path.join(heatmaps_dir, f"{map_id}_heatmaps.json"), 'w') as f:
            json.dump(heatmaps, f)

    print("Data processing complete.")

if __name__ == "__main__":
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    aggregate_data(BASE_PATH)
