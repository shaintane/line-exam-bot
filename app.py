import os
import json
import random
import difflib
import requests
import re
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
NUM_QUESTIONS = 10

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

def remove_duplicate_questions(questions):
    seen = set()
    unique = []
    for q in questions:
        key = q["題目"].strip()
        if key not in seen:
            seen.add(key)
            unique.append(q)
    return unique

def filter_similar_questions(questions, threshold=0.9):
    filtered = []
    for q in questions:
        is_similar = False
        for fq in filtered:
            ratio = difflib.SequenceMatcher(None, q["題目"], fq["題目"]).ratio()
            if ratio > threshold:
                is_similar = True
                break
        if not is_similar:
            filtered.append(q)
    return filtered

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
    except Exception as e:
        return None

# 其他 handle_message 與 webhook 保留原樣...

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text.strip()

    # ...（略）...

    if user_id not in user_sessions or user_sessions[user_id].get("current", NUM_QUESTIONS) >= NUM_QUESTIONS:
        matched_subject = match_subject_name(user_input)
        if matched_subject:
            repo = SUBJECTS[matched_subject]
            questions = load_question_bank(repo)
            questions = remove_duplicate_questions(questions)
            questions = filter_similar_questions(questions, threshold=0.9)
            if len(questions) < NUM_QUESTIONS:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 題庫中可用題目數量不足，請更換科目或更新題庫。"))
                return
            selected = random.sample(questions, NUM_QUESTIONS)
            for idx, q in enumerate(selected):
                q["題號"] = idx + 1
            user_sessions[user_id] = {
                "subject": matched_subject,
                "repo": repo,
                "questions": selected,
                "current": 0,
                "answers": [],
                "錯題": [],
                "統計已回應": False
            }
            first_q = selected[0]
            reply = format_question(first_q, 0, repo)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ 已選擇『{matched_subject}』科目，開始測驗：\n" + reply))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="請輸入欲練習科目，例如：血清免疫"))
        return

    # ...（其餘保持原樣）...

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)




