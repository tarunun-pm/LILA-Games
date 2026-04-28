import glob
from pathlib import Path

import pandas as pd

# Get the first nakama-0 file
raw_data_dir = Path(__file__).resolve().parent.parent / "data" / "raw" / "February_10"
files = sorted(glob.glob(str(raw_data_dir / "*.nakama-0")))
if files:
    print(f"Reading file: {files[0]}")
    print("=" * 100)
    
    # Read the Parquet file
    df = pd.read_parquet(files[0])
    
    print(f"File format: Parquet (Binary Columnar Storage)")
    print(f"Total records: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print("\nData Sample (first 10 rows with all columns visible):")
    print(df.head(10).to_string())
    print("\nBasic Statistics:")
    print(df.describe())
else:
    print("No nakama-0 files found")
