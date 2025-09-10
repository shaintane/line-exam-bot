# init_pipeline.py

import json
from datetime import datetime
from plans_loader import load_plan
from student_sheet_logic import init_student_sheet
from drive_logic import create_student_drive_folder
from whitelist import get_user_plan_list
from sheets_logic import get_student_identity_from_basic_sheet


def init_plan_for_student(user_id, plan_id="Plan_A", base_date: datetime = None):
    # 1. 載入 Plan 設定
    plan = load_plan(plan_id)
    if not plan:
        print(f"[init_plan_for_student] 無法載入 Plan: {plan_id}")
        return False

    # 2. 擷取學生身份資料（含姓名/學號/年度/梯次）
    student_raw = get_student_identity_from_basic_sheet(user_id)
    if not student_raw:
        print(f"[init_plan_for_student] 找不到學生基本資料: {user_id}")
        return False

    # ✅ 欄位轉換，對應 Drive / Sheet 使用的 key
    student = {
        "name": student_raw.get("姓名"),
        "student_id": student_raw.get("學號"),
        "grade": student_raw.get("年度", "2025"),
        "batch": student_raw.get("梯次", "秋期")
    }

    print(f"[init_plan_for_student] 取得學生身份資料：{student}")

    # 3. 建立 Google Drive 子資料夾
    folder_id = create_student_drive_folder(student, plan["tasks"])
    print(f"[init_plan_for_student] 已建立學生資料夾：{folder_id}")

    # 4. 建立 Google Sheet 分頁並初始化任務
    if base_date is None:
        base_date = datetime.now()
    init_student_sheet(user_id, student, plan, base_date)
    print(f"[init_plan_for_student] 已建立任務分頁")

    return True


def init_plan_list_for_student(user_id):
    plan_list = get_user_plan_list(user_id)
    if not plan_list:
        print(f"[init_plan_list_for_student] 尚未指定 plan_list，略過")
        return False

    for plan_id in plan_list:
        print(f"[init_plan_list_for_student] 執行 Plan: {plan_id}")
        init_plan_for_student(user_id, plan_id)

    return True
