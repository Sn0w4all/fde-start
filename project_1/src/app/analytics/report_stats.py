import anthropic
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

def get_analysis(normalized_data):
    reports = []
    prompt_path = Path(__file__).parent / "analytics_prompt.md"
    prompt_file = str(prompt_path)
    try:
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except Exception as e:
        logger.error("Ошибка при загрузке промпта из %s",prompt_path)
        return None
    

    try:
        for position, data in normalized_data.items():
            params = {
                "position": position,
                "normalized_data": normalized_data,
                "data": json.dumps(data, ensure_ascii=False, indent=2)                     
            }
            prompt = prompt_template.format_map(params)
    
            comment = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1200,
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                output_config={
                    "format": {
                        "type": "json_schema",
                        "schema": {
                            "type": "object",
                            "properties": {
                                "ticker_name": {"type": "string", "description": "Идентификатор тикера"}, 
                                "ticker_description": {"type": "string", "description": "Описание тикера"}, 
                                "ticker_params": {"type": "string", "description": "Значений цены позиции"}, 
                                "ticker_metrics": {"type": "string", "description": "Аналитические меторики"}, 
                                "position_analys": {"type": "string", "description": "Анализ ценовых значений по тикеру"}, 
                                "correlation_analys": {"type": "string", "description": "Анализ корреляций"}, 
                                "summary": {"type": "string", "description": "Вывод"}, 
                            },
                            "required": ["ticker_name"],
                            "additionalProperties": False
                        }
                    }
                }
            )
            report = {
                "Position": position,
                "Comment": comment.content[0].text
            }
            reports.append(report)
            logger.info("Сгенерирован комментарий для позиции %s", position)
        return reports

    except anthropic.BadRequestError as e:
        logger.error("API Error: %s", e)
        return None
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        return None