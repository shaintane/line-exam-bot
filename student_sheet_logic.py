# student_sheet_logic.py (lazy load 版, 統一認證方式)

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# ✅ 全域 client，僅在第一次呼叫時初始化
_gc = None

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_gc():
    """延遲初始化 gspread client"""
    global _gc
    if _gc is None:
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        _gc = gspread.authorize(creds)
        print("[Sheets] gspread client 已初始化")
    return _gc


# ✅ 學生任務專用的 Google Sheet ID
SPREADSHEET_ID = "1U2prbo2B1CXYVZPudk1ZS6U9yu_wbIyEFnQn-JnY4jI"


def init_student_sheet(user_id: str, student: dict, plan: dict, base_date: datetime):
    """
    在 Google Sheet 中建立學生的任務分頁，並初始化 Plan 任務列表
    """
    try:
        gc = get_gc()
        name = student.get("name", user_id[-4:])
        student_id = student.get("student_id", user_id[-6:])
        grade = student.get("grade", "2025")
        batch = student.get("batch", "秋期")

        sheet_title = f"{grade}_{batch}_{name}_{student_id}"
        print(f"[Sheet] 建立中：{sheet_title}")

        sheet = gc.open_by_key(SPREADSHEET_ID)
        try:
            worksheet = sheet.worksheet(sheet_title)
            print(f"[Sheet] 已存在分頁：{sheet_title}")
            return
        except:
            worksheet = sheet.add_worksheet(title=sheet_title, rows="100", cols="20")

        # ✅ 建立表頭
        headers = ["任務編號", "任務名稱", "開始日", "到期日"]
        for key in plan["tasks"][0].get("sheet_columns", {}).keys():
            headers.append(key)

        worksheet.append_row(headers)

        # ✅ 寫入任務資料
        for task in plan["tasks"]:
            start = base_date + timedelta(days=task.get("start_offset_days", 0))
            due = base_date + timedelta(days=task.get("due_offset_days", 0))

            row = [
                task.get("task_id"),
                task.get("title"),
                start.strftime("%Y-%m-%d"),
                due.strftime("%Y-%m-%d"),
            ]
            for val in task.get("sheet_columns", {}).values():
                row.append(val)

            worksheet.append_row(row)

        print(f"[Sheet] 建立完成：{sheet_title}，共 {len(plan['tasks'])} 筆任務")

    except Exception as e:
        print(f"[Sheet] 建立學生分頁時發生錯誤：{e}")
