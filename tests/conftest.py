import sys
import pathlib

# Ensure project root is on sys.path so tests can import top-level modules
ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
