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

    # Check if the user is in the process of a conversation
    if user_id in user_state:
        if user_state[user_id] == "awaiting_description":
            # If user was asked for a description, process the reply and generate image
            try:
                prompt = user_text  # Use the user's message as the prompt for image generation
                img_response = client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="hd",
                    n=1
                )
                image_url = img_response.data[0].url

                # Send the generated image back to the user
                line_bot_api.reply_message(
                    event.reply_token,
                    [
                        ImageSendMessage(original_content_url=image_url, preview_image_url=image_url),
                        TextSendMessage(text="นี่คือภาพที่คุณขอมา")
                    ]
                )
                # Reset state after processing the message
                user_state.pop(user_id, None)
            except Exception as e:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=f"ขออภัย เกิดข้อผิดพลาดในการสร้างภาพ: {e}")
                )
                user_state.pop(user_id, None)
        else:
            # If the bot is not in an expected state, reset the state
            user_state.pop(user_id, None)

    else:
        # If it's the first message or a new conversation, ask what image to generate
        user_state[user_id] = "awaiting_description"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="สวัสดีครับ! คุณต้องการให้ผมสร้างภาพอะไรให้คุณ? กรุณาบอกคำอธิบายสั้นๆ เกี่ยวกับภาพที่คุณต้องการ")
        )
