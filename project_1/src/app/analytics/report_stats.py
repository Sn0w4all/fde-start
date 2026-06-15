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
    try:
        for position, data in normalized_data.items():
            comment = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1200,
                messages=[
                    {
                        "role": "user", 
                        "content": f"Ты финансовый аналитик,  опиши и прокомментируй(без рекомендаций) по активу {position} значения цены сегодня: {json.dumps(data, ensure_ascii=False, indent=2)}.  Что это может означать для трейдера? Используй для оценки корреляции следующие значения {normalized_data}"
                    }
                ],
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