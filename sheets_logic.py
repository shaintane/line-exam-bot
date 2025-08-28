import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json
import os

# ====== Google Sheets 設定 ======
GOOGLE_SHEET_NAME = "附件7.1實習學生基本資料表（回應）"  # <-- 請確認表單名稱正確
WHITELIST_FILE = "whitelist.json"

# ====== 欄位名稱設定（請與表單表頭一致） ======
COLUMN_LINE_ID = "LINE ID"
COLUMN_NAME = "姓名"
COLUMN_SCHOOL = "學校名稱"
COLUMN_START_DATE = "實習起始日期"
COLUMN_END_DATE = "實習結束日期"

def update_whitelist_from_sheet():
    # 驗證連線
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("teachingsystemapi-998c7b2ffc1c.json", scope)
    client = gspread.authorize(creds)

    sheet = client.open(GOOGLE_SHEET_NAME).sheet1
    records = sheet.get_all_records()

    today = datetime.today().date()

    # 載入現有白名單
    if os.path.exists(WHITELIST_FILE):
        with open(WHITELIST_FILE, "r", encoding="utf-8") as f:
            whitelist = json.load(f)
    else:
        whitelist = {}

    new_entries = 0

    for row in records:
        try:
            line_id = str(row[COLUMN_LINE_ID]).strip()
            name = row[COLUMN_NAME]
            school = row[COLUMN_SCHOOL]
            start_date = datetime.strptime(str(row[COLUMN_START_DATE]), "%Y-%m-%d").date()
            end_date = datetime.strptime(str(row[COLUMN_END_DATE]), "%Y-%m-%d").date()
        except Exception as e:
            print(f"[❌ 略過無效資料] {e}")
            continue

        # 判斷是否符合期間
        if start_date <= today <= end_date:
            if line_id not in whitelist:
                whitelist[line_id] = {
                    "name": name,
                    "school": school,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                }
                new_entries += 1

    # 寫回 json
    with open(WHITELIST_FILE, "w", encoding="utf-8") as f:
        json.dump(whitelist, f, ensure_ascii=False, indent=2)

    print(f"[✅ 白名單更新完成] 新增 {new_entries} 筆，總計 {len(whitelist)} 筆。")
