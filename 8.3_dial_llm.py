import anthropic
import httpx
import requests
import os
from bs4 import BeautifulSoup
from pydantic import BaseModel

from dotenv import load_dotenv
load_dotenv("claude_api.env")
#выдаем JSON двумя способами. промптом и тулом

http_client = httpx.Client()
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
    http_client=http_client
)

def get_article_content(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        article = soup.find("div", class_="mw-body-content")
        if article:
            content = "\n".join(p.text for p in article.find_all("p"))
            return content[:1000] 
        else:
            return ""
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""
    
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
            messages=[
                {"role": "user", "content": f"Summarize this article:\n\n{text}"}
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


urls = [
    "https://en.wikipedia.org/wiki/Albert_Einstein",
    "https://en.wikipedia.org/wiki/Richard_Feynman",
]

print("Scraping and analyzing articles...")

for i, url in enumerate(urls):
    print("\n--- Processing Article {i+1} ---")
    content = get_article_content(url)
    
    if content:
        summary = get_article_summary(content)
        if summary:
            print(f"Scientist: {summary.name}")
            print(f"Born:      {summary.born}")
            print(f"Fame:      {summary.fame}")
            print(f"Nobel:     {summary.prize}")
            print(f"Died:      {summary.death}")
        else:
            print("Failed to generate summary.")
    else:
        print("Skipping (No content)")

print("\nDone.")