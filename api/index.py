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

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    if "ผ้าไหม" in user_text or "ลายผ้า" in user_text:
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt="ลายผ้าไหมพื้นเมืองโทนคราม รูปทรงเรขาคณิตสมมาตร มีลายละเอียดแบบทอมือจากสกลนคร",
                size="1024x1024",
                quality="standard",
                n=1
            )
            image_url = response.data[0].url
            line_bot_api.reply_message(
                event.reply_token,
                ImageSendMessage(
                    original_content_url=image_url,
                    preview_image_url=image_url
                )
            )
        except Exception as e:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"ขออภัย ไม่สามารถสร้างภาพได้: {e}")
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"คุณพิมพ์ว่า: {user_text}")
        )

if __name__ == "__main__":
    app.run()
