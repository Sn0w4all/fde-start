from datetime import datetime
from pathlib import Path
import json 

def save_data(data, data_type = "raw"):
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H-%M-%S")
    core_folder = Path(__file__).parent.parent.parent.parent / "data"
    folder = Path(f"{core_folder}/{data_type}_{date}")
    folder.mkdir(parents=True, exist_ok=True)   # создаст папку, если её нет
    path = folder / f"data_{time}.json"
    print(f"Saving {data_type} data to {path}")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)