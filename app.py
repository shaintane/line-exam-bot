import os
import json
import random
import difflib
import requests
from flask import Flask, request, abort
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

SUBJECTS = {
    "血清免疫": "examimmun",
    "血液與血庫": "exmablood",
    "生物化學": "exambiochemicy",
    "分子檢驗與顯微": "exammolecu",
    "生理與病理": "exampatho",
    "微生物與微生物學": "exammicrobiog"
}

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
    image_url = f"https://raw.githubusercontent.com/shaintane/{repo}/main/{q['圖片連結']}.jpg" if q.get("圖片連結") else ""
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
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ AI 解析失敗：{str(e)}"

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
    user_id = event.source.user_id
    user_input = event.message.text.strip()

    if user_input.startswith("題號"):
        try:
            target_qnum = int(user_input.replace("題號", "").strip())
            session = user_sessions.get(user_id)
            if not session:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 尚未啟動測驗，請先選擇科目開始。"))
                return
            matched = next((q for q in session["answers"] if q["題號"] == target_qnum), None)
            full_question = next((q for q in session["questions"] if q["題號"] == target_qnum), None)
            if matched and full_question:
                explanation = generate_explanation(full_question, matched["作答"])
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=explanation))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 查無此題號，請確認題號是否正確。"))
            return
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 請輸入格式：題號3"))
            return

    if user_id not in user_sessions or user_sessions[user_id].get("current", 20) >= 20:
        matched_subject = match_subject_name(user_input)
        if matched_subject:
            repo = SUBJECTS[matched_subject]
            questions = load_question_bank(repo)
            selected = random.sample(questions, 20)
            user_sessions[user_id] = {
                "subject": matched_subject,
                "repo": repo,
                "questions": selected,
                "current": 0,
                "answers": [],
                "錯題": []
            }
            first_q = selected[0]
            reply = format_question(first_q, 0, repo)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ 已選擇『{matched_subject}』科目，開始測驗：\n" + reply))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入欲練習科目，例如：血清免疫"))
        return

    session = user_sessions[user_id]
    current_index = session["current"]
    repo = session["repo"]

    if current_index >= 20:
        wrong_answers = session["錯題"]
        total = len(session["answers"])
        wrong_count = len(wrong_answers)
        wrong_list = "\n".join([f"題號 {w['題號']}（你選 {w['作答']}）正解 {w['正解']}" for w in wrong_answers])
        summary = f"📝 測驗已完成\n共 {total} 題，錯誤 {wrong_count} 題\n\n錯題如下：\n{wrong_list if wrong_count > 0 else '全部答對！'}\n\n💡 想查看解析請輸入：題號3"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=summary))
        return

    user_answer = user_input.strip().upper()
    if user_answer not in ["A", "B", "C", "D"]:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入 A/B/C/D 作答"))
        return

    question = session["questions"][current_index]
    correct = question["正解"]
    is_correct = (user_answer == correct)
    session["answers"].append({
        "題號": question["題號"],
        "作答": user_answer,
        "正解": correct,
        "是否正確": is_correct
    })
    if not is_correct:
        session["錯題"].append({
            "題號": question["題號"],
            "作答": user_answer,
            "正解": correct
        })
    session["current"] += 1

    if session["current"] < 20:
        next_q = session["questions"][session["current"]]
        reply = format_question(next_q, session["current"], repo)
    else:
        reply = "🎉 測驗結束，請稍後查看統計結果與解析。"

    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

