import anthropic
import requests
from pathlib import Path
from dotenv import load_dotenv
import os
import json
import logging


logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
load_dotenv(SCRIPT_DIR / "claude_api.env")
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

async def get_html_report(text_reports):
    try:
        if text_reports == None:
            logger.info("Data empty. nothing transform to HTML")
            return None
        html_report = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=20000,
            messages=[
                {
                    "role": "user", 
                    "content": f"Ты дизайнер и аналитик,  твоя задача - созать визуализацию отчета по анализу рыночных значений в HTML. Данные для анализа - {len(text_reports)} блока, расположи их отдельно, но структурированно; сами данные - {json.dumps(text_reports, ensure_ascii=False, indent=2)}. Стиль - спокойный, корпоративный, но приятный глазу, используй не стандартные шрифты."
                }
            ],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "html": {"type": "string"}
                        },
                        "required": ["html"],
                        "additionalProperties": False
                    }
                }
            }
        )

        html = json.loads(html_report.content[0].text) #выгружаем текст (строку) - загружаем в json - достаем поле HTML - убираем кавычки
        return html
    
    except anthropic.BadRequestError as e:
        logger.error("API Error: %s", e)
        raise
    except requests.exceptions.RequestException as e:
        logger.error("Network error %s", e)
        raise
    except json.JSONDecodeError as e: 
        logger.exception("Ошибка парсинга JSON %s,", e)
        raise
         