from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
)
import os
import openai

# Init API Keys
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# OpenAI Client
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Flask App
app = Flask(__name__)

@app.route('/')
def home():
    return 'LINE Bot is running!'

@app.route("/webhook", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

from linebot.models import TextSendMessage, ImageSendMessage

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()
    print(f"[DEBUG] User said: {user_text}")
    
    # สร้างคำอธิบายจาก ChatGPT
    chatgpt.add_msg(f"Human: โปรดอธิบายลวดลายผ้าไหมในหัวข้อ '{user_text}' อย่างสร้างสรรค์\n")
    explanation = chatgpt.get_response().replace("AI:", "", 1).strip()
    chatgpt.add_msg(f"AI: {explanation}\n")

    # สร้างภาพจาก DALL·E (OpenAI Image API)
    response = openai.Image.create(
        prompt=user_text,
        n=1,
        size="1024x1024"
    )
    image_url = response['data'][0]['url']

    # ส่งทั้งภาพ + ข้อความกลับไปยัง LINE
    line_bot_api.reply_message(
        event.reply_token,
        [
            TextSendMessage(text=explanation),
            ImageSendMessage(
                original_content_url=image_url,
                preview_image_url=image_url
            )
        ]
    )


if __name__ == "__main__":
    app.run()
