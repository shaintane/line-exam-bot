import os
import json
import random
import difflib
import requests
import re
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

# JSON profile setup
PROFILE_FILE = "user_profiles.json"
ADMIN_FILE = "admin_users.json"

def load_user_profiles():
    if os.path.exists(PROFILE_FILE):
        with open(PROFILE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_user_profiles(data):
    with open(PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_admin_users():
    if os.path.exists(ADMIN_FILE):
        with open(ADMIN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_admin_users(admin_list):
    with open(ADMIN_FILE, "w", encoding="utf-8") as f:
        json.dump(admin_list, f, ensure_ascii=False, indent=2)

user_profiles = load_user_profiles()
admin_users = load_admin_users()
user_sessions = {}
NUM_QUESTIONS = 10

SUBJECTS = {
    "臨床血清免疫學": "examimmun",
    "臨床血液與血庫學": "exmablood",
    "生物化學及臨床生化": "exambiochemicy",
    "醫學分子與鏡檢學": "exammolecu",
    "臨床生理與病理學": "exampatho",
    "微生物與臨床微生物學": "exammicrobiog"
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
    except Exception:
        return None

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    user_input = event.message.text.strip()

    # Admin 登記程序
    if user_input == "admin":
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=f"⚙️ 您的 LINE ID 是：{user_id}\n若要註冊為管理者請輸入：確認 admin")
        )
        return

    if user_input == "確認 admin":
        if user_id not in admin_users:
            admin_users.append(user_id)
            save_admin_users(admin_users)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 您已成功註冊為管理者，未來可直接使用所有功能。"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="您已是管理者，無需重複註冊。"))
        return

    # Step 1: 新使用者須註冊
    if user_id not in user_profiles:
        user_profiles[user_id] = { "狀態": "待填寫" }
        save_user_profiles(user_profiles)
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="👋 歡迎加入！請依照格式輸入您的資料：\n\n姓名/學校/學號\n（例如：王小明/OO醫學大學/M123456）")
        )
        return

    # Step 2: 收集註冊資料
    if user_profiles.get(user_id, {}).get("狀態") == "待填寫":
        parts = user_input.split("/")
        if len(parts) == 3:
            user_profiles[user_id] = {
                "姓名": parts[0].strip(),
                "學校": parts[1].strip(),
                "學號": parts[2].strip(),
                "加入日期": datetime.today().strftime("%Y-%m-%d"),
                "狀態": "已加入"
            }
            save_user_profiles(user_profiles)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 資料已登記，歡迎開始使用測驗功能！"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 請依正確格式輸入：姓名/學校/學號"))
        return

    # Step 3: 檢查是否為 admin 或白名單
    if user_id not in admin_users:
        profile = user_profiles.get(user_id)
        if not profile or profile.get("狀態") != "已加入":
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 您尚未註冊，請先輸入 姓名/學校/學號 才能使用測驗功能。"))
            return

    # Step 4: 刪除學號指令
    if user_input.startswith("刪除 "):
        sid = user_input.replace("刪除", "").strip()
        removed = False
        for uid, prof in list(user_profiles.items()):
            if prof.get("學號") == sid:
                del user_profiles[uid]
                save_user_profiles(user_profiles)
                removed = True
                break
        msg = f"✅ 已移除學號 {sid} 的測驗權限" if removed else "❌ 查無該學號"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=msg))
        return

    # 開始測驗流程
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)



