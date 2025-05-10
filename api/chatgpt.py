import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")

class ChatGPT:
    def __init__(self):
        self.messages = []

    def add_msg(self, msg):
        self.messages.append({"role": "user", "content": msg})

    def get_response(self):
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=self.messages
        )
        return response.choices[0].message.content.strip()
