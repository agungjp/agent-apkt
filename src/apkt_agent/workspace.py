"""Workspace management for APKT Agent."""

import json
import random
import string
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from .config import Config


@dataclass
class RunContext:
    """Context for a single data extraction run."""
    
    run_id: str
    dataset: str
    period_ym: str
    snapshot_date: str
    run_dir: Path
    raw_dir: Path
    excel_dir: Path
    parsed_dir: Path
    logs_dir: Path
    manifest_path: Path

    def to_dict(self) -> dict:
        """Convert RunContext to dictionary for JSON serialization."""
        data = asdict(self)
        # Convert Path objects to strings for JSON serialization
        for key in ['run_dir', 'raw_dir', 'excel_dir', 'parsed_dir', 'logs_dir', 'manifest_path']:
            data[key] = str(data[key])
        return data


def create_run(
    dataset: str,
    period_ym: str,
    snapshot_date: str,
    config: Config,
) -> RunContext:
    """Create a new run context with directory structure.
    
    Args:
        dataset: Dataset name (e.g., 'se004_kumulatif')
        period_ym: Period in YYYYMM format (e.g., '202512')
        snapshot_date: Snapshot date in YYYYMMDD format (e.g., '20250106')
        config: Configuration object
        
    Returns:
        RunContext with initialized directories and manifest
        
    Raises:
        ValueError: If parameters are invalid
    """
    # Validate period format
    if not (isinstance(period_ym, str) and len(period_ym) == 6 and period_ym.isdigit()):
        raise ValueError(f"Invalid period_ym format: {period_ym}. Expected YYYYMM.")
    
    # Validate snapshot_date format
    if not (isinstance(snapshot_date, str) and len(snapshot_date) == 8 and snapshot_date.isdigit()):
        raise ValueError(f"Invalid snapshot_date format: {snapshot_date}. Expected YYYYMMDD.")
    
    # Generate run_id
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    run_id = f"{timestamp}_{dataset}_{period_ym}_{random_suffix}"
    
    # Create directory structure
    workspace_root = Path(config.get('workspace.root', './workspace'))
    runs_dir = workspace_root / 'runs' / run_id
    
    raw_dir = runs_dir / 'raw'
    excel_dir = raw_dir / 'excel'
    parsed_dir = runs_dir / 'parsed'
    logs_dir = runs_dir / 'logs'
    
    # Create all directories
    excel_dir.mkdir(parents=True, exist_ok=True)
    parsed_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Create RunContext
    manifest_path = runs_dir / 'manifest.json'
    ctx = RunContext(
        run_id=run_id,
        dataset=dataset,
        period_ym=period_ym,
        snapshot_date=snapshot_date,
        run_dir=runs_dir,
        raw_dir=raw_dir,
        excel_dir=excel_dir,
        parsed_dir=parsed_dir,
        logs_dir=logs_dir,
        manifest_path=manifest_path,
    )
    
    # Create and save manifest
    manifest = {
        'run_id': run_id,
        'dataset': dataset,
        'period_ym': period_ym,
        'snapshot_date': snapshot_date,
        'created_at': datetime.now().isoformat(),
        'directories': {
            'run_dir': str(runs_dir),
            'raw_dir': str(raw_dir),
            'excel_dir': str(excel_dir),
            'parsed_dir': str(parsed_dir),
            'logs_dir': str(logs_dir),
        }
    }
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    return ctx
