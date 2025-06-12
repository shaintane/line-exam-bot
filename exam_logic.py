from linebot.models import TextSendMessage
import requests
import json
import difflib

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
    base = f"第 {index+1} 題：{q['題目']}
" + "\n".join(q['選項'])
    return base + (f"\n\n{image_url}" if image_url else "")

def handle_exam_logic(user_input, user_id, event, line_bot_api, client, user_sessions, registration_buffer):
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

    if user_id not in user_sessions:
        subject = match_subject_name(user_input, ALIAS, SUBJECTS)
        if subject:
            repo = SUBJECTS[subject]
            question_bank = load_question_bank(repo)
            if not question_bank:
                line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 題庫載入失敗"))
                return
            import random
            questions = random.sample(question_bank, min(NUM_QUESTIONS, len(question_bank)))
            for idx, q in enumerate(questions):
                q["題號"] = idx + 1
            user_sessions[user_id] = {
                "repo": repo,
                "subject": subject,
                "questions": questions,
                "current": 0,
                "answers": [],
                "解析次數": 0
            }
            q = questions[0]
            message = format_question(q, 0, repo)
            line_bot_api.push_message(user_id, TextSendMessage(text=f"""✅ 已選擇『{subject}』科目，開始測驗：
{message}"""))
            return

    if user_id in user_sessions:
        session = user_sessions[user_id]
        user_input_normalized = normalize_answer(user_input)
        if session["current"] < NUM_QUESTIONS:
            current_idx = session["current"]
            current_q = session["questions"][current_idx]
            if user_input_normalized not in ['A', 'B', 'C', 'D']:
                line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 請填入 A / B / C / D 作為答案。"))
                return
            correct = normalize_answer(current_q["正解"])
            is_correct = (user_input_normalized == correct)
            session["answers"].append({
                "題號": current_q["題號"],
                "作答": user_input_normalized,
                "正解": correct,
                "是否正確": is_correct,
                "圖片連結": current_q.get("圖片連結")
            })
            session["current"] += 1
            if session["current"] < NUM_QUESTIONS:
                next_q = session["questions"][session["current"]]
                reply = format_question(next_q, session["current"], session["repo"])
                line_bot_api.push_message(user_id, TextSendMessage(text=reply))
            else:
                answers = session["answers"]
                wrong = [a for a in answers if not a["是否正確"]]
                total = len(answers)
                correct_count = total - len(wrong)
                rate = round((correct_count / total) * 100, 1)
                summary = f"📩 測驗已完成
共 {total} 題，正確 {correct_count} 題，正確率 {rate}%

錯題如下：
"
                if wrong:
                    summary += "
".join([f"題號 {w['題號']}（你選 {w['作答']}） 正解 {w['正解']}" for w in wrong])
                else:
                    summary += "全部答對！"
                summary += "

💡 想查看解析請輸入：題號3"
                line_bot_api.push_message(user_id, TextSendMessage(text=summary))
            return

        if user_input.startswith("題號"):
            try:
                tid = int(user_input.replace("題號", "").strip())
                if session["解析次數"] >= 3:
                    line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 你已達到本次測驗解析上限（3題）。"))
                    return
                q = next((q for q in session["questions"] if q["題號"] == tid), None)
                a = next((a for a in session["answers"] if a["題號"] == tid), None)
                if q and a:
                    explanation = generate_explanation(q, a["作答"])
                    if explanation:
                        session["解析次數"] += 1
                        repo = session["repo"]
                        image_url = f"https://raw.githubusercontent.com/shaintane/{repo}/main/{q['圖片連結']}" if q.get("圖片連結") else ""
                        reply = f"📘 題號 {tid} 解析：
{explanation}" + (f"

🔗 圖片：{image_url}" if image_url else "")
                        line_bot_api.push_message(user_id, TextSendMessage(text=reply))
                    else:
                        line_bot_api.push_message(user_id, TextSendMessage(text=f"⚠️ 題號 {tid}：目前無法提供解析，請稍後再試。"))
                else:
                    line_bot_api.push_message(user_id, TextSendMessage(text=f"⚠️ 查無題號 {tid} 的紀錄。"))
            except:
                line_bot_api.push_message(user_id, TextSendMessage(text="⚠️ 請輸入正確格式：題號3"))
            return
            import random
            questions = random.sample(question_bank, min(NUM_QUESTIONS, len(question_bank)))
            user_sessions[user_id] = {
                "repo": repo,
                "subject": subject,
                "questions": questions,
                "current": 0,
                "answers": []
            }
            q = questions[0]
            message = format_question(q, 0, repo)
            line_bot_api.push_message(user_id, TextSendMessage(text=message))
            return

    if user_id in user_sessions:
        session = user_sessions[user_id]
        idx = session["current"]
        if idx < len(session["questions"]):
            session["answers"].append(user_input)
            session["current"] += 1
            if session["current"] < len(session["questions"]):
                next_q = session["questions"][session["current"]]
                msg = format_question(next_q, session["current"], session["repo"])
                line_bot_api.push_message(user_id, TextSendMessage(text=msg))
            else:
                reply = f"📊 測驗完成！共 {len(session['questions'])} 題。
"
                correct = 0
                wrong_indexes = []
                for i, q in enumerate(session["questions"]):
                    student_ans = normalize_answer(session["answers"][i])
                    correct_ans = normalize_answer(q["正解"])
                    if student_ans == correct_ans:
                        correct += 1
                    else:
                        wrong_indexes.append(i)
                reply += f"✅ 答對：{correct} 題
❌ 答錯：{len(session['questions']) - correct} 題"
                line_bot_api.push_message(user_id, TextSendMessage(text=reply))

                # 錯題解析
                for i in wrong_indexes:
                    q = session["questions"][i]
                    student_ans = normalize_answer(session["answers"][i])
                    explanation = generate_explanation(client, q, student_ans)
                    if explanation:
                        text = f"第{i+1}題解析：
{explanation}"
                    else:
                        text = f"第{i+1}題解析無法生成"
                    line_bot_api.push_message(user_id, TextSendMessage(text=text))

                del user_sessions[user_id]
            return
            import random
            questions = random.sample(question_bank, min(NUM_QUESTIONS, len(question_bank)))
            user_sessions[user_id] = {
                "repo": repo,
                "subject": subject,
                "questions": questions,
                "current": 0,
                "answers": []
            }
            q = questions[0]
            message = format_question(q, 0, repo)
            line_bot_api.push_message(user_id, TextSendMessage(text=message))
            return

    if user_id in user_sessions:
        session = user_sessions[user_id]
        idx = session["current"]
        if idx < len(session["questions"]):
            session["answers"].append(user_input)
            session["current"] += 1
            if session["current"] < len(session["questions"]):
                next_q = session["questions"][session["current"]]
                msg = format_question(next_q, session["current"], session["repo"])
                line_bot_api.push_message(user_id, TextSendMessage(text=msg))
            else:
                reply = f"📊 測驗完成！共 {len(session['questions'])} 題。\n"
                correct = 0
                for i, q in enumerate(session["questions"]):
                    student_ans = normalize_answer(session["answers"][i])
                    correct_ans = normalize_answer(q["正解"])
                    if student_ans == correct_ans:
                        correct += 1
                reply += f"✅ 答對：{correct} 題\n❌ 答錯：{len(session['questions']) - correct} 題"
                line_bot_api.push_message(user_id, TextSendMessage(text=reply))
                del user_sessions[user_id]
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
