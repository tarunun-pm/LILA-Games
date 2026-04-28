"""
Data Loading and Exploration Module
Handles Parquet file loading, schema validation, coordinate transformations, 
and data quality assessment for player tracking data.
"""

import pyarrow.parquet as pq
import pandas as pd
import numpy as np
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DataLoader:
    """Load and manage parquet data files."""
    
    EXPECTED_SCHEMA = {
        'user_id': 'string',
        'match_id': 'string',
        'map_id': 'string',
        'x': 'float32',
        'y': 'float32',
        'z': 'float32',
        'ts': 'timestamp',
        'event': 'object'
    }
    
    def __init__(self, data_dir: str):
        """Initialize data loader with directory path."""
        self.data_dir = Path(data_dir)
        self.dataframes: Dict[str, pd.DataFrame] = {}
        self.schema_issues: List[str] = []
        
    def discover_parquet_files(self, max_files: Optional[int] = None) -> List[Path]:
        """Discover all parquet files in data directory."""
        if not self.data_dir.exists():
            logger.error(f"Data directory not found: {self.data_dir}")
            return []
        
        # Find .nakama-0 files (which are parquet format)
        parquet_files = list(self.data_dir.glob('**/*.nakama-0'))
        
        if max_files:
            parquet_files = parquet_files[:max_files]
        
        logger.info(f"Found {len(parquet_files)} parquet files")
        return sorted(parquet_files)
    
    def load_single_file(self, filepath: Path) -> Optional[pd.DataFrame]:
        """Load a single parquet file."""
        try:
            df = pd.read_parquet(filepath)
            logger.debug(f"Loaded {len(df)} rows from {filepath.name}")
            return df
        except Exception as e:
            logger.error(f"Failed to load {filepath.name}: {e}")
            return None
    
    def load_sample_files(self, sample_size: int = 5) -> pd.DataFrame:
        """Load sample parquet files and combine into single dataframe."""
        files = self.discover_parquet_files(max_files=sample_size)
        dfs = []
        
        for filepath in files:
            df = self.load_single_file(filepath)
            if df is not None:
                df['_source_file'] = filepath.name
                dfs.append(df)
        
        if not dfs:
            logger.warning("No files loaded successfully")
            return pd.DataFrame()
        
        combined_df = pd.concat(dfs, ignore_index=True)
        logger.info(f"Combined {len(dfs)} files: {len(combined_df)} total rows")
        return combined_df
    
    def validate_schema(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate dataframe schema against expected schema."""
        issues = []
        
        # Check for required columns
        for col in self.EXPECTED_SCHEMA.keys():
            if col not in df.columns:
                issues.append(f"Missing column: {col}")
        
        # Check data types
        for col, expected_dtype in self.EXPECTED_SCHEMA.items():
            if col not in df.columns:
                continue
            
            actual_dtype = str(df[col].dtype)
            # Flexible type checking
            if expected_dtype == 'timestamp' and 'datetime' not in actual_dtype:
                issues.append(f"Column '{col}': expected timestamp, got {actual_dtype}")
            elif expected_dtype == 'object' and actual_dtype not in ['object', 'bytes']:
                issues.append(f"Column '{col}': expected object, got {actual_dtype}")
            elif expected_dtype == 'string' and actual_dtype not in ['object', 'string']:
                issues.append(f"Column '{col}': expected string, got {actual_dtype}")
            elif expected_dtype in ['float32', 'float64'] and 'float' not in actual_dtype:
                issues.append(f"Column '{col}': expected float, got {actual_dtype}")
        
        self.schema_issues = issues
        valid = len(issues) == 0
        logger.info(f"Schema validation: {'PASS' if valid else 'FAIL'}")
        
        for issue in issues:
            logger.warning(f"  - {issue}")
        
        return valid, issues


class CoordinateTransformer:
    """Handle coordinate transformations and validations."""
    
    # Map dimensions (estimated based on typical game worlds)
    MAP_BOUNDS = {
        'AmbroseValley': {'x': (0, 1000), 'y': (0, 1000), 'z': (0, 500)},
        'GrandRift': {'x': (0, 1200), 'y': (0, 1200), 'z': (0, 400)},
        'Lockdown': {'x': (0, 800), 'y': (0, 800), 'z': (0, 300)},
    }
    
    @staticmethod
    def normalize_coordinates(df: pd.DataFrame, map_id: str = None) -> pd.DataFrame:
        """Normalize coordinates to 0-1 range."""
        df = df.copy()
        
        if map_id and map_id in CoordinateTransformer.MAP_BOUNDS:
            bounds = CoordinateTransformer.MAP_BOUNDS[map_id]
        else:
            # Use min-max scaling from data
            bounds = {
                'x': (df['x'].min(), df['x'].max()),
                'y': (df['y'].min(), df['y'].max()),
                'z': (df['z'].min(), df['z'].max()),
            }
        
        for axis in ['x', 'y', 'z']:
            min_val, max_val = bounds[axis]
            if max_val > min_val:
                df[f'{axis}_norm'] = (df[axis] - min_val) / (max_val - min_val)
            else:
                df[f'{axis}_norm'] = 0.0
        
        return df
    
    @staticmethod
    def calculate_distance(df: pd.DataFrame, p1_idx: int, p2_idx: int) -> float:
        """Calculate Euclidean distance between two points."""
        if p1_idx >= len(df) or p2_idx >= len(df):
            return None
        
        p1 = df.iloc[p1_idx][['x', 'y', 'z']].values
        p2 = df.iloc[p2_idx][['x', 'y', 'z']].values
        
        return np.linalg.norm(p1 - p2)
    
    @staticmethod
    def test_transformations(df: pd.DataFrame) -> Dict:
        """Test coordinate transformations."""
        results = {}
        
        # Test normalization
        df_norm = CoordinateTransformer.normalize_coordinates(df)
        results['normalized_stats'] = {
            'x_norm_range': (df_norm['x_norm'].min(), df_norm['x_norm'].max()),
            'y_norm_range': (df_norm['y_norm'].min(), df_norm['y_norm'].max()),
            'z_norm_range': (df_norm['z_norm'].min(), df_norm['z_norm'].max()),
        }
        
        # Test distance calculations (sample)
        if len(df) > 1:
            distances = []
            for i in range(min(10, len(df) - 1)):
                dist = CoordinateTransformer.calculate_distance(df, i, i + 1)
                if dist is not None:
                    distances.append(dist)
            
            results['distance_stats'] = {
                'sample_count': len(distances),
                'mean_distance': np.mean(distances) if distances else 0,
                'max_distance': np.max(distances) if distances else 0,
                'min_distance': np.min(distances) if distances else 0,
            }
        
        return results


class DataQualityAnalyzer:
    """Analyze data quality issues."""
    
    @staticmethod
    def analyze_missing_values(df: pd.DataFrame) -> Dict:
        """Identify missing values."""
        missing = {}
        
        for col in df.columns:
            missing_count = df[col].isna().sum()
            missing_pct = (missing_count / len(df)) * 100 if len(df) > 0 else 0
            
            if missing_count > 0:
                missing[col] = {
                    'count': missing_count,
                    'percentage': round(missing_pct, 2)
                }
        
        return missing if missing else {'status': 'No missing values'}
    
    @staticmethod
    def analyze_coordinate_outliers(df: pd.DataFrame, threshold_std: float = 3.0) -> Dict:
        """Identify coordinate outliers using z-score."""
        outliers = {}
        
        for axis in ['x', 'y', 'z']:
            if axis not in df.columns:
                continue
            
            mean = df[axis].mean()
            std = df[axis].std()
            
            if std == 0:
                outlier_count = 0
            else:
                z_scores = np.abs((df[axis] - mean) / std)
                outlier_count = (z_scores > threshold_std).sum()
            
            outliers[axis] = {
                'mean': round(float(mean), 2),
                'std': round(float(std), 2),
                'outlier_count': int(outlier_count),
                'outlier_pct': round((outlier_count / len(df)) * 100, 2) if len(df) > 0 else 0
            }
        
        return outliers
    
    @staticmethod
    def analyze_event_distribution(df: pd.DataFrame) -> Dict:
        """Analyze event type distribution."""
        if 'event' not in df.columns:
            return {'status': 'No event column'}
        
        event_counts = df['event'].value_counts()
        total = len(df)
        
        distribution = {}
        for event, count in event_counts.items():
            try:
                event_str = event.decode('utf-8') if isinstance(event, bytes) else str(event)
            except:
                event_str = str(event)
            
            distribution[event_str] = {
                'count': int(count),
                'percentage': round((count / total) * 100, 2)
            }
        
        return distribution
    
    @staticmethod
    def analyze_human_bot_ratio(df: pd.DataFrame) -> Dict:
        """Analyze human vs bot distribution."""
        if 'event' not in df.columns:
            return {'status': 'Cannot determine from available data'}
        
        # This is a placeholder - actual logic depends on how humans/bots are marked
        # Could be based on event patterns, user IDs, or explicit field
        total_users = df['user_id'].nunique() if 'user_id' in df.columns else 0
        
        return {
            'total_unique_users': int(total_users),
            'note': 'Bot detection logic not yet implemented - requires domain knowledge'
        }
    
    @staticmethod
    def generate_report(df: pd.DataFrame) -> Dict:
        """Generate comprehensive quality report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'missing_values': DataQualityAnalyzer.analyze_missing_values(df),
            'coordinate_outliers': DataQualityAnalyzer.analyze_coordinate_outliers(df),
            'event_distribution': DataQualityAnalyzer.analyze_event_distribution(df),
            'human_bot_ratio': DataQualityAnalyzer.analyze_human_bot_ratio(df),
            'temporal_info': {
                'date_range_start': str(df['ts'].min()) if 'ts' in df.columns else None,
                'date_range_end': str(df['ts'].max()) if 'ts' in df.columns else None,
            }
        }
        
        return report


def main():
    """Main data exploration workflow."""
    
    # Setup paths
    data_dir = Path(__file__).parent.parent / 'data' / 'raw' / 'February_10'
    
    logger.info("=" * 80)
    logger.info("DATA EXPLORATION WORKFLOW")
    logger.info("=" * 80)
    
    # 1. Load data
    logger.info("\n[1/4] Loading sample data files...")
    loader = DataLoader(str(data_dir))
    df = loader.load_sample_files(sample_size=5)
    
    if df.empty:
        logger.error("No data loaded. Exiting.")
        return
    
    # 2. Validate schema
    logger.info("\n[2/4] Validating schema...")
    valid, issues = loader.validate_schema(df)
    
    # 3. Test coordinate transformations
    logger.info("\n[3/4] Testing coordinate transformations...")
    transformer = CoordinateTransformer()
    transform_results = transformer.test_transformations(df)
    
    logger.info("  Normalized coordinate ranges:")
    for axis, (min_v, max_v) in transform_results['normalized_stats'].items():
        logger.info(f"    {axis}: [{min_v:.4f}, {max_v:.4f}]")
    
    if 'distance_stats' in transform_results:
        logger.info("  Distance statistics (consecutive points):")
        stats = transform_results['distance_stats']
        logger.info(f"    Sample count: {stats['sample_count']}")
        logger.info(f"    Mean: {stats['mean_distance']:.2f}")
        logger.info(f"    Range: [{stats['min_distance']:.2f}, {stats['max_distance']:.2f}]")
    
    # 4. Analyze data quality
    logger.info("\n[4/4] Analyzing data quality...")
    analyzer = DataQualityAnalyzer()
    quality_report = analyzer.generate_report(df)
    
    logger.info(f"\n  Total rows: {quality_report['row_count']}")
    logger.info(f"  Columns: {', '.join(quality_report['columns'])}")
    
    logger.info("\n  Missing values:")
    missing = quality_report['missing_values']
    if isinstance(missing, dict) and 'status' in missing:
        logger.info(f"    {missing['status']}")
    else:
        for col, info in missing.items():
            logger.info(f"    {col}: {info['count']} ({info['percentage']}%)")
    
    logger.info("\n  Coordinate outliers (3σ threshold):")
    for axis, info in quality_report['coordinate_outliers'].items():
        logger.info(f"    {axis}: {info['outlier_count']} outliers ({info['outlier_pct']}%)")
    
    logger.info("\n  Event distribution:")
    for event, info in quality_report['event_distribution'].items():
        logger.info(f"    {event}: {info['count']} ({info['percentage']}%)")
    
    logger.info("\n  Temporal range:")
    logger.info(f"    Start: {quality_report['temporal_info']['date_range_start']}")
    logger.info(f"    End: {quality_report['temporal_info']['date_range_end']}")
    
    logger.info("\n" + "=" * 80)
    logger.info("DATA EXPLORATION COMPLETE")
    logger.info("=" * 80)
    
    return df, quality_report


if __name__ == '__main__':
    df, report = main()
