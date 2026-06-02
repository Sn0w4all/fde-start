import os
from anthropic import Anthropic
from dotenv import load_dotenv
load_dotenv("claude_api.env")

client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
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

for i in range(0,12,1):
    print('Твой ввод №', str(i),':')
    user_input = input()
    answer = chat(input)
    if answer != "":
        print('Ответ LLM:', answer)         
    else:
        print('Токены закончились')
        break

print('Сессия закончилась')