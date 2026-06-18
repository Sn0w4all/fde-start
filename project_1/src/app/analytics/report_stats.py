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
            
            prompt_path = Path(__file__).parent / "analytics_prompt.md"
            prompt_file = str(prompt_path)

            try:
                with open(prompt_file, "r", encoding="utf-8") as f:
                    prompt = f.read()
                    params = {
                        "position": position,
                        "normalized_data": normalized_data,
                        "data": json.dumps(data, ensure_ascii=False, indent=2)                     
                    }
                    prompt = prompt.format_map(params)
            except Exception as e:
                logger.error("Ошибка при загрузке промпта из %s",prompt_path)
                return None


            comment = client.messages.create(
                model="claude-haiku-4-5",
                max_tokens=1200,
                messages=[
                    {
                        "role": "user", 
                        "content": prompt
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