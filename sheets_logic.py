# sheets_logic.py

import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
gc = gspread.authorize(creds)

# ✅ 對應學生身份的欄位名稱（可根據你的表單調整）
BASIC_INFO_SHEET_ID = "1U2prbo2B1CXYVZPudk1ZS6U9yu_wbIyEFnQn-JnY4jI"
BASIC_INFO_SHEET_NAME = "表單回應 1"  # ← 改為你實際表單工作表名稱

def get_student_identity_from_basic_sheet(user_id: str) -> dict:
    try:
        worksheet = gc.open_by_key(BASIC_INFO_SHEET_ID).worksheet(BASIC_INFO_SHEET_NAME)
        rows = worksheet.get_all_records()
        for row in reversed(rows):
            if str(row.get("LINE ID", "")).strip() == user_id:
                return {
                    "姓名": row.get("姓名", "unknown"),
                    "學號": row.get("學號", user_id[-6:]),
                    "年度": row.get("年度", "2025"),
                    "梯次": row.get("梯次", "秋期")
                }
        return {}
    except Exception as e:
        print(f"[ERROR] 擷取學生身份失敗: {e}")
        return {}
