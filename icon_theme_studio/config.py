import json, os
from pathlib import Path

CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home()/".config")) / "icon-theme-studio"
CONFIG_FILE = CONFIG_DIR / "themes.json"

def load_metadata() -> dict:
    try: return json.loads(CONFIG_FILE.read_text())
    except (OSError, ValueError): return {"themes": {}}

def save_metadata(data: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    tmp.replace(CONFIG_FILE)
