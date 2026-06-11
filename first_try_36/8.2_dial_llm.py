import anthropic
import httpx
import requests
import json
import os
from bs4 import BeautifulSoup
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
    
summary_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "description": "The name of the Scientist"},
        "born": {"type": "string", "description": "When and where the scientist was born"},
        "fame": {"type": "string", "description": "A summary of what their main claim to fame is"},
        "prize": {"type": "integer", "description": "The year they won the Nobel Prize. 0 if none."},
        "death": {"type": "string", "description": "When and where they died. 'Still alive' if living."}
    },
    "required": ["name", "born", "fame", "prize", "death"],
    "additionalProperties": False
}

def get_article_summary(text: str):
    if not text: return None
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            temperature=0.2,
            messages=[
                {"role": "user", "content": f"Summarize this article:\n\n{text}"}
            ],
            output_config={
                "format": {
                    "type": "json_schema",
                    "schema": summary_schema
                }
            }
        )


        


        # The API returns the JSON directly in the text content
        return json.loads(response.content[0].text)

    except anthropic.BadRequestError as e:
        print(f"API Error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


urls = [
    "https://en.wikipedia.org/wiki/Albert_Einstein",
    "https://en.wikipedia.org/wiki/Richard_Feynman",
    "https://en.wikipedia.org/wiki/James_Clerk_Maxwell",
    "https://en.wikipedia.org/wiki/Alan_Guth"
]

print("Scraping and analyzing articles...")

for i, url in enumerate(urls):
    print("\n--- Processing Article {i+1} ---")
    content = get_article_content(url)
    
    if content:
        summary = get_article_summary(content)
        if summary:
            print(f"Scientist: {summary.get('name')}")
            print(f"Born:      {summary.get('born')}")
            print(f"Fame:      {summary.get('fame')}")
            print(f"Nobel:     {summary.get('prize')}")
            print(f"Died:      {summary.get('death')}")
        else:
            print("Failed to generate summary.")
    else:
        print("Skipping (No content)")

print("\nDone.")