from datetime import datetime
from pathlib import Path
import json 

def save_raw_data(raw_data):
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H-%M-%S")
    core_folder = Path(__file__).parent.parent.parent.parent / "data"
    folder = Path(f"{core_folder}/raw_{date}")
    folder.mkdir(parents=True, exist_ok=True)   # создаст папку, если её нет
    path = folder / f"raw_data_{time}.json"
    print(f"Saving raw data to {path}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(raw_data, f, ensure_ascii=False, indent=2)