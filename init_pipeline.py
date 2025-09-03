# init_pipeline.py

from plans_loader import load_plan_data
from whitelist import get_student_data, save_student_data
from student_sheet_logic import init_student_sheet
from drive_logic import create_student_drive_folders
from sheets_logic import get_student_identity_from_basic_sheet
from datetime import datetime, timedelta

# ✅ 初始化指定模組給該學生

def init_plan_for_student(user_id: str, plan_id: str, offset_base: int = 0):
    print(f"[INIT] 開始為 {user_id} 初始化 {plan_id}（偏移量 {offset_base} 天）")

    student = get_student_data(user_id)
    if not student:
        print(f"[INIT] 找不到白名單學生：{user_id}")
        return

    plan = load_plan_data(plan_id)
    if not plan:
        print(f"[INIT] 找不到計畫內容：{plan_id}")
        return

    anchor_date = datetime.strptime(student["start_date"], "%Y-%m-%d")
    base_date = anchor_date + timedelta(days=offset_base)

    # ✅ 取得學生身份（學號、姓名、年度、梯次）
    identity = get_student_identity_from_basic_sheet(user_id)
    if identity:
        student["name"] = identity.get("姓名", student.get("name", "同學"))
        student["student_id"] = identity.get("學號", user_id[-6:])
        student["grade"] = identity.get("年度", "2025")
        student["batch"] = identity.get("梯次", "秋期")

        save_student_data(user_id, student)  # 更新 whitelist.json 中的資料
    else:
        print(f"[INIT] 無法從基本資料表取得 {user_id} 的身份資訊")

    # ✅ 建立 Sheet 任務與 Drive 資料夾
    init_student_sheet(user_id, student, plan, base_date)
    create_student_drive_folders(user_id, student, plan, base_date)

    print(f"[INIT] {plan_id} 初始化完成 for {user_id}。")
