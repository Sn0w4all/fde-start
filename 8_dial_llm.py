import os
import pandas as pd
from anthropic import Anthropic
from dotenv import load_dotenv
load_dotenv("claude_api.env")

client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
)

portfolio = pd.read_csv(
    "portfolio.csv",
    sep=';',
#    decimal=',',
    encoding='utf-8-sig'
)

messages = []

def chat(text):
    messages.append({"role": "user", "content":text})
    
    message = client.messages.create(
        max_tokens=1024,
        messages= messages,
        model="claude-haiku-4-5"
    )
    answer = message.content[0].text
    if message.stop_reason == 'end_turn':
        messages.append({"role": "assistant", "content":answer})
        return answer   
    else:
        return ''

for i in range(1,12,1):
    user_input = 'Прокомментируй мне эту транзакцию' + portfolio.loc[i].to_string()
    #user_input = input()
    answer = chat(user_input)
    if answer != "":
        print('Ответ LLM:',str(i), answer)         
    else:
        print('Токены закончились')
        break

print('Сессия закончилась')