from flask import Flask, request, abort
import json
import os
import openai
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

load_dotenv()

app = Flask(__name__)

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
openai.api_key = os.getenv("OPENAI_API_KEY")

with open("question_bank.json", "r", encoding="utf-8") as f:
    question_bank = json.load(f)

def find_question(text):
    if "題號" in text and "我選" in text:
        try:
            q_part = text.split("題號")[1].split("，我選")
            q_number = int(q_part[0].strip())
            choice = q_part[1].strip().upper()
            return q_number, choice
        except:
            return None, None
    return None, None

def generate_explanation(question, student_answer):
    correct = question["正解"]
    prompt = f"""
你是一位國考輔導老師，請針對下列題目進行解析：
題目：{question['題目']}
選項：{'、'.join(question['選項'])}
學生作答：{student_answer}
正確答案：{correct}
請指出學生是否正確，並簡要解釋為什麼正解正確，以及錯解的迷思點。
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一位專業的國考解析導師。"},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"發生錯誤：{str(e)}"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text
    q_number, student_choice = find_question(user_input)
    if q_number is not None and student_choice:
        question = next((q for q in question_bank if q['題號'] == q_number), None)
        if question:
            explanation = generate_explanation(question, student_choice)
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=explanation)
            )
        else:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="找不到該題號，請確認輸入格式。")
            )
    else:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="請輸入格式：題號1，我選A")
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
