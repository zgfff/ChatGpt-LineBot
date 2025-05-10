from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from openai import OpenAI
import os
import logging

# Setup
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Logging
logging.basicConfig(level=logging.INFO)

# Store the state of conversation
user_state = {}

@app.route("/")
def home():
    return "LINE Bot is running."

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
    user_id = event.source.user_id
    user_text = event.message.text.strip()

    # กรณีที่ผู้ใช้ต้องการคุย
    if user_text.lower() == "สวัสดี" or "hello" in user_text.lower():
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="สวัสดีครับ! ผมคือนักออกแบบลายผ้าไหม\nถ้าต้องการให้ผมสร้างลายผ้าไหมให้คุณ?\nพิมพ์ 'สร้างลายผ้าไหม' ได้เลย")
        )
        user_state[user_id] = "awaiting_interaction"  # กำหนดสถานะเป็นการสนทนา

    # ถ้าผู้ใช้ต้องการให้สร้างภาพ
    elif "สร้างภาพ" in user_text:
        # ถามคำอธิบายสำหรับการสร้างภาพ
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="กรุณาบอกคำอธิบายของภาพที่คุณต้องการ")
        )
        user_state[user_id] = "awaiting_description"  # รอคำอธิบาย

    # หากผู้ใช้กำลังอยู่ในสถานะรอคำอธิบายเพื่อสร้างภาพ
    elif user_id in user_state and user_state[user_id] == "awaiting_description":
        try:
            # ใช้ข้อความของผู้ใช้เป็น prompt สำหรับสร้างภาพ
            prompt = user_text
            img_response = client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="hd",
                n=1
            )
            # ส่งภาพกลับไปให้ผู้ใช้
            line_bot_api.reply_message(
                event.reply_token,
                [
                    ImageSendMessage(original_content_url=image_url, preview_image_url=image_url),
                    TextSendMessage(text="นี่คือภาพที่คุณขอมา")
                ]
            )
            user_state.pop(user_id, None)  # รีเซ็ตสถานะหลังการสร้างภาพเสร็จ

        except Exception as e:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"ขออภัย เกิดข้อผิดพลาดในการสร้างภาพ: {e}")
            )
            user_state.pop(user_id, None)
# ใช้ GPT เพื่อตอบคำถามทั่วไป
    else:
        try:
            chat_response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_text}
                ]
            )
            bot_reply = chat_response['choices'][0]['message']['content'].strip()
            
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=bot_reply)
            )
        except Exception as e:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"ขออภัย เกิดข้อผิดพลาดในการตอบคำถาม: {e}")
            )
