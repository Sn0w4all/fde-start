import anthropic
from typing import Optional
import os
from pydantic import BaseModel
import argparse
from pathlib import Path
import json 
import requests
from dotenv import load_dotenv

SCRIPT_DIR = Path(__file__).resolve().parent
load_dotenv(SCRIPT_DIR / "claude_api.env")
client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),
)


def fetch_weather(city: str) -> dict:
    # Сначала геокодируем город в координаты
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "en"}
    ).json()
    loc = geo["results"][0]
    lat, lon = loc["latitude"], loc["longitude"]

    # Затем получаем погоду
    weather = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat, "longitude": lon,
            "current": "temperature_2m,wind_speed_10m,precipitation"
        }
    ).json()["current"]

    return {
        "temperature": f"{weather['temperature_2m']}°C",
        "wind": int(weather["wind_speed_10m"]),
        "rainy": "yes" if weather["precipitation"] > 0 else "no"
    }



class WeatherToday(BaseModel):
    city: str
    temperature: str
    wind: Optional[int] = None   
    rainy: Optional[str] = None  


# Клод сопоставляет тут по name, description и даже properties - если чтото похожее claud пойдет в поля схемы и если там про погоду найдет что можно использовать этот тул.
tools = [
    {
        "name": "get_weather_in_my_city",
        "description": "Get weather information for a specific city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name to get weather for"}
            },
            "required": ["city"],
        },
    },
        {
        "name": "get_roadtraffic_in_my_city",
        "description": "Get road traffic information for a specific city.",
        "input_schema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name to get road traffic for"}
            },
            "required": ["city"],
        },
    }
]


def get_weather_today(text: str):
    if not text: return None
    
    try:
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=200,
            tools=tools,
            messages=[
                {
                    "role": "user", 
                    "content": f"Search weather today in City :\n\n{text}"
                }
            ],
        )
        tool_use = next((block for block in response.content if block.type == "tool_use"), None)
        #print(tool_use)
        if tool_use is None:
        # Claude решил не вызывать инструмент — это нормальный случай, не ошибка
            text_block = next((b for b in response.content if b.type == "text"), None)
            print("Claude не вызвал инструмент. Ответ:", text_block.text if text_block else "(пусто)")
            return None
        # Случай 2: вызвал — но НУЖНО проверить, какой именно
        if tool_use.name == "get_weather_in_my_city":
            result = fetch_weather(tool_use.input["city"])
        elif tool_use.name == "get_roadtraffic_in_my_city":
            # пока не реализовано — честно говорим об этом, а не делаем вид
            print(f"Инструмент {tool_use.name} пока не поддерживается")
            return None
        else:
            # Claude вызвал что-то, чего мы не знаем — не угадываем
            print(f"Неизвестный инструмент: {tool_use.name}")
            return None

        #result = {"event_id": "evt_123", "status": "created"} #заглушка может выглядеть так. 
     

        # The API returns the JSON directly in the text content

        weather = client.messages.parse(
            model="claude-haiku-4-5",
            max_tokens=200,
            tools=tools,
            tool_choice={"type": "auto", "disable_parallel_tool_use": True},
            messages=[
                {"role": "user", "content": f"Search weather today in City :\n\n{text}"},
                {"role": "assistant", "content": response.content},
                {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": json.dumps(result),
                    }
                ]
                }
            ],
            output_format=WeatherToday
        )

        print(f"stop_reason: {weather.stop_reason}")
        final_text = next(block for block in weather.content if block.type == "text")
        print(final_text.text)

        return weather.parsed_output
        
        

    except anthropic.BadRequestError as e:
        print(f"API Error: {e}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Показывает погоду на сегодня в том городе, который ты укажешь"
    )
    parser.add_argument(
        "city",
        nargs="+",                       # один или больше городов (минимум один обязательный)
        help="город, погода в котором тебе интересна",
    )
    args = parser.parse_args()

    print("Scraping and analyzing weather data...")
    for i, city in enumerate(args.city):
        print(f"\n--- Processing city {i+1} ---")  
        summary = get_weather_today(city)
        if summary:

            print(f"City:      {summary.city}")
            print(f"Temperature:      {summary.temperature}")
            print(f"Wind:     {summary.wind}")
            print(f"Is rainy:      {summary.rainy}")
        else:
            print("Failed to generate.")

    print("\nDone.")

if __name__ == "__main__":
    main()