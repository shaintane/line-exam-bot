from linebot.models import TextSendMessage
import requests
import json
import difflib
import random
import os
import logging

from access_control import check_user_access

LOGGER = logging.getLogger(__name__)

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

def handle_exam_logic(user_input, user_id, event, line_bot_api, client, user_sessions, registration_buffer):
    access = check_user_access(user_id)
    if not access.allowed:
        line_bot_api.push_message(user_id, TextSendMessage(text=access.message))
        return

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

    if user_id not in user_sessions or user_sessions[user_id].get("completed"):
        subject = match_subject_name(user_input, ALIAS, SUBJECTS)
        if subject:
            repo = SUBJECTS[subject]
            question_bank = load_question_bank(repo)
            if not question_bank:
                line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 題庫載入失敗"))
                return
            questions = random.sample(question_bank, min(NUM_QUESTIONS, len(question_bank)))
            for idx, q in enumerate(questions):
                q["題號"] = idx + 1
            user_sessions[user_id] = {
                "repo": repo,
                "subject": subject,
                "questions": questions,
                "current": 0,
                "answers": [],
                "解析次數": 0,
                "completed": False
            }
            q = questions[0]
            message = format_question(q, 0, repo)
            line_bot_api.push_message(user_id, TextSendMessage(text=f"✅ 已選擇『{subject}』科目，開始測驗：\n{message}"))
            return

    if user_id in user_sessions:
        session = user_sessions[user_id]
        user_input_normalized = normalize_answer(user_input)

        if user_input.startswith("題號"):
            try:
                tid = int(user_input.replace("題號", "").strip())
                if session["解析次數"] >= 3:
                    line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 你已達到本次測驗解析上限（3題）。"))
                    return
                q = next((q for q in session["questions"] if q["題號"] == tid), None)
                a = next((a for a in session["answers"] if a["題號"] == tid), None)
                if q and a:
                    explanation = generate_explanation(client, q, a["作答"])
                    if explanation:
                        session["解析次數"] += 1
                        image_url = f"https://raw.githubusercontent.com/shaintane/{session['repo']}/main/{q['圖片連結']}" if q.get("圖片連結") else ""
                        text = f"📘 題號 {tid} 解析：\n{explanation}" + (f"\n\n🔗 圖片：{image_url}" if image_url else "")
                        line_bot_api.push_message(user_id, TextSendMessage(text=text))
                    else:
                        line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 無法生成解析，請稍後再試"))
                else:
                    line_bot_api.push_message(user_id, TextSendMessage(text=f"⚠️ 查無題號 {tid} 的紀錄。"))
            except:
                line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 請輸入正確格式：題號3"))
            return

        if session["current"] < NUM_QUESTIONS:
            current_q = session["questions"][session["current"]]
            if user_input_normalized not in ['A', 'B', 'C', 'D']:
                line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 請填入 A / B / C / D 作為答案。"))
                return
            correct = normalize_answer(current_q["正解"])
            session["answers"].append({
                "題號": current_q["題號"],
                "作答": user_input_normalized,
                "正解": correct,
                "是否正確": user_input_normalized == correct
            })
            session["current"] += 1
            if session["current"] < NUM_QUESTIONS:
                next_q = session["questions"][session["current"]]
                message = format_question(next_q, session["current"], session["repo"])
                line_bot_api.push_message(user_id, TextSendMessage(text=message))
            else:
                answers = session["answers"]
                wrong = [a for a in answers if not a["是否正確"]]
                correct_count = NUM_QUESTIONS - len(wrong)
                rate = round((correct_count / NUM_QUESTIONS) * 100, 1)
                summary = f"📩 測驗已完成\n共 {NUM_QUESTIONS} 題，正確 {correct_count} 題，正確率 {rate}%\n\n"
                summary += "錯題如下：\n" if wrong else "全部答對！"
                summary += "\n".join([f"題號 {w['題號']}（你選 {w['作答']}） 正解 {w['正解']}" for w in wrong])
                summary += "\n\n💡 想查看解析請輸入：題號3"
                summary += "\n\n📘 想選擇其他科目請輸入『微生物』或『免疫』等關鍵字。"
                line_bot_api.push_message(user_id, TextSendMessage(text=summary))
                session["completed"] = True
            return

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
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            messages=[
                {"role": "system", "content": "你是一位專業的國考解析導師。"},
                {"role": "user", "content": prompt}
            ],
            timeout=10
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        LOGGER.exception("Failed to generate explanation: %s", exc)
        return None
