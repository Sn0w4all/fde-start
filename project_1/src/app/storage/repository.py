from datetime import datetime
from pathlib import Path
import json 
import logging
logger = logging.getLogger(__name__)

def save_data(data, data_type = "raw"):
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H-%M-%S")
    core_folder = Path(__file__).parent.parent.parent.parent / "data"
    folder = Path(f"{core_folder}/{data_type}_{date}")
    folder.mkdir(parents=True, exist_ok=True)   # создаст папку, если её нет
    path = folder / f"{data_type}_data_{time}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Saving %s data to %s", data_type, path)


def load_latest_data(data_type  = "raw"):
    #Находит самый свежий JSON файл в папке и подпапках и загружает его
    
    folder = Path(__file__).parent.parent.parent.parent / "data"
    folder_path = str(folder)
    if not folder.exists():
        logger.error("Папки нет. Данных в %s пока не существует", folder_path)
        return None

    
    # Находим все JSON файлы рекурсивно (в папке и подпапках)
    json_files = list(folder.rglob("*.json"))
    
    # Фильтруем по содержимому имени файла, если задано
    
    json_files = [
        f 
        for f in json_files 
        if data_type in f.name
    ]
    
    if not json_files:
        logger.warning("JSON файлов нет в %s", folder_path)
        return None
    
    # Находим самый свежий файл
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("Загружены данные из: %s", latest_file)
        return data
    except Exception as e:
        logger.error("Ошибка при загрузке файла %s: %s", latest_file, e)
        return None
    