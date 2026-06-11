import os
from anthropic import Anthropic
from dotenv import load_dotenv
load_dotenv("claude_api.env")

client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
)

message = client.messages.create(
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Hello, Claude",
        }
    ],
    model="claude-haiku-4-5"
)
print(message.content[0].text)