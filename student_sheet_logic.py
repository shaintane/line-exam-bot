from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import gspread

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
sheets_service = build("sheets", "v4", credentials=creds)
gc = gspread.authorize(creds)

def create_student_sheet_with_tasks(user_id: str, student: dict, plan: dict, offset_base: int = 0):
    sheet_id = plan.get("google_sheet_id")
    student_name = student.get("name", "unknown")
    student_start = student.get("start_date")
    identity_code = student.get("student_id", user_id[-6:])
    grade = student.get("grade", "2025")
    batch = student.get("batch", "秋期")
    sheet_title = f"{grade}_{batch}_{student_name}_{identity_code}"

    sh = gc.open_by_key(sheet_id)
    try:
        sh.add_worksheet(title=sheet_title, rows="100", cols="20")
    except Exception as e:
        print(f"[Sheet] 無法建立分頁 {sheet_title}：{e}")
        return

    worksheet = sh.worksheet(sheet_title)
    headers = ["任務名稱", "開始日", "到期日"] + list(plan["tasks"][0]["sheet_columns"].keys())
    worksheet.append_row(headers)

    for task in plan.get("tasks", []):
        title = task.get("title", "")
        start_offset = task.get("start_offset_days", 0) + offset_base
        due_offset = task.get("due_offset_days", 0) + offset_base
        start_date = (datetime.strptime(student_start, "%Y-%m-%d") + timedelta(days=start_offset)).strftime("%Y-%m-%d")
        due_date = (datetime.strptime(student_start, "%Y-%m-%d") + timedelta(days=due_offset)).strftime("%Y-%m-%d")
        default_values = list(task.get("sheet_columns", {}).values())
        row = [title, start_date, due_date] + default_values
        worksheet.append_row(row)

    print(f"[Sheet] 建立完成：{sheet_title}，共 {len(plan['tasks'])} 筆任務")
