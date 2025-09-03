# plan_executor.py

from init_pipeline import init_plan_for_student
from plans_loader import load_plan_data
from whitelist import get_student_data, mark_planlist_executed
from completion_checker import check_plan_completed

from linebot.models import FlexSendMessage
from linebot import LineBotApi
from google.oauth2.service_account import Credentials
import gspread

# Line Bot 初始化（你可以在外部初始化並傳入）
line_bot_api = LineBotApi("<YOUR_CHANNEL_ACCESS_TOKEN>")

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
gc = gspread.authorize(creds)


def check_and_run_plan_list(user_id: str):
    student = get_student_data(user_id)
    if not student:
        print(f"[plan_executor] 找不到學生資料：{user_id}")
        return

    if student.get("planlist_executed", False):
        print(f"[plan_executor] {user_id} 已執行過 plan_list，不重複執行")
        return

    if not check_plan_completed(user_id, "Plan_A"):
        print(f"[plan_executor] Plan_A 尚未完成，暫不執行 plan_list")
        show_plan_progress(user_id, "Plan_A")  # ✅ 顯示進度條
        return

    plan_list = student.get("plan_list", [])
    if not plan_list:
        print(f"[plan_executor] {user_id} 無 plan_list，不需執行其他模組")
        return

    print(f"[plan_executor] {user_id} Plan_A 完成，開始執行 plan_list: {plan_list}")
    plan_A = load_plan_data("Plan_A")
    base_offset = get_plan_duration(plan_A)

    for plan_id in plan_list:
        init_plan_for_student(user_id, plan_id, offset_base=base_offset)
        plan_data = load_plan_data(plan_id)
        base_offset += get_plan_duration(plan_data)

    mark_planlist_executed(user_id)
    print(f"[plan_executor] {user_id} 已完成所有模組初始化。")


def get_plan_duration(plan: dict) -> int:
    if not plan or "tasks" not in plan:
        return 0
    return max([task.get("due_offset_days", 0) for task in plan["tasks"]]) + 1


# ✅ 顯示 FlexMessage 任務進度條

def show_plan_progress(user_id: str, plan_id: str):
    student = get_student_data(user_id)
    plan = load_plan_data(plan_id)
    sheet_id = plan.get("google_sheet_id")
    student_name = student.get("name", "unknown")
    identity_code = student.get("student_id", user_id[-6:])
    grade = student.get("grade", "2025")
    batch = student.get("batch", "秋期")
    sheet_title = f"{grade}_{batch}_{student_name}_{identity_code}"

    try:
        worksheet = gc.open_by_key(sheet_id).worksheet(sheet_title)
        rows = worksheet.get_all_records()

        total = len([r for r in rows if r.get("任務名稱", "").strip()])
        done = len([r for r in rows if r.get("狀態", "").strip() == "完成"])
        percent = round(done / total * 100) if total else 0

        bubble = build_flex_progress_bar(plan_id, done, total, percent)
        line_bot_api.push_message(user_id, FlexSendMessage(alt_text="任務進度追蹤", contents=bubble))

    except Exception as e:
        print(f"[Flex進度] 發送失敗：{e}")


# ✅ 建立 Flex 卡片進度條內容

def build_flex_progress_bar(plan_id: str, done: int, total: int, percent: int) -> dict:
    bar_blocks = int(percent / 10)
    bar_str = "█" * bar_blocks + "░" * (10 - bar_blocks)

    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": f"📘 {plan_id} 任務進度", "weight": "bold", "size": "md", "margin": "none"},
                {"type": "text", "text": f"你已完成 {done}/{total} 項任務（{percent}%）", "size": "sm", "margin": "md"},
                {"type": "text", "text": f"[{bar_str}]", "size": "sm", "margin": "sm", "wrap": True},
                {"type": "text", "text": f"⏳ 尚有 {total - done} 項未完成，請盡快完成以開啟後續模組。", "size": "xs", "margin": "md", "wrap": True}
            ]
        },
        "styles": {
            "body": {"backgroundColor": "#f7f9fa"}
        }
    }
