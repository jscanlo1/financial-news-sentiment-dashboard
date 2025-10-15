import sys
from pathlib import Path

# Add src/ to sys.path
project_root = Path(__file__).resolve().parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
