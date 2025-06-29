from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
import requests
import os
import logging
import base64
from io import BytesIO

# Setup
app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))

# Logging
logging.basicConfig(level=logging.INFO)

# Store the state of conversation
user_state = {}

# Hugging Face & ImgBB Config
HF_TOKEN = os.getenv("HF_API_KEY", "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")
HF_MODEL = "TanapongW/silk_spai"
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY", "b9f20d2368e71aa2e21e2fde732a4cf2")  # ต้องตั้งค่าใน Vercel

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

# ฟังก์ชัน: ส่ง prompt ไป Hugging Face แล้วอัปโหลดไป ImgBB
def generate_image_from_huggingface(prompt):
    url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
    headers = {
        "Authorization": f"Bearer {HF_TOKEN}"
    }
    payload = {
        "inputs": prompt
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    image_bytes = response.content

    # อัปโหลดไป imgbb
    imgbb_url = "https://api.imgbb.com/1/upload"
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    imgbb_payload = {
        "key": IMGBB_API_KEY,
        "image": b64_image,
        "name": "silk_pattern"
    }

    imgbb_response = requests.post(imgbb_url, data=imgbb_payload)
    imgbb_response.raise_for_status()
    result = imgbb_response.json()
    return result['data']['url']

@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_text = event.message.text.strip()

    if user_text.lower() == "สวัสดี" or "hello" in user_text.lower():
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="สวัสดีครับ! ผมคือนักออกแบบลายผ้าไหม\nอยากให้ผมสร้างลายผ้าไหมให้คุณ?\nพิมพ์ 'สร้างลายผ้าไหม' ได้เลย")
        )
        user_state[user_id] = "awaiting_interaction"

    elif "สร้างลายผ้าไหม" in user_text:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="กรุณาบอกคำอธิบายของลายผ้าไหมที่คุณต้องการ")
        )
        user_state[user_id] = "awaiting_description"

    elif user_id in user_state and user_state[user_id] == "awaiting_description":
        try:
            prompt = user_text
            image_url = generate_image_from_huggingface(prompt)

            line_bot_api.reply_message(
                event.reply_token,
                [
                    ImageSendMessage(original_content_url=image_url, preview_image_url=image_url),
                    TextSendMessage(text="นี่คือลายที่คุณขอมา")
                ]
            )
            user_state.pop(user_id, None)
        except Exception as e:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"ขออภัย เกิดข้อผิดพลาดในการสร้างภาพ: {e}")
            )
            user_state.pop(user_id, None)

    else:
        try:
            # ถ้าคุณยังใช้ GPT สำหรับตอบคำถามทั่วไป
            gpt_response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": user_text}
                    ]
                }
            )
            gpt_response.raise_for_status()
            bot_reply = gpt_response.json()['choices'][0]['message']['content'].strip()

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=bot_reply)
            )
        except Exception as e:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"ขออภัย เกิดข้อผิดพลาดในการตอบคำถาม: {e}")
            )
