from linebot.models import TextSendMessage
from datetime import datetime
import difflib
import requests
import json
import os

def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def normalize_answer(ans):
    return ans.strip().replace('.', '').replace('．', '').upper().replace('Ｂ', 'B').replace('Ａ', 'A').replace('Ｃ', 'C').replace('Ｄ', 'D')

def match_subject_name(input_name, alias, subjects):
    if input_name in alias:
        input_name = alias[input_name]
    best_match = difflib.get_close_matches(input_name, subjects.keys(), n=1, cutoff=0.4)
    return best_match[0] if best_match else None

def load_question_bank(repo):
    try:
        api_url = f"https://api.github.com/repos/shaintane/{repo}/contents"
        res = requests.get(api_url, timeout=5)
        if res.status_code == 200:
            files = res.json()
            for file in files:
                if file["name"].startswith("question_bank_") and file["name"].endswith(".json"):
                    raw_url = file["download_url"]
                    return requests.get(raw_url, timeout=5).json()
    except:
        return []
    return []

def format_question(q, index, repo):
    image_url = f"https://raw.githubusercontent.com/shaintane/{repo}/main/{q['圖片連結']}" if q.get("圖片連結") else ""
    base = f"第 {index+1} 題：{q['題目']}\n" + "\n".join(q['選項'])
    return base + (f"\n\n{image_url}" if image_url else "")

def generate_explanation(client, question, student_answer):
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
    except:
        return None

def process_message(event, line_bot_api, client, user_sessions, registration_buffer):
    user_id = event.source.user_id
    user_input = event.message.text.strip()
    DEV_USER_ID = "shaintane"
    WHITELIST_FILE = "whitelist.json"
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
    NUM_QUESTIONS = 5

    def load_whitelist():
        if not os.path.exists(WHITELIST_FILE):
            return {}
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_whitelist(data):
        with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    whitelist = load_whitelist()

    if user_input.lower().startswith("admin") and user_id not in whitelist:
        whitelist[user_id] = {
            "role": "admin",
            "name": "管理者",
            "student_id": "admin",
            "school": "System",
            "start_date": "2025-01-01",
            "end_date": "2099-12-31",
            "line_id": user_id
        }
        save_whitelist(whitelist)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="✅ 管理者登入成功。"))
        return

    if user_input.startswith("input") and whitelist.get(user_id, {}).get("role") == "admin":
        try:
            _, school, name, student_id, start_date, end_date = user_input.split()
            whitelist[student_id] = {
                "school": school,
                "name": name,
                "student_id": student_id,
                "start_date": start_date,
                "end_date": end_date,
                "line_id": student_id,
                "role": "intern"
            }
            save_whitelist(whitelist)
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"✅ 已手動新增 {name} 進入白名單。"))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 輸入格式錯誤，請使用 input 學校 姓名 學號 起始日 結束日"))
        return

    if user_input.startswith("delet") and whitelist.get(user_id, {}).get("role") == "admin":
        try:
            _, student_id = user_input.split()
            if student_id in whitelist:
                del whitelist[student_id]
                save_whitelist(whitelist)
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"🗑️ 已移除 {student_id}。"))
            else:
                line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"⚠️ 查無 {student_id} 於白名單內。"))
        except:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="⚠️ 請輸入格式：delet 學號"))
        return

    from core_logic import process_message as inner_logic
    inner_logic(event, line_bot_api, client, user_sessions, registration_buffer)
