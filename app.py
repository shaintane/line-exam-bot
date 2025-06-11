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

WHITELIST_FILE = "whitelist.json"

def load_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        return {}
    with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_whitelist(data):
    with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def is_user_active(user):
    today = datetime.now().date()
    start = datetime.strptime(user["start_date"], "%Y-%m-%d").date()
    end = datetime.strptime(user["end_date"], "%Y-%m-%d").date()
    return start <= today <= end

def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

app = Flask(__name__)
line_bot_api = LineBotApi(os.getenv("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

user_sessions = {}
registration_buffer = {}
DEV_USER_ID = "shaintane"

NUM_QUESTIONS = 5

SUBJECTS = {
    "臨床血清免疫學": "examimmun",
    "臨床血液與血庫學": "exmablood",
    "臨床生物化學": "exambiochemicy",
    "醫學分子檢驗與鏡檢學": "exammolecu",
    "臨床生理與病理學": "exampatho",
    "臨床微生物學": "exammicrbiog"
}

ALIAS = {
    "微生物": "臨床微生物學",
    "微生": "臨床微生物學",
    "血庫": "臨床血液與血庫學",
    "血液": "臨床血液與血庫學",
    "分子": "醫學分子檢驗與鏡檢學",
    "免疫": "臨床血清免疫學",
    "生化": "臨床生物化學",
    "病理": "臨床生理與病理學"
}

def normalize_answer(ans):
    return ans.strip().replace('.', '').replace('．', '').upper().replace('Ｂ', 'B').replace('Ａ', 'A').replace('Ｃ', 'C').replace('Ｄ', 'D')

def match_subject_name(input_name):
    if input_name in ALIAS:
        input_name = ALIAS[input_name]
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
    whitelist = load_whitelist()

    if user_id == DEV_USER_ID:
    pass
    elif user_id not in whitelist:
        if user_id not in registration_buffer:
        registration_buffer[user_id] = []
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            text="🎓 歡迎使用國考 AI 助教系統！請依序輸入以下 5 項資料（每行一項）：\n1. 學校\n2. 姓名\n3. 學號\n4. 實習起始日 (YYYY-MM-DD)\n5. 實習結束日 (YYYY-MM-DD)\n\n✅ 系統會自動記錄您的 LINE ID，無需輸入！"))
        return

    # 🧠 處理一次性貼上五行的情況
    lines = user_input.strip().split('\n')
    if len(lines) == 5:
        school, name, student_id, start_date, end_date = lines

        if not all([school, name, student_id, start_date, end_date]):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text="⚠️ 輸入資料不完整，請重新輸入 5 項完整資訊。"))
            return

        if not is_valid_date(start_date) or not is_valid_date(end_date):
            line_bot_api.reply_message(event.reply_token, TextSendMessage(
                text="⚠️ 日期格式錯誤，請使用 YYYY-MM-DD。\n請重新開始輸入資料。"))
            return

        registration_buffer[user_id] = [school, name, student_id, start_date, end_date]
    else:
        registration_buffer[user_id].append(user_input)

    # ✅ 若已收滿 5 項就寫入白名單
    if len(registration_buffer[user_id]) == 5:
        school, name, student_id, start_date, end_date = registration_buffer[user_id]
        whitelist[user_id] = {
            "school": school,
            "name": name,
            "student_id": student_id,
            "line_id": user_id,
            "start_date": start_date,
            "end_date": end_date,
            "role": "intern"
        }
        save_whitelist(whitelist)
        del registration_buffer[user_id]
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 註冊完成，請輸入科目名稱開始測驗。"))
        return
    else:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(
            text=f"✅ 已收到第 {len(registration_buffer[user_id])} 項，請輸入第 {len(registration_buffer[user_id]) + 1} 項："))
        return


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
            if selected not in ['A', 'B', 'C', 'D']:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 請填入 A / B / C / D 作為答案。"))
                return
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
