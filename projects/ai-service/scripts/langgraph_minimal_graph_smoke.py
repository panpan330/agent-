import json
from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.minimal_graph import run_minimal_graph


if __name__ == "__main__":
    result = run_minimal_graph("  你好，LangGraph  ")
    print(json.dumps(result, ensure_ascii=False, indent=2))
