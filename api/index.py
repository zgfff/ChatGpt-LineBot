from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageSendMessage
from api.chatgpt import ChatGPT
from api.imagegen import generate_image
import os

app = Flask(__name__)

# LINE config
line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
chatgpt = ChatGPT()

@app.route('/')
def home():
    return 'Hello, World!'

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

    try:
        # สร้าง prompt จากข้อความผู้ใช้
        chatgpt.add_msg(f"Human: สร้างคำอธิบายสำหรับภาพลายผ้าไหมแบบสกลนคร โดยใช้คำว่า '{user_text}' พร้อมรายละเอียดเชิงเรขาคณิต สีคราม ไล่ระดับความละเอียด\n")
        prompt = chatgpt.get_response().replace("AI:", "", 1)

        # สร้างภาพ
        image_url = generate_image(prompt)

        # ส่งภาพกลับผู้ใช้
        line_bot_api.reply_message(
            event.reply_token,
            ImageSendMessage(
                original_content_url=image_url,
                preview_image_url=image_url
            )
        )
    except Exception as e:
        print(f"[ERROR] {e}")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="ขออภัย ระบบไม่สามารถสร้างภาพได้ในขณะนี้ 🧵")
        )
