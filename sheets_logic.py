# sheets_logic.py

import gspread
from google.oauth2.service_account import Credentials

# ✅ 延遲初始化 Google Sheets client
_gc = None

def get_gc():
    """延遲初始化 gspread client"""
    global _gc
    if _gc is None:
        SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
        creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)
        _gc = gspread.authorize(creds)
        print("[Sheets] gspread client 已初始化")
    return _gc


# ✅ 學生基本資料表資訊
BASIC_INFO_SHEET_ID = "1U2prbo2B1CXYVZPudk1ZS6U9yu_wbIyEFnQn-JnY4jI"
BASIC_INFO_SHEET_NAME = "基本資料表"  # ← 請依實際表單的工作表名稱修改


def get_student_identity_from_basic_sheet(user_id: str) -> dict:
    """
    從 Google Sheets 擷取學生身份資訊
    依據 LINE ID 對應姓名 / 學號 / 年度 / 梯次
    """
    try:
        gc = get_gc()
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
