import anthropic
from pathlib import Path
from dotenv import load_dotenv
import os
import json

SCRIPT_DIR = Path(__file__).resolve().parent.parent.parent.parent.parent
load_dotenv(SCRIPT_DIR / "claude_api.env")
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)

def get_analysis(data, position):
    try:
        comment = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=200,
            messages=[
                {
                    "role": "user", 
                    "content": f"Ты финансовый аналитик,  прокомментируй по активу {position} значения цены сегодня: {json.dumps(data, ensure_ascii=False, indent=2)}.  Что это может означать для трейдера?"
                }
            ],
        )
        result = {
            "Position": position,
            "Comment": comment.content[0].text
        }
        return result

    except anthropic.BadRequestError as e:
        print(f"API Error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None