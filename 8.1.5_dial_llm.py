import anthropic
import httpx
import requests
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
    




def get_article_summary(text: str):
    if not text: return None
    
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=200,
            messages=[
                {"role": "user", "content": f"Суммаризируй эту статью.\n\n{text}. Результаты представь четко(проверь что именно такой формат, не выделяй *-ами и не делай лишние переводы строки и прочее) в структурированном виде Scientist: \nBorn: \nFame: \nNobel: \nDied:   "}
            ]
        )
        # The API returns the JSON directly in the text content
        return response.content[0].text

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
            print(f"{summary}")
        else:
            print("Failed to generate summary.")
    else:
        print("Skipping (No content)")

print("\nDone.")