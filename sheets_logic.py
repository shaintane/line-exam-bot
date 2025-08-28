import os
import json
from datetime import datetime
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

def get_credentials_from_env():
    creds_info = json.loads(os.environ["GOOGLE_CREDENTIALS"])
    return Credentials.from_service_account_info(creds_info)

def get_latest_valid_row(sheet_id, sheet_name="Form Responses 1"):
    creds = get_credentials_from_env()
    service = build("sheets", "v4", credentials=creds)
    sheet = service.spreadsheets()

    result = sheet.values().get(spreadsheetId=sheet_id, range=sheet_name).execute()
    values = result.get("values", [])

    if not values or len(values) < 2:
        return None  # 無資料

    headers = values[0]
    latest_row = values[-1]

    data = dict(zip(headers, latest_row))

    start_date = data.get("實習起始日期")
    end_date = data.get("實習結束日期")
    line_id = data.get("第 12 題")  # 假設這是 LINE ID 欄位名稱

    try:
        today = datetime.today().date()
        start = datetime.strptime(start_date, "%Y/%m/%d").date()
        end = datetime.strptime(end_date, "%Y/%m/%d").date()
        if start <= today <= end:
            return {"line_id": line_id, "start_date": str(start), "end_date": str(end)}
    except Exception as e:
        print(f"[Sheets] 日期轉換錯誤: {e}")

    return None
