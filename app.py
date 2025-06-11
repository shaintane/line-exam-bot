import os
import json
import random
import difflib
import requests
from flask import Flask, request, abort
from datetime import datetime
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

user_sessions = {}
NUM_QUESTIONS = 5  # 修改為 5 題

SUBJECTS = {
    "臨床血清免疫學": "examimmun",
    "臨床血液與血庫學": "exmablood",
    "臨床生物化學": "exambiochemicy",
    "醫學分子檢驗與鏡檢學": "exammolecu",
    "臨床生理與病理學": "exampatho",
    "臨床微生物學": "exammicrobiog"
}

def normalize_answer(ans):
    return ans.strip().replace('.', '').replace('．', '').upper().replace('Ｂ', 'B').replace('Ａ', 'A').replace('Ｃ', 'C').replace('Ｄ', 'D')

def match_subject_name(input_name):
    best_match = difflib.get_close_matches(input_name, SUBJECTS.keys(), n=1, cutoff=0.4)
    return best_match[0] if best_match else None

def load_question_bank(repo):
    api_url = f"https://api.github.com/repos/shaintane/{repo}/contents"
    res = requests.get(api_url)
    if res.status_code == 200:
        files = res.json()
        for file in files:
            if file["name"].startswith("question_bank_") and file["name"].endswith(".json"):
                raw_url = file["download_url"]
                return requests.get(raw_url).json()
    return []

def format_question(q, index, repo):
    image_url = f"https://raw.githubusercontent.com/shaintane/{repo}/main/{q['圖片連結']}" if q.get("圖片連結") else ""
    base = f"第 {index+1} 題：{q['題目']}\n" + "\n".join(q['選項'])
    return base + (f"\n\n{image_url}" if image_url else "")

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
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "你是一位專業的國考解析導師。"},
                {"role": "user", "content": prompt}
            ],
            timeout=10
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return None

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text.strip()

    matched_subject = match_subject_name(user_input)
    if matched_subject:
        repo = SUBJECTS[matched_subject]
        questions = load_question_bank(repo)
        selected = random.sample(questions, NUM_QUESTIONS)
        for idx, q in enumerate(selected):
            q["題號"] = idx + 1
        user_sessions[user_id] = {
            "subject": matched_subject,
            "repo": repo,
            "questions": selected,
            "current": 0,
            "answers": [],
            "解析次數": 0
        }
        first_q = selected[0]
        reply = format_question(first_q, 0, repo)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ 已選擇『{matched_subject}』科目，開始測驗：\n" + reply))
        return

    if user_id in user_sessions:
        session = user_sessions[user_id]
        current = session["current"]
        repo = session["repo"]
        if current < NUM_QUESTIONS:
            current_q = session["questions"][current]
            selected = normalize_answer(user_input)
            correct = current_q["正解"]
            is_correct = (selected == correct)
            session["answers"].append({
                "題號": current_q["題號"],
                "作答": selected,
                "正解": correct,
                "是否正確": is_correct,
                "圖片連結": current_q.get("圖片連結")
            })
            session["current"] += 1
            if session["current"] < NUM_QUESTIONS:
                next_q = session["questions"][session["current"]]
                reply = format_question(next_q, session["current"], repo)
            else:
                answers = session["answers"]
                wrong_answers = [ans for ans in answers if not ans.get("是否正確")]
                total = len(answers)
                correct_count = total - len(wrong_answers)
                rate = round((correct_count / total) * 100, 1)
                wrong_list = "\n".join([f"題號 {w['題號']}（你選 {w['作答']}） 正解 {w['正解']}" for w in wrong_answers])
                summary = f"📩 測驗已完成\n共 {total} 題，正確 {correct_count} 題，正確率 {rate}%\n\n錯題如下：\n{wrong_list if wrong_answers else '全部答對！'}\n\n💡 想查看解析請輸入：題號3"
                reply = summary
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
            return

        if user_input.startswith("題號"):
            try:
                tid = int(user_input.replace("題號", "").strip())
                if session["解析次數"] >= 3:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 你已達到本次測驗解析上限（3題）。"))
                    return
                q = next((q for q in session["questions"] if q["題號"] == tid), None)
                a = next((a for a in session["answers"] if a["題號"] == tid), None)
                if q and a:
                    explain = generate_explanation(q, a["作答"])
                    if explain:
                        session["解析次數"] += 1
                        image_url = f"https://raw.githubusercontent.com/shaintane/{repo}/main/{q['圖片連結']}" if q.get("圖片連結") else ""
                        reply = f"📘 題號 {tid} 解析：\n{explain}" + (f"\n\n🔗 圖片：{image_url}" if image_url else "")
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
                    else:
                        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"⚠️ 題號 {tid}：目前無法提供解析，請稍後再試。"))
                else:
                    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"⚠️ 查無題號 {tid} 的紀錄。"))
            except:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 請輸入正確格式：題號3"))
            return

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
