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
    user_id = event.source.user_id
    reply_token = event.reply_token

    try:
        # 1. แปลงข้อความไทย → Prompt ภาษาอังกฤษ
        prompt = chatgpt.get_response(
            f"แปลงข้อความนี้เป็น prompt ภาษาอังกฤษสำหรับสร้างภาพผ้าไหมแบบไทย: {user_text}"
        ).replace("AI:", "").strip()

        # 2. สร้างภาพจาก prompt ด้วย OpenAI
        from openai import OpenAI
        import os

        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        image_url = response.data[0].url

        # 3. อธิบายภาพที่สร้างจาก prompt
        description = chatgpt.get_response(
            f"ช่วยอธิบายภาพที่สร้างจาก prompt นี้เป็นภาษาไทย: {prompt}"
        ).replace("AI:", "").strip()

        # 4. ตอบกลับผู้ใช้บน LINE
        messages = [
            TextSendMessage(text=f"🌸 คุณต้องการ: {user_text}"),
            TextSendMessage(text=f"🧵 Prompt ที่ใช้สร้างภาพ:\n{prompt}"),
            TextSendMessage(text=f"🎨 คำอธิบายภาพ:\n{description}"),
            TextSendMessage(text=f"🖼️ ภาพลายผ้าไหม:\n{image_url}")
        ]
        line_bot_api.reply_message(reply_token, messages)

    except Exception as e:
        print(f"[ERROR] {e}")
        line_bot_api.reply_message(
            reply_token,
            TextSendMessage(text="ขออภัย เกิดข้อผิดพลาดในการสร้างภาพผ้าไหม กรุณาลองใหม่อีกครั้งภายหลัง")
        )



if __name__ == "__main__":
    app.run()
