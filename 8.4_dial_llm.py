import anthropic
import httpx
import requests
import os
from bs4 import BeautifulSoup
from pydantic import BaseModel
import argparse
from pathlib import Path

from dotenv import load_dotenv
SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / "claude_api.env")
#выдаем JSON двумя способами. промптом и тулом

http_client = httpx.Client()
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
    http_client=http_client
)

class ArticleSummary(BaseModel):
    name: str
    born: str
    fame: str
    prize: int
    death: str

def get_article_summary(text: str):
    if not text: return None
    
    try:
        response = client.messages.parse(
            model="claude-sonnet-4-6",
            max_tokens=200,
            tools=[{"type": "web_search_20260209", "name": "web_search"}],
            messages=[
                {"role": "user", "content": f"Search key facts about:\n\n{text}"}
            ],
            output_format=ArticleSummary
        )
        # The API returns the JSON directly in the text content
        return response.parsed_output

    except anthropic.BadRequestError as e:
        print(f"API Error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Ищет в интернете и делает структурное саммари через Claude"
    )
    parser.add_argument(
        "person",
        nargs="+",                       # одна или больше ссылок (минимум одна обязательна)
        help="одна или несколько персон которые тебе интересны",
    )
    args = parser.parse_args()

    print("Scraping and analyzing articles...")
    for i, person in enumerate(args.person):
        print(f"\n--- Processing person {i+1} ---")   # ← тут был баг: не хватало f
        summary = get_article_summary(person)
        if summary:
            print(f"Scientist: {summary.name}")
            print(f"Born:      {summary.born}")
            print(f"Fame:      {summary.fame}")
            print(f"Nobel:     {summary.prize}")
            print(f"Died:      {summary.death}")
        else:
            print("Failed to generate summary.")

    print("\nDone.")

if __name__ == "__main__":
    main()